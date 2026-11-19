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

---

*(Additional libraries will be documented here as they are added in their respective phases.)*
