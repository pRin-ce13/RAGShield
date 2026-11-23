# RAGShield: Development Log

A chronological record of architectural decisions, completed milestones, active work, and next steps.

---

## [Phase 0] Project Discovery and Setup
- **Date Started:** 2026-11-18
- **Status:** Completed

### Completed Milestones
1. **Operating Guide & Mandates:** Reviewed and adopted `docs/PROJECT_CONTEXT.md` as the master project instruction.
2. **Environment Inspection:**
   - Operating System: Windows
   - Python: 3.12.0
   - Git: 2.52.0.windows.1
   - Node.js, Docker, PostgreSQL identified as dependencies for later phases (Phases 7, 8, 11).
3. **Step 0.1:** Initialized Git repository and created comprehensive [.gitignore](file:///c:/Users/WIN-10/Desktop/4TH_YEAR/RAGShield/.gitignore) protecting against leaks of Python bytecode, virtual environments, vector stores, and `.env` secrets.
4. **Step 0.2:** Created and verified Python 3.12 virtual environment (`.venv`). Verified Git ignores `.venv`.
5. **Step 0.3:** Created root configuration template (`.env.example`), root `README.md`, and initial foundational documentation:
   - `docs/TECH_STACK_AND_LIBRARIES.md`
   - `docs/PROJECT_OVERVIEW.md`
   - `docs/ARCHITECTURE.md`
   - `docs/INTERVIEW_PREPARATION.md`

### Decisions & Trade-Offs
- **Decision:** Use Python's built-in `venv` module rather than external tools like `conda` or `poetry`.
  - *Reasoning:* Minimal overhead, zero external dependencies required for initial bootstrapping, native to Python standard library.
- **Decision:** Separate target RAG system (`demo-rag/`) from security testing engine (`engine/`).
  - *Reasoning:* Ensures RAGShield tests RAG systems as a black-box/gray-box client via HTTP adapters, rather than tightly coupling evaluation logic to the internal data structures of one specific RAG framework.

### Active Work
- Completed Phase 7 (Backend API & Persistence Hardening) and Phase 7 Learning Report.
- Preparing to start Phase 8 (Frontend Dashboard).

---

## [Phase 7] Backend API & Persistence Hardening
- **Date Completed:** 2026-11-23
- **Status:** Completed

### Completed Milestones
1. **Asynchronous Relational Persistence:** Implemented `backend/app/database/session.py` with SQLAlchemy 2.0 and `aiosqlite`.
2. **Core ORM Models:** Defined `User`, `Target`, `ScanRun`, `TestResultRecord`, and `VulnerabilityFindingRecord` with `lazy="selectin"` eager loading.
3. **Database Migrations:** Initialized Alembic with async environment and generated baseline migration `f807a98f64b6_initial_schema.py`.
4. **Pydantic DTOs & Repositories:** Created DTO schemas and encapsulated database access in `UserRepository`, `TargetRepository`, `ScanRepository`, and `FindingRepository`.
5. **Authentication & RBAC:** Implemented native `bcrypt` password hashing and stateless JWT bearer tokens (`pyjwt`) with `require_role()` dependency.
6. **Scan Service & Background Execution:** Built `ScanService` supporting non-blocking scan execution returning `202 Accepted` and updating database asynchronously.
7. **REST API Routers & App:** Configured `/auth`, `/targets`, `/scans`, and `/findings` routers with CORS, lifespan startup seeding, and structured JSON error handlers in `backend/app/main.py`.
8. **Phase 7 Report:** Compiled comprehensive learning report in `docs/phase-reports/PHASE_07_REPORT.md`.

### Decisions & Trade-Offs
- **Decision:** Use native `bcrypt` directly rather than passlib wrapper.
  - *Reasoning:* Eliminates bcrypt 4.1+ attribute deprecation bugs and adheres strictly to 72-byte password length limits.
- **Decision:** Asynchronous background execution via `asyncio.create_task` with isolated database sessions.
  - *Reasoning:* Prevents client gateway timeouts during multi-probe scans while keeping the system lightweight without requiring external Celery/Redis daemons in local dev.

---

## [Phase 6] Findings, Severity & Risk Assessment
- **Date Completed:** 2026-11-23
- **Status:** Completed

### Completed Milestones
1. **Defect & Evidence Models:** Defined `EvidenceInstance` and `VulnerabilityFinding` schemas in `engine/scoring/models.py`.
2. **Quantitative Risk Scoring:** Implemented CVSS-aligned risk score formula combining base severity weights (Critical 9.5 to Info 0.5) with evaluation confidence multipliers (Confirmed 1.0 to Low 0.4).
3. **Remediation Catalog:** Built `engine/scoring/remediation.py` containing concrete engineering playbooks and OWASP/CWE references for each vulnerability category.
4. **Deduplication Engine:** Implemented `FindingsManager` in `engine/scoring/manager.py` using SHA-256 root-cause fingerprinting to consolidate multiple related test failures into single actionable findings with full evidence chains.
5. **Scanner & CLI Dashboard:** Enhanced `run_scan.py` to display the Security Posture dashboard and export deduplicated findings with remediation guidance in JSON output.
6. **Phase 6 Report:** Compiled comprehensive learning report in `docs/phase-reports/PHASE_06_REPORT.md`.

### Decisions & Trade-Offs
- **Decision:** Deduplicate test failures using deterministic SHA-256 fingerprinting on (Category + OWASP + Severity).
  - *Reasoning:* Prevents alert fatigue and noisy bug tracking by presenting a single defect per architectural flaw while preserving all individual test payloads as supporting evidence.
- **Decision:** Combine Base Severity Weight with Confidence Multipliers for a quantitative 0.0 - 10.0 risk score.
  - *Reasoning:* Ensures that high-severity rules do not trigger panic if the detection confidence is low, providing realistic, actionable prioritization.

---

## [Phase 5] Evaluation Engine
- **Date Completed:** 2026-11-23
- **Status:** Completed

### Completed Milestones
1. **Evaluation Models:** Defined `TestStatus`, `ConfidenceLevel`, and `EvaluationResult` in `engine/evaluators/models.py`.
2. **Deterministic Evaluators:** Built `ExactMatchEvaluator` (token leakage), `RBACRetrievalEvaluator` (unauthorized document access), `PatternMatchEvaluator` (regex), and `PolicyRefusalEvaluator` (refusal assertions).
3. **Composite Pipeline:** Implemented `EvaluationPipeline` in `engine/evaluators/pipeline.py` to prioritize high-confidence deterministic checks and aggregate statistics.
4. **CLI Integration:** Updated `run_scan.py` to automatically evaluate execution results and output the Security Verdict table.
5. **Phase 5 Report:** Compiled comprehensive learning report in `docs/phase-reports/PHASE_05_REPORT.md`.

### Decisions & Trade-Offs
- **Decision:** Prioritize deterministic string, regex, and source citation checking over non-deterministic LLM-as-a-judge.
  - *Reasoning:* Eliminates hallucinations and false alarms, runs in microseconds, and costs zero API credits while providing mathematically verifiable proof.
- **Decision:** Keep Test Status (`PASS`/`FAIL`), Confidence (`CONFIRMED`/`HIGH`), and Severity (`CRITICAL`/`HIGH`) strictly separated.
  - *Reasoning:* Prevents low-confidence heuristic alerts from being misinterpreted as confirmed critical vulnerabilities.

---

## [Phase 4] Scan Orchestration and Execution
- **Date Completed:** 2026-11-22
- **Status:** Completed

### Completed Milestones
1. **Lifecycle Models:** Defined `ScanConfig`, `ScanStatus`, `TestExecutionResult`, `ScanProgress`, and `ScanSummary` in `engine/orchestrator/models.py`.
2. **Async Scan Orchestrator:** Engineered `engine/orchestrator/runner.py` with pre-flight health verification, `asyncio.Semaphore` concurrency gating, non-blocking cancellation, and progress telemetry.
3. **CLI Scanner Tool:** Built `run_scan.py` with ASCII banner, real-time percentage progress bar, and summary results table.
4. **Automated Verification:** Verified full 11-test scan execution, pre-flight fault tolerance, and filtered category scans.
5. **Phase 4 Report:** Compiled comprehensive learning report in `docs/phase-reports/PHASE_04_REPORT.md`.

### Decisions & Trade-Offs
- **Decision:** Use native `asyncio.Semaphore` for concurrency throttling rather than heavy external queuing systems at this stage.
  - *Reasoning:* Keeps the testing engine lightweight, self-contained, and blazingly fast with zero external dependencies while still protecting targets from Denial of Service.
- **Decision:** Include pre-flight health checks before launching test suites.
  - *Reasoning:* Prevents misleading test failures and saves time if the target application is offline or malfunctioning.

---

## [Phase 3] Test-Case Model and Attack Library
- **Date Completed:** 2026-11-22
- **Status:** Completed

### Completed Milestones
1. **OWASP Taxonomy Mapping:** Standardized `AttackCategory`, `OWASPCategory`, and `SeverityLevel` in `engine/attacks/categories.py`.
2. **Pydantic TestCase Schemas:** Built `TestCase`, `TestSuite`, and `EvaluationCriteria` in `engine/attacks/schema.py` with automated validation and OWASP assignment.
3. **Declarative Test Datasets:** Authored 11 parameterized security test cases in `datasets/test_cases/v1/` across direct injection, secret disclosure, unauthorized retrieval, and retrieval manipulation.
4. **Attack Registry:** Built `engine/attacks/registry.py` providing dataset discovery, duplicate ID detection, and multi-dimensional filtering.
5. **Phase 3 Report:** Compiled comprehensive learning report in `docs/phase-reports/PHASE_03_REPORT.md`.

### Decisions & Trade-Offs
- **Decision:** Separate test definitions (JSON) from test execution (Python).
  - *Reasoning:* Enables zero-code extensibility, allowing new security tests to be added and versioned without touching core engine logic.
- **Decision:** Enforce regex patterns on test IDs (`^[A-Z0-9_\-]+$`) and auto-assign OWASP categories via Pydantic model validators.
  - *Reasoning:* Guarantees structural uniformity and eliminates manual tagging errors across datasets.

---

## [Phase 2] Target Adapter and Integration
- **Date Completed:** 2026-11-20
- **Status:** Completed

### Completed Milestones
1. **Demo Target REST API:** Implemented `demo-rag/api.py` using FastAPI with `/health` and `/query` endpoints, Pydantic validation, and API key authentication.
2. **SSRF Defense Module:** Built `engine/targets/url_validator.py` with DNS resolution, link-local metadata protection (`169.254.169.254`), and strict private IP blocking.
3. **Target Adapter Contract:** Defined `BaseTargetAdapter`, `TargetResponse`, and `TargetHealth` in `engine/targets/base.py`.
4. **Async HTTP Target Adapter:** Implemented `engine/targets/http_adapter.py` using `httpx.AsyncClient` with field translation maps, latency profiling, and timeout resilience.
5. **Phase 2 Report:** Compiled comprehensive learning report in `docs/phase-reports/PHASE_02_REPORT.md`.

### Decisions & Trade-Offs
- **Decision:** Enforce SSRF validation on adapter initialization before opening network connections.
  - *Reasoning:* Eliminates the risk of RAGShield being used as an SSRF proxy to probe internal cloud metadata or local subnet services.
- **Decision:** Introduce configurable request and response field mapping in `HTTPTargetAdapter`.
  - *Reasoning:* Allows RAGShield to test arbitrary third-party RAG APIs without modifying internal security test suites.

---

## [Phase 1] RAG Fundamentals and Demonstration Target
- **Date Completed:** 2026-11-19
- **Status:** Completed

### Completed Milestones
1. **Synthetic Knowledge Base:** Created `public_handbook.txt`, `restricted_payroll.txt`, and `engineering_playbook.txt` with security classifications.
2. **Document Ingestion & Chunking:** Implemented `demo-rag/ingestion/loader.py` and `chunker.py` with sliding-window overlap and metadata preservation.
3. **Local Vector Storage:** Built `demo-rag/retrieval/vector_store.py` using ChromaDB with local persistent storage and cosine distance indexing.
4. **Grounded Generation:** Built `demo-rag/generation/prompt.py` and `generator.py` with deterministic local generation, citation formatting, and negative refusal logic.
5. **Unified Application & CLI:** Built `demo-rag/main.py` supporting indexing, CLI queries, and role-based access filtering (`public` vs `all`).
6. **Phase 1 Report:** Compiled comprehensive learning report in `docs/phase-reports/PHASE_01_REPORT.md`.

### Decisions & Trade-Offs
- **Decision:** Use ChromaDB with embedded ONNX `all-MiniLM-L6-v2` embeddings.
  - *Reasoning:* Enables 100% offline, zero-cost, local vector similarity search without requiring cloud API keys or external database daemons.
- **Decision:** Implement a deterministic mock generator alongside extensible LLM interfaces.
  - *Reasoning:* Enables reliable, automated testing without latency, API billing, or flakiness, while keeping the interface compatible with OpenAI/Ollama.
