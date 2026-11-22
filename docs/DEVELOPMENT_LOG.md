# RAGShield: Development Log

A chronological record of architectural decisions, completed milestones, active work, and next steps.

---

## [Phase 0] Project Discovery and Setup
- **Date Started:** 2026-11-18
- **Status:** In Progress

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
- Completed Phase 2 (Target Adapter and Integration) and Phase 2 Learning Report.
- Preparing to commit Phase 2 deliverables and start Phase 3 (Test-Case Model and Attack Library).

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
