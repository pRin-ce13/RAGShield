# RAGShield: Tech Stack & Library Reference

> **Living Document**: This ledger tracks every programming language, library, framework, and tool used in RAGShield, along with the technical justification for its selection, alternatives considered, and code examples.

---

## 1. Classification of Software Dependencies

To understand our dependency choices, we categorize all technologies into five distinct layers:

| Category | Definition | Example in RAGShield |
| :--- | :--- | :--- |
| **Python Built-in Modules** | Libraries that ship directly inside Python's standard distribution. Require zero installation via `pip`. | `venv`, `json`, `pathlib`, `re` |
| **Third-Party Packages** | External Python libraries developed by the open-source community, installed via `pip` into `.venv`. | `httpx`, `pydantic` *(coming in future phases)* |
| **Frameworks** | Large architectural software packages that invert control and dictate application structure. | `FastAPI`, `React` *(future phases)* |
| **Development & Testing Tools** | Packages used only during coding, static analysis, and automated testing (never in production). | `pytest`, `ruff` *(future phases)* |
| **Infrastructure Services** | Standalone server software running outside of Python, communicating via network sockets. | `PostgreSQL`, `Redis` *(future phases)* |

---

## 2. Dependency Ledger

### Python 3.12 Standard Runtime
- **Category:** Core Runtime / Language
- **What it is:** The official CPython 3.12 interpreter.
- **Why RAGShield needs it:** Provides the execution environment for backend services, scan orchestrators, and testing modules.
- **Why selected:** Python 3.12 offers substantial performance improvements over 3.10/3.11 (improved specializing adaptive interpreter) and excellent type hinting support.
- **Alternatives considered:** Python 3.11, Python 3.13 (too recent; some AI/vector packages have wheel compatibility issues on 3.13 in Windows).

### `venv` (Standard Library)
- **Category:** Python Built-in Module
- **What it is:** Python's native virtual environment isolation mechanism.
- **Why RAGShield needs it:** Isolates RAGShield dependencies from system-wide Python packages, preventing version collisions.
- **Where it is used:** Project root directory (`.venv/`).
- **How it works:** Creates a folder with a copy/symlink of the Python executable and configures `sys.prefix` so that `pip` installs packages exclusively within that local folder.
- **Alternatives considered:** 
  - `virtualenv`: Third-party tool, largely superseded by built-in `venv` for standard use cases.
  - `conda` / `miniconda`: Useful for heavy C/CUDA dependencies, but introduces unnecessary complexity for our standard async web and testing stack.
  - `poetry` / `uv`: Modern package managers. We start with standard `venv` + `pip` to ensure complete foundational understanding before introducing packaging wrappers.
- **Dependency Type:** Built-in / Development environment.

### `chromadb`
- **Category:** Third-Party Python Package
- **What it is:** An open-source, lightweight embedded AI vector database.
- **Why RAGShield needs it:** Serves as the vector indexing and semantic retrieval engine for our local demonstration target (`demo-rag/`).
- **Which feature/module uses it:** `demo-rag/retrieval/`
- **How it works at a high level:** ChromaDB stores document text chunks, metadata, and high-dimensional vector embeddings. It uses an in-process SQLite database for document metadata and an Approximate Nearest Neighbor index (HNSW algorithm) to compute cosine/L2 distance between the query embedding and stored document embeddings.
- **Small example from our code:**
  ```python
  import chromadb

  client = chromadb.PersistentClient(path="./chroma_db")
  collection = client.get_or_create_collection(name="acme_knowledge_base")
  collection.add(
      documents=["Acme meal stipend is up to $75/day."],
      metadatas=[{"source": "public_handbook.txt", "classification": "PUBLIC"}],
      ids=["doc_1_chunk_1"]
  )
  results = collection.query(query_texts=["How much can I spend on food?"], n_results=1)
  ```
- **Alternatives considered:**
  - **FAISS (Facebook AI Similarity Search):** Fast and lightweight, but lacks built-in metadata filtering, persistence management, and document storage. You have to maintain a separate SQLite database to map vector IDs back to text.
  - **Pinecone / Weaviate / Qdrant Cloud:** Managed cloud services. Require API keys, internet connectivity, and monthly fees. Not ideal for a self-contained local demonstration and offline testing.
- **Why selected:** It runs 100% locally in-process on Windows, is open-source, requires zero Docker or database setup, and comes with a lightweight default CPU embedding model for zero-cost semantic search.
- **Dependency Type:** Direct dependency (`requirements.txt`).
- **Security & Compatibility Considerations:** Vector databases for the target application (`demo-rag`) are strictly isolated from RAGShield's application database (PostgreSQL in Phase 7) to guarantee that target vector storage can never pollute RAGShield's scan evidence database.

### `fastapi`
- **Category:** Framework (Web API)
- **What it is:** A modern, high-performance web framework for building RESTful APIs with Python 3.8+ based on standard Python type hints.
- **Why RAGShield needs it:** Serves as the web API layer for both our demonstration target (`demo-rag/api.py`) and later RAGShield's main backend service (`backend/` in Phase 7).
- **Which feature/module uses it:** `demo-rag/api.py` and `backend/`
- **How it works at a high level:** Runs on top of Starlette and AnyIO using an ASGI server (Uvicorn). Requests are parsed and validated automatically against Pydantic models before entering route handlers.
- **Small example from our code:**
  ```python
  from fastapi import FastAPI
  from pydantic import BaseModel

  app = FastAPI(title="Acme Demo RAG API")

  class QueryRequest(BaseModel):
      question: str
      role: str = "all"

  @app.post("/query")
  async def query_endpoint(req: QueryRequest):
      return {"answer": "...", "sources": []}
  ```
- **Alternatives considered:**
  - **Flask:** Synchronous by default, lacks native OpenAPI generation and built-in type hint validation without heavy extensions.
  - **Django / Django REST Framework:** Overkill; introduces heavy ORM and monolithic overhead for lightweight API microservices.
- **Why selected:** Asynchronous by design (`async def`), ultra-fast, native Pydantic validation, and automatic OpenAPI interactive Swagger documentation at `/docs`.
- **Dependency Type:** Direct dependency (`requirements.txt`).
- **Security Considerations:** Enforces request body validation, preventing malformed JSON payloads and unexpected field types.

### `httpx`
- **Category:** Third-Party Python Package (HTTP Client)
- **What it is:** A next-generation HTTP client for Python, supporting both synchronous and fully asynchronous requests.
- **Why RAGShield needs it:** Powers RAGShield's Target Adapter (`engine/targets/http_adapter.py`) to execute security tests and scan probes against remote RAG APIs over HTTP/HTTPS.
- **Which feature/module uses it:** `engine/targets/http_adapter.py`
- **How it works at a high level:** Provides an asynchronous client (`httpx.AsyncClient`) that integrates with Python's `asyncio` event loop. It can fire hundreds of HTTP requests concurrently without spawning multiple operating system threads.
- **Small example from our code:**
  ```python
  import httpx

  async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.post(
          "http://127.0.0.1:8001/query",
          json={"question": "What is the travel policy?"}
      )
      data = response.json()
  ```
- **Alternatives considered:**
  - **`requests`:** The traditional standard, but strictly synchronous and blocking. Running concurrent scans with `requests` requires cumbersome multi-threading or multi-processing pools.
  - **`aiohttp`:** Fast and asynchronous, but has a more verbose API and less intuitive timeout/connection configuration than `httpx`.
- **Why selected:** Clean API identical to `requests`, native `async/await` support, HTTP/2 support, and granular timeout configurations (connect, read, write, pool).
- **Dependency Type:** Direct dependency (`requirements.txt`).
- **Security Considerations:** Target adapters must pair `httpx` with strict timeout controls and SSRF URL validation to prevent connection hanging and internal network probing.

### `sqlalchemy`
- **Category:** Third-Party Python Package / ORM
- **What it is:** The premier Python SQL toolkit and Object Relational Mapper (ORM), providing an expressive, database-agnostic interface to relational databases.
- **Why RAGShield needs it:** Persists target configurations, scan runs, test results, vulnerability findings, and user accounts in a relational database.
- **Which feature/module uses it:** `backend/app/models/`, `backend/app/database/`, `backend/app/repositories/`
- **How it works at a high level:** SQLAlchemy 2.0 maps Python classes derived from `DeclarativeBase` to database tables. With `AsyncSession` and `create_async_engine`, database queries (`select(Target).where(...)`) execute asynchronously without blocking the event loop.
- **Small example from our code:**
  ```python
  from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
  from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

  class Base(DeclarativeBase):
      pass

  class Target(Base):
      __tablename__ = "targets"
      id: Mapped[str] = mapped_column(primary_key=True)
      name: Mapped[str] = mapped_column()
  ```
- **Alternatives considered:**
  - **Raw SQL (sqlite3 / psycopg2):** Error-prone, lacks automatic schema type-safety and dialect translation.
  - **Tortoise-ORM / Peewee:** Smaller community, less enterprise tooling, and limited Alembic migration integration.
- **Why selected:** Industry standard, battle-tested, excellent async support in v2.0+, and seamless integration with Alembic.
- **Dependency Type:** Direct dependency (`requirements.txt`).
- **Security Considerations:** SQLAlchemy automatically utilizes parameterized SQL queries, completely eliminating SQL injection vulnerabilities.

### `aiosqlite`
- **Category:** Third-Party Python Package (Database Driver)
- **What it is:** An asynchronous interface to SQLite databases using Python's `asyncio` event loop.
- **Why RAGShield needs it:** Serves as the asynchronous SQLite driver for SQLAlchemy (`sqlite+aiosqlite:///...`), enabling zero-configuration persistent storage in local development and automated testing.
- **Which feature/module uses it:** `backend/app/database/session.py`
- **How it works at a high level:** Wraps standard `sqlite3` operations in thread-pool executors to present a clean `async/await` API that integrates with SQLAlchemy's `AsyncEngine`.
- **Alternatives considered:**
  - Standard `sqlite3`: Synchronous and blocking; causes event loop lag in FastAPI.
  - Mandatory `PostgreSQL` (`asyncpg`): Requires running Docker or a local database server, complicating local evaluation.
- **Why selected:** Provides non-blocking persistence with zero setup. In Phase 11, switching to PostgreSQL is accomplished merely by updating the `DATABASE_URL` environment variable.
- **Dependency Type:** Direct dependency (`requirements.txt`).

### `alembic`
- **Category:** Third-Party Development & Migration Tool
- **What it is:** A lightweight database migration tool written for SQLAlchemy.
- **Why RAGShield needs it:** Manages evolutionary schema migrations, tracking database version revisions over time and applying automated schema changes.
- **Which feature/module uses it:** `backend/alembic/`
- **How it works at a high level:** Inspects the SQLAlchemy metadata and compares it against the database catalog to generate versioned migration scripts (`upgrade()` and `downgrade()`).
- **Alternatives considered:** Manual SQL schema update scripts.
- **Why selected:** Standard migration framework for SQLAlchemy with automated schema comparison and rollback support.
- **Dependency Type:** Direct dependency (`requirements.txt`).

### `pydantic-settings`
- **Category:** Third-Party Python Package
- **What it is:** Environment variable parsing and application configuration management based on Pydantic models.
- **Why RAGShield needs it:** Safely parses, validates, and manages environment variables from `.env` files (e.g. database URLs, JWT secret keys, token expiry).
- **Which feature/module uses it:** `backend/app/core/config.py`
- **How it works at a high level:** Inherits from `BaseSettings`. At startup, it reads OS environment variables and `.env` files, validates data types, and raises errors if critical configurations are missing.
- **Alternatives considered:** `python-dotenv` with manual `os.getenv()` calls (lacks type-safety and validation).
- **Why selected:** Extracted from Pydantic v1 into a dedicated library for Pydantic v2; provides strict types, default values, and secrets masking.
- **Dependency Type:** Direct dependency (`requirements.txt`).

### `passlib[bcrypt]` & `bcrypt`
- **Category:** Third-Party Security Package
- **What it is:** A comprehensive password hashing library providing secure, salted bcrypt password hashes.
- **Why RAGShield needs it:** Securely hashes user passwords before storing them in the database, ensuring raw passwords are never saved.
- **Which feature/module uses it:** `backend/app/security/passwords.py`
- **How it works at a high level:** Uses the adaptive bcrypt hashing function with a randomly generated salt and configurable work factor (rounds), protecting against rainbow table and brute-force attacks.
- **Alternatives considered:** Plain SHA-256 (insecure for passwords; lacks salt and key-stretching), Argon2 (more complex C dependency on Windows).
- **Why selected:** Industry standard, NIST-approved, and native integration with FastAPI security patterns.
- **Dependency Type:** Direct dependency (`requirements.txt`).

### `pyjwt`
- **Category:** Third-Party Security Package
- **What it is:** A Python implementation of RFC 7519 (JSON Web Tokens).
- **Why RAGShield needs it:** Generates, signs, and decodes stateless JWT bearer tokens for user authentication and role-based access control.
- **Which feature/module uses it:** `backend/app/security/jwt.py`
- **How it works at a high level:** Encodes a JSON claims payload (user ID, username, roles, expiration timestamp) signed with a cryptographic HMAC-SHA256 secret key.
- **Alternatives considered:** `python-jose` (older, slower release cadence, maintenance concerns).
- **Why selected:** Actively maintained, zero dependencies, high performance, and secure token decoding with strict claim verification.
- **Dependency Type:** Direct dependency (`requirements.txt`).

### `email-validator`
- **Category:** Third-Party Python Package
- **What it is:** A robust email address syntax and deliverability validation library.
- **Why RAGShield needs it:** Enables Pydantic `EmailStr` field validation on user registration and authentication payloads.
- **Which feature/module uses it:** `backend/app/schemas/user.py`
- **How it works at a high level:** Validates email addresses against RFC 5322 specifications, parses domain names, and normalizes email formats.
- **Alternatives considered:** Custom regex (error-prone and fails on valid edge cases like plus-addressing or new TLDs).
- **Why selected:** Official validation provider for Pydantic v2 `EmailStr`.
- **Dependency Type:** Direct dependency (`requirements.txt`).

### `python-multipart`
- **Category:** Third-Party Python Package
- **What it is:** A streaming multipart/form-data and urlencoded parser for Python.
- **Why RAGShield needs it:** Powers FastAPI's `OAuth2PasswordRequestForm` parsing at `/api/v1/auth/login`.
- **Which feature/module uses it:** `backend/app/api/v1/auth.py`
- **How it works at a high level:** Parses incoming `application/x-www-form-urlencoded` HTTP bodies into Python form dictionaries for OAuth2 compliance.
- **Alternatives considered:** JSON-only login (OAuth2 standard Swagger UI expects form data).
- **Why selected:** Required by FastAPI for OAuth2 password grant form support.
- **Dependency Type:** Direct dependency (`requirements.txt`).

### `React` (v19)
- **Category:** Frontend UI Framework
- **What it is:** The declarative component-based UI library developed by Meta.
- **Why RAGShield needs it:** Powers the single-page application (SPA) dashboard for monitoring scans, managing targets, and inspecting vulnerabilities.
- **Which feature/module uses it:** `frontend/src/`
- **How it works at a high level:** Maintains an in-memory Virtual DOM tree, reconciles state transitions, and renders DOM elements efficiently based on reactive state changes.
- **Alternatives considered:** Vue, Svelte, Plain HTML/Jinja2 (SSR). React with pure JavaScript (`.jsx`) was selected to provide a modern, reactive single-page app while avoiding TypeScript complexity for backend-focused engineers.
- **Dependency Type:** Direct frontend dependency (`frontend/package.json`).

### `Vite` (v6)
- **Category:** Frontend Build Tool & Dev Server
- **What it is:** Next-generation frontend tooling offering fast development server start times using native ES modules.
- **Why RAGShield needs it:** Bundles and optimizes frontend JavaScript, CSS, and JSX assets for production, and provides development API proxying to FastAPI.
- **Which feature/module uses it:** `frontend/vite.config.js`
- **How it works at a high level:** Uses `esbuild` for pre-bundling dependencies and `Rollup` for highly optimized, tree-shaken production asset generation into `frontend/dist/`.
- **Alternatives considered:** Webpack (slower, more complex configuration), Create React App (deprecated).
- **Dependency Type:** Development dependency (`frontend/package.json`).

### `Tailwind CSS` (v3)
- **Category:** Utility-First CSS Framework
- **What it is:** A utility-first CSS framework that generates classes on demand directly from component source code.
- **Why RAGShield needs it:** Provides a responsive, sleek DevSecOps dark-mode UI theme with zero custom CSS stylesheet overhead.
- **Which feature/module uses it:** `frontend/src/index.css`, `frontend/tailwind.config.js`
- **How it works at a high level:** Scans template and component files for utility class names, generates corresponding CSS using PostCSS, and purges unused styles during production build.
- **Alternatives considered:** Bootstrap, MUI/Material-UI (heavier runtime overhead, opinionated default styles).
- **Dependency Type:** Development dependency (`frontend/package.json`).

### `Lucide React`
- **Category:** UI Component & Icon Library
- **What it is:** An open-source, lightweight icon library for React applications.
- **Why RAGShield needs it:** Provides standard DevSecOps iconography (shields, alerts, terminal, checks, targets) across dashboard views.
- **Which feature/module uses it:** `frontend/src/components/`
- **How it works at a high level:** Exports SVG icons as lightweight, customizable React components that support Tailwind CSS classes for sizing and color.
- **Alternatives considered:** FontAwesome, React Icons.
- **Dependency Type:** Direct frontend dependency (`frontend/package.json`).

### `reportlab` (v5.1)
- **Category:** Third-Party Python Package (PDF Generation Engine)
- **What it is:** The open-source standard Python library for programmatically generating PDF documents and graphics.
- **Why RAGShield needs it:** Generates professional, publication-quality executive security assessment reports and audit documentation.
- **Which feature/module uses it:** `engine/reporting/pdf_reporter.py`
- **How it works at a high level:** Uses ReportLab's Platypus (Page Layout and Typography Using Scripts) engine. It constructs a "Story" of flowable elements (`Paragraph`, `Table`, `Spacer`, `KeepTogether`) and compiles them onto a `SimpleDocTemplate` canvas, automatically handling multi-page pagination, word-wrapping, and color-coded severity tables.
- **Small example from our code:**
  ```python
  from reportlab.lib.pagesizes import letter
  from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer
  from reportlab.lib.styles import getSampleStyleSheet

  doc = SimpleDocTemplate("report.pdf", pagesize=letter)
  story = [Paragraph("RAGShield Audit Report", getSampleStyleSheet()["Heading1"])]
  doc.build(story)
  ```
- **Alternatives considered:**
  - **WeasyPrint:** Converts HTML/CSS to PDF via headless browser engine. Extremely heavy; requires native C libraries (cairo, pango, gdk-pixbuf) that are notoriously difficult to install and maintain on Windows environments without external DLLs.
  - **xhtml2pdf:** Converts HTML to PDF, but has buggy CSS3 support, poorly supported table wrapping, and frequent rendering artifacts.
  - **PyPDF2 / pypdf:** PDF manipulation/concatenation libraries only; cannot easily generate complex styled documents from scratch.
- **Why selected:** 100% pure Python runtime on Windows, zero external C library dependencies, deterministic multi-page flow layout, and enterprise-grade styling control.
- **Dependency Type:** Direct backend dependency (`requirements.txt`).

---

*(Additional libraries will be documented here as they are added in their respective phases.)*
