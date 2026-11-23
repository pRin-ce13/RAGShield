# Phase 7 Learning Report: Backend API & Persistence Hardening

---

## A. Phase Summary
- **Phase Number and Title:** Phase 7 — Backend API & Persistence Hardening
- **Date Completed:** 2026-11-23
- **Overall Objective:** Transform RAGShield from a CLI-driven security scanner into an enterprise-grade backend service with asynchronous relational persistence (SQLAlchemy 2.0 + SQLite/PostgreSQL), versioned schema migrations (Alembic), cryptographic authentication & RBAC (JWT & bcrypt), non-blocking background scan execution (`ScanService`), and structured REST API endpoints.
- **Short Summary of the Work:**
  In Phase 7, we engineered the production server foundation for RAGShield. We established an asynchronous relational database architecture in [backend/app/database/session.py](file:///c:/Users/WIN-10/Desktop/4TH_YEAR/RAGShield/backend/app/database/session.py) and defined core ORM models ([backend/app/models/](file:///c:/Users/WIN-10/Desktop/4TH_YEAR/RAGShield/backend/app/models/)) for `User`, `Target`, `ScanRun`, `TestResultRecord`, and `VulnerabilityFindingRecord`. We initialized Alembic with asynchronous migration support and generated the initial schema migration script. We designed Pydantic DTO schemas ([backend/app/schemas/](file:///c:/Users/WIN-10/Desktop/4TH_YEAR/RAGShield/backend/app/schemas/)) and built an asynchronous repository layer ([backend/app/repositories/](file:///c:/Users/WIN-10/Desktop/4TH_YEAR/RAGShield/backend/app/repositories/)) isolating data access. We implemented stateless JWT authentication and native bcrypt password hashing with Role-Based Access Control (`admin`, `analyst`, `viewer`). We created the asynchronous `ScanService` supporting non-blocking scan execution in background tasks. Finally, we engineered REST API routers for authentication, targets, scans, and findings with CORS middleware, lifespan database seeding, and structured JSON error handlers in [backend/app/main.py](file:///c:/Users/WIN-10/Desktop/4TH_YEAR/RAGShield/backend/app/main.py), and verified the entire API surface with automated integration tests.

---

## B. What Did We Achieve?
- **Implemented:**
  - Asynchronous database engine (`create_async_engine`) and session factory supporting zero-configuration SQLite (`aiosqlite`) for development and PostgreSQL (`asyncpg`) for production.
  - Relational ORM models with `lazy="selectin"` eager loading:
    - `User`: RBAC accounts with bcrypt password hashes.
    - `Target`: Remote RAG application configurations, target URLs, API keys, and field translation maps.
    - `ScanRun`: Assessment lifecycle records with status tracking (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`), progress counters, and risk scores.
    - `TestResultRecord`: Granular test execution results, latency, evaluator reasoning, and evidence snippets.
    - `VulnerabilityFindingRecord`: Deduplicated security findings with CVSS risk scores, evidence lists, and remediation playbooks.
  - Versioned database schema migrations with Alembic (`f807a98f64b6_initial_schema.py`).
  - Data Transfer Objects (DTOs) with Pydantic v2 and `email-validator`.
  - Repository layer: `BaseRepository`, `UserRepository`, `TargetRepository`, `ScanRepository`, and `FindingRepository`.
  - Security module: native `bcrypt` password hashing (with 72-byte truncation) and HMAC-SHA256 JWT bearer token issuance/verification (`pyjwt`).
  - Asynchronous `ScanService` with non-blocking background task dispatch (`asyncio.create_task`).
  - REST API surface under `/api/v1/`:
    - `/auth`: User registration, OAuth2 password grant login, and `/me` profile retrieval.
    - `/targets`: Target registration, listing, detail view, updates, deletions, and active `/check` connectivity testing.
    - `/scans`: Asynchronous `/launch` returning `202 Accepted`, scan status retrieval, and granular execution results.
    - `/findings`: Deduplicated vulnerability findings and aggregate security posture breakdown.
  - Global structured error handling envelope and CORS middleware in `backend/app/main.py`.
- **Tested & Verified:**
  - Verified database schema creation and async transaction commit/rollback.
  - Verified versioned Alembic migration creation and application.
  - Verified repository CRUD operations for all entities.
  - Verified password hashing, verification, JWT signing, claims verification, and rejection of tampered tokens.
  - Verified non-blocking background scan execution and pre-flight offline error logging.
  - Verified full REST API suite across auth, targets, scans, findings, and 404 error formatting via `httpx.ASGITransport`.
- **Partially Implemented:**
  - Distributed task queues (Redis/Celery) — deferred to Phase 11; `asyncio.create_task` provides lightweight, in-process async execution without external daemon dependencies.
- **Not Implemented:**
  - Frontend web UI (scheduled for Phase 8).

---

## C. Why Did We Build It?
A CLI scanner is effective for local testing, but modern engineering security programs require an **enterprise-ready API architecture**:
1. **Persistent Historical Records:** Security teams need historical tracking: When was a target last assessed? Did a code update fix an RBAC flaw or introduce a regression? Relational database persistence tracks scan runs and findings across time.
2. **Decoupled Client & Server:** A REST API decouples scanning logic from user interfaces. Web dashboards (React in Phase 8), CI/CD pipelines (GitHub Actions), and automation scripts can trigger scans, query findings, and pull remediation playbooks over standard HTTP.
3. **Non-Blocking User Experience:** Running a comprehensive 20-test security suite across remote LLM endpoints can take minutes. Blocking HTTP requests causes connection timeouts and freezes user interfaces. Launching scans as background tasks and returning `202 Accepted` keeps the API fast and responsive.
4. **Role-Based Access Control (RBAC):** Not all users should have equal permissions. System administrators configure integrations, security analysts trigger scans and triage vulnerabilities, and executive stakeholders view read-only posture dashboards.

---

## D. How Did We Build It?

### Architecture & Data Flow:

```mermaid
flowchart TD
    Client["Client / Frontend\n(React or CI/CD)"] -->|POST /auth/login| AuthRoute["Auth API\n(/api/v1/auth)"]
    AuthRoute -->|Issue Bearer Token| Client
    
    Client -->|POST /scans/launch\nBearer Token| ScanRoute["Scan API\n(/api/v1/scans)"]
    ScanRoute -->|Verify RBAC Role| SecurityDep["Security Dependency\n(require_role)"]
    
    SecurityDep --> ScanService["ScanService.launch_scan()"]
    ScanService -->|Create ScanRun (PENDING)| DB[(Relational DB\nSQLite / Postgres)]
    ScanService -->|Return 202 Accepted| Client
    
    ScanService -->|asyncio.create_task| BgWorker["Background Worker\n(_execute_scan_background)"]
    
    subgraph Background Execution
        BgWorker -->|1. Pre-Flight Check| Adapter["Target Adapter"]
        BgWorker -->|2. Run Test Probes| Orchestrator["ScanOrchestrator"]
        Orchestrator --> TargetRAG["Target RAG API"]
        TargetRAG --> Orchestrator
        Orchestrator -->|3. Evaluate Results| EvalPipeline["EvaluationPipeline"]
        EvalPipeline -->|4. Deduplicate & Score| FindingsMgr["FindingsManager"]
        FindingsMgr -->|5. Bulk Persist Results & Findings| DB
        FindingsMgr -->|6. Update ScanRun (COMPLETED)| DB
    end
    
    Client -->|GET /scans/{id}\nGET /findings/{id}| FindingsRoute["Findings API\n(/api/v1/findings)"]
    FindingsRoute --> DB
    FindingsRoute -->|Prioritized Defects + Remediation| Client
```

---

## E. Architecture Changes
- Created `backend/`:
  - `backend/alembic/` (Alembic environment, versioned migrations)
  - `backend/app/`
    - `core/config.py` (Pydantic settings)
    - `database/session.py` (AsyncEngine, AsyncSession, Base, get_db)
    - `models/` (`user.py`, `target.py`, `scan.py`, `result.py`, `finding.py`)
    - `schemas/` (`user.py`, `target.py`, `scan.py`, `finding.py`)
    - `repositories/` (`base.py`, `user_repo.py`, `target_repo.py`, `scan_repo.py`, `finding_repo.py`)
    - `security/` (`passwords.py`, `jwt.py`, `deps.py`)
    - `services/` (`scan_service.py`, `target_service.py`)
    - `api/v1/` (`auth.py`, `targets.py`, `scans.py`, `findings.py`)
    - `main.py` (FastAPI app, CORS, exception handlers, lifespan)
- Created `alembic.ini` configuration.

---

## F. Python Libraries and Technologies Used

### 1. `sqlalchemy` (v2.1.9)
- **Purpose:** Object Relational Mapper for persistent database entities.
- **Why selected:** SQLAlchemy 2.0 provides native `async/await` syntax with `AsyncSession` and `create_async_engine`.
- **Where used:** `backend/app/database/`, `backend/app/models/`, `backend/app/repositories/`.

### 2. `aiosqlite` (v0.22.1)
- **Purpose:** Non-blocking asynchronous SQLite driver.
- **Why selected:** Provides zero-config local development persistence without requiring a standalone database server.
- **Where used:** `backend/app/database/session.py`.

### 3. `alembic` (v1.20.1)
- **Purpose:** Version-controlled database schema migrations.
- **Why selected:** Standard migration framework for SQLAlchemy with automated schema comparison and rollback support.
- **Where used:** `backend/alembic/`.

### 4. `pydantic-settings` (v2.16.3)
- **Purpose:** Environment variable validation and settings management.
- **Why selected:** Validates database connection strings and JWT secrets with strict typing and `.env` loading.
- **Where used:** `backend/app/core/config.py`.

### 5. `bcrypt` (v5.0.0)
- **Purpose:** Salted, adaptive password hashing adhering to NIST SP 800-63B.
- **Why selected:** Direct integration prevents compatibility issues with legacy passlib wrappers.
- **Where used:** `backend/app/security/passwords.py`.

### 6. `pyjwt` (v2.15.1)
- **Purpose:** Stateless JSON Web Token generation and verification.
- **Why selected:** High-performance, zero-dependency RFC 7519 implementation.
- **Where used:** `backend/app/security/jwt.py`.

### 7. `email-validator` (v2.4.0) & `python-multipart` (v0.0.34)
- **Purpose:** RFC 5322 email syntax validation and OAuth2 password form parsing.
- **Where used:** `backend/app/schemas/user.py`, `backend/app/api/v1/auth.py`.

---

## G. Important Code Explanation

### 1. Asynchronous Background Scan Dispatch
In [backend/app/services/scan_service.py](file:///c:/Users/WIN-10/Desktop/4TH_YEAR/RAGShield/backend/app/services/scan_service.py#L42-L78):
```python
scan = await scan_repo.create_scan_run(
    target_id=target.id,
    triggered_by_id=triggered_by_id,
    total_tests=0,
    categories=request.categories,
    severities=request.severities
)
await self.session.commit()

# Non-blocking async dispatch with dedicated session
asyncio.create_task(
    self._execute_scan_background(
        scan_id=scan.id,
        target=target,
        request=request
    )
)
return scan
```
*How it works:* The endpoint commits an initial `PENDING` scan record, spawns `_execute_scan_background` as an asynchronous background task on the event loop, and immediately returns the scan ID to the caller with HTTP 202 Accepted. The background worker opens an isolated `AsyncSessionLocal()` session to prevent session contention.

### 2. Role-Based Access Control Dependency Factory
In [backend/app/security/deps.py](file:///c:/Users/WIN-10/Desktop/4TH_YEAR/RAGShield/backend/app/security/deps.py#L45-L56):
```python
def require_role(allowed_roles: List[str]) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {allowed_roles}. Current role: '{current_user.role}'."
            )
        return current_user
    return role_checker
```
*How it works:* Implements a dependency factory for FastAPI. By attaching `Depends(require_role(["admin", "analyst"]))` to a route, non-analysts or viewers attempting administrative actions (such as launching a scan or deleting targets) are halted with `403 Forbidden` before executing route logic.

---

## H. Testing and Verification

### Test 1: Database Persistence & Relationships
- **Command:** `.\.venv\Scripts\python.exe scratch/test_db_models.py`
- **Results:** Verified database creation, `User`, `Target`, `ScanRun`, `TestResultRecord`, and `VulnerabilityFindingRecord` persistence and foreign key navigation using `lazy="selectin"`.

### Test 2: Alembic Migrations
- **Command:** `.\.venv\Scripts\alembic.exe revision --autogenerate -m "initial_schema"` followed by `upgrade head`.
- **Results:** Successfully autogenerated `f807a98f64b6_initial_schema.py` and upgraded SQLite database schema.

### Test 3: Passwords, JWT & Security
- **Command:** `.\.venv\Scripts\python.exe scratch/test_auth_security.py`
- **Results:**
  - Password hashing and verification passed.
  - JWT creation, claims decoding, expiration, and signature validation passed.
  - Tampered tokens rejected cleanly.

### Test 4: Asynchronous Scan Service
- **Command:** `.\.venv\Scripts\python.exe scratch/test_scan_service.py`
- **Results:** Verified non-blocking dispatch; confirmed pre-flight check caught offline target, transitioned status to `FAILED`, and recorded HTTP 504 diagnostics in the database.

### Test 5: End-to-End REST API Suite
- **Command:** `.\.venv\Scripts\python.exe scratch/test_api_endpoints.py`
- **Results:**
  - `GET /` and `GET /health` returned `200 OK`.
  - Admin login returned valid JWT bearer token.
  - User registration verified with duplicate email detection (HTTP 400).
  - Target creation and listing verified.
  - Scan launched asynchronously returning `202 Accepted`.
  - Findings and posture endpoints returned JSON responses.
  - Non-existent resource returned structured 404 error envelope.

---

## I. Problems Faced and Solutions
- *Challenge 1: `MissingGreenlet` Exception in Async SQLAlchemy.*
  - *Symptom:* `sqlalchemy.exc.StatementError: greenlet_spawn has not been called; can't call await_() here.`
  - *Root Cause:* Accessing relationship attributes (e.g. `scan.target`) synchronously triggered lazy-loading IO, which is prohibited in async mode.
  - *Fix:* Configured `lazy="selectin"` on all relationship attributes across `ScanRun`, `Target`, `User`, `TestResultRecord`, and `VulnerabilityFindingRecord`.
- *Challenge 2: Passlib and Modern Bcrypt Incompatibility.*
  - *Symptom:* `AttributeError: module 'bcrypt' has no attribute '__about__'` and `ValueError: password cannot be longer than 72 bytes`.
  - *Root Cause:* Newer bcrypt versions (4.1.0+) deprecated internal attributes used by `passlib`.
  - *Fix:* Switched to native `bcrypt` library directly (`bcrypt.hashpw` and `bcrypt.checkpw`) with explicit 72-byte truncation conforming to the standard.
- *Challenge 3: OAuth2 Form Parsing Dependency.*
  - *Symptom:* `RuntimeError: Form data requires "python-multipart" to be installed.`
  - *Fix:* Installed `python-multipart>=0.0.9` and added it to `requirements.txt`.

---

## J. Interview Preparation

### The 30-Second Explanation
> *"In Phase 7, we built RAGShield's backend service and persistence architecture. We implemented an asynchronous relational database layer using SQLAlchemy 2.0 and Alembic, supporting SQLite for local testing and PostgreSQL for production. We engineered JWT-based authentication and role-based access control, an asynchronous ScanService that executes assessments in non-blocking background tasks returning 202 Accepted, and structured REST API endpoints for targets, scans, and prioritized vulnerability findings."*

### The 2-Minute Explanation
> *"Transitioning a security scanner from a CLI script to an enterprise product requires a resilient server architecture.*
> 
> *In Phase 7, I designed the backend infrastructure for RAGShield.*
> 
> *First, we established our data layer with SQLAlchemy 2.0 using `async/await` sessions. We defined models for Users, Targets, Scans, Results, and deduplicated Findings. To prevent the notorious `MissingGreenlet` error common in async SQLAlchemy, we configured `lazy='selectin'` eager loading on all relationships. We paired this with Alembic for version-controlled migrations.*
> 
> *Second, we implemented authentication using native bcrypt for salted password hashing and HMAC-SHA256 JWT bearer tokens for stateless authorization, with custom FastAPI dependency factories enforcing RBAC across Admin, Analyst, and Viewer roles.*
> 
> *Third, we solved the long-running scan problem. Remote RAG evaluations take dozens of seconds, which would trigger gateway timeouts if handled synchronously. We built `ScanService`, which creates a `PENDING` database record, dispatches the assessment suite to a background `asyncio.create_task` worker with an isolated database session, and immediately returns `202 Accepted` to the client.*
> 
> *Finally, we organized clean REST routers under `/api/v1/`, complete with structured JSON error envelopes and CORS middleware ready for our React frontend."*

### Likely Interview Questions & Model Answers

#### Q1: Why use `async/await` with SQLAlchemy in a security scanner backend?
**Answer:**
> *"Security scanning involves heavy I/O: waiting on HTTP responses from target LLM endpoints and querying the database for test suites and findings. Synchronous database drivers block the operating system thread during I/O. Using SQLAlchemy 2.0 with async drivers (`aiosqlite` / `asyncpg`) allows the FastAPI event loop to handle hundreds of concurrent requests, stream scan progress, and serve dashboard queries while scans run in the background."*

#### Q2: What causes the SQLAlchemy `MissingGreenlet` error and how do you resolve it?
**Answer:**
> *"The `MissingGreenlet` error occurs in async SQLAlchemy when code attempts to access a relationship attribute (like `scan.target`) that was not loaded into memory when the parent object was queried. In synchronous code, SQLAlchemy issues a lazy query transparently. In async mode, attribute access cannot implicitly `await` I/O. We resolve this by specifying `lazy='selectin'` on the relationship definition, ensuring related entities are eagerly fetched using an efficient `WHERE id IN (...)` query during the primary async fetch."*

#### Q3: Why return HTTP 202 Accepted when launching a security scan?
**Answer:**
> *"HTTP 202 Accepted signifies that the request has been accepted for processing, but processing has not completed. Security scans involve sending dozens of network probes to remote RAG systems, which can take 10 to 60+ seconds. Holding an HTTP connection open until the scan finishes risks reverse-proxy gateway timeouts (504 Gateway Timeout) and freezes the UI. Returning 202 with a scan ID allows the client to poll or stream status asynchronously."*

---

## K. What I Learned
1. How to architect asynchronous database persistence with SQLAlchemy 2.0 and Alembic.
2. How to avoid `MissingGreenlet` errors using `selectin` eager loading.
3. How to implement native bcrypt password hashing and JWT authentication in FastAPI.
4. How to decouple long-running operations using asynchronous background task execution.
5. How to build repository patterns that abstract database operations from API routing logic.

---

## L. Current Project Status
- **Completed:** Phase 0 (Setup), Phase 1 (Demo Target), Phase 2 (Target Adapter), Phase 3 (Attack Library), Phase 4 (Scan Orchestration), Phase 5 (Evaluation Engine), Phase 6 (Findings & Risk Assessment), Phase 7 (Backend API & Persistence Hardening).
- **Pending:** Phase 8 (Frontend Dashboard).
- **Known Issues:** None. All tests passing cleanly.
- **Technical Debt:** None.

---

## M. Next Phase Preview: Phase 8 — Frontend Dashboard
In **Phase 8**, we build the user-facing web interface for RAGShield:
1. **React + TypeScript + Vite Dashboard**: Clean, modern web UI communicating with our FastAPI backend.
2. **Authentication Screens**: Login and user registration.
3. **Target Management**: Register and configure RAG targets and run connectivity checks.
4. **Scan Console**: Launch scans with category/severity filters and view real-time progress.
5. **Vulnerability Explorer**: Interactive findings table with severity badges, CVSS risk scores, evidence inspection, and step-by-step remediation playbooks.

---

## N. GitHub Checklist
- [x] All Phase 7 backend code created in `backend/app/` and `backend/alembic/`.
- [x] `alembic.ini` and initial migration script created.
- [x] `requirements.txt` and `docs/TECH_STACK_AND_LIBRARIES.md` updated.
- [x] No secrets committed (synthetic credentials only).
- [x] Automated tests passing cleanly.
- [x] Commit recommendation: `feat(backend): implement REST API, persistence layer, JWT auth, and async scan service`
