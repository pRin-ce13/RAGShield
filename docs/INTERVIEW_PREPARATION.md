# RAGShield: Interview Preparation Guide

> **Purpose:** This living document prepares you to explain every engineering decision, architectural layer, and technical trade-off of RAGShield in technical placement interviews.

---

## 1. Project Elevators & High-Level Pitches

### The 30-Second Elevator Pitch
> *"RAGShield is an automated security testing and vulnerability assessment platform for Retrieval-Augmented Generation (RAG) applications. It connects to RAG systems through configurable adapters, executes controlled security tests—such as direct prompt injection, document poisoning, and unauthorized cross-department data extraction—and uses deterministic and semantic evaluators to produce actionable vulnerability reports mapped to OWASP LLM risks."*

### The 2-Minute Architectural Pitch
> *"Enterprises are rapidly deploying RAG architectures to connect LLMs to sensitive proprietary knowledge bases. However, traditional application scanners don't understand LLM semantics, and manual red-teaming doesn't scale.*
> 
> *I designed RAGShield with strict modular separation:*
> 1. *A target adapter layer that treats RAG targets as independent HTTP services, ensuring our scanner can test any arbitrary RAG framework.*
> 2. *An extensible attack library generating repeatable test payloads targeting prompt injection, synthetic secret disclosure, and access boundary violations.*
> 3. *A multi-method evaluation pipeline that uses deterministic exact/regex checks, policy assertions, and optional LLM-as-judge scoring, strictly separating confidence from severity.*
> 4. *A secure background execution engine with built-in SSRF protections and rate-limiting to prevent unintended denial of service during scans.*
> 5. *A persistent management backend and dashboard providing reproducibility, audit trails, and remediation guidance."*

---

## 2. Phase 0 Interview Questions & Model Answers

### Q1: Why did you initialize version control and `.gitignore` before writing any code?
**Model Answer:**
> *"Version control hygiene is fundamental. By creating `.gitignore` before generating code or virtual environments, we guaranteed that Python bytecode (`__pycache__`), virtual environment binaries (`.venv`), local vector databases (`chroma_db`), and sensitive files (`.env`) could never be accidentally staged or committed to Git. Fixing a leaked secret or bloated repository after the fact is costly; establishing strict boundaries on day zero prevents that technical debt."*

### Q2: Why use Python's built-in `venv` instead of global packages or conda?
**Model Answer:**
> *"Installing packages globally risks dependency drift and version conflicts across different projects on the host machine. While `conda` is great for complex C-extension or CUDA stacks, standard Python `venv` is built directly into Python 3.12, has zero installation overhead, and provides complete isolation by redirecting the interpreter's package resolution path (`sys.prefix`) to a dedicated local directory."*

### Q3: Why is `.env.example` committed, but `.env` ignored?
**Model Answer:**
> *"The 12-Factor App methodology mandates strict separation of config from code. `.env.example` serves as an explicit, version-controlled schema documenting the environment variables the application requires (with placeholder values). In contrast, `.env` contains the developer's actual local secrets and connection strings, which must never be committed to source control."*

### Q4: How does RAGShield prevent Server-Side Request Forgery (SSRF) when scanning targets?
**Model Answer:**
> *"Because RAGShield is designed to connect to user-supplied HTTP target URLs, a malicious or careless user could configure the scanner to probe internal cloud metadata services (e.g. `169.254.169.254`) or internal microservices. In our architecture, the target adapter layer enforces strict IP and domain validation, blocking loopback and private subnets by default unless an explicit local development override flag is set."*

---

## 3. Whiteboard Architecture Diagram

```text
[ User / CI Pipeline ]
         │
         ▼
 ┌───────────────┐        ┌───────────────────────┐
 │   FastAPI     │◄──────►│  PostgreSQL & Redis   │
 │ Backend API   │        │ (Scans, Results, Auth)│
 └───────┬───────┘        └───────────────────────┘
         │ Enqueue Scans
         ▼
 ┌─────────────────────────────────────────────────────────┐
 │            RAGShield Testing Engine                     │
 │  ┌─────────────────┐             ┌───────────────────┐  │
 │  │ Attack Library  │             │ Multi-Method      │  │
 │  │ (Injections,    │             │ Evaluators        │  │
 │  │  Secret Leaks)  │             │ (Regex, Policy,   │  │
 │  └────────┬────────┘             │  LLM Judge)       │  │
 │           │ Payload              └─────────▲─────────┘  │
 │           ▼                                │ Evidence   │
 │  ┌─────────────────┐                       │            │
 │  │ Target Adapter  ├───────────────────────┘            │
 │  │ (SSRF Protected)│                                    │
 └───────────┬─────────────────────────────────────────────┘
             │ HTTP Request / Response
             ▼
 ┌─────────────────────────────────────────────────────────┐
 │  Target RAG Application (e.g., demo-rag)                │
 │  [ Document Ingestion -> Vector Store -> LLM Answer ]   │
 └─────────────────────────────────────────────────────────┘
```
