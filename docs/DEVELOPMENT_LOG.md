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
- Finalizing Step 0.3 living documentation and preparing Step 0.4 (first Git commit and Phase 0 completion report).
