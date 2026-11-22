"""FastAPI HTTP REST API service for Acme Demo RAG Target.

Provides /health and /query endpoints to allow external HTTP clients (like RAGShield)
to perform automated security scanning against the target.
"""

from contextlib import asynccontextmanager
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

# Ensure local imports resolve cleanly
CURRENT_DIR = Path(__file__).parent.resolve()
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from main import RAGApplication

# Synthetic API Key for demonstration security testing
EXPECTED_API_KEY = "demo_synthetic_insecure_key_for_testing"

# Global RAG application instance
rag_app: Optional[RAGApplication] = None


def get_rag_app() -> RAGApplication:
    """Returns the initialized RAGApplication singleton, lazily creating it if needed."""
    global rag_app
    if rag_app is None:
        rag_app = RAGApplication(
            persist_dir="data/demo_chroma",
            docs_dir="datasets/synthetic_documents",
            generator_provider="mock"
        )
        rag_app.initialize(force_reindex=False)
    return rag_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes the RAG application and ChromaDB collection on server startup."""
    get_rag_app()
    yield


app = FastAPI(
    title="Acme Global Demo RAG Target API",
    description="Target RAG application for RAGShield security vulnerability assessments.",
    version="1.0.0",
    lifespan=lifespan
)


# --- Request & Response Models ---

class QueryRequest(BaseModel):
    """Schema for querying the RAG application."""
    question: str = Field(..., min_length=1, description="Question for the knowledge assistant")
    role: str = Field("all", description="Access role boundary ('public' or 'all')")
    top_k: int = Field(3, ge=1, le=10, description="Maximum number of context chunks to retrieve")


class ChunkMetadata(BaseModel):
    """Metadata representing a single retrieved text chunk."""
    chunk_id: str
    distance: float
    classification: Optional[str] = None
    source: Optional[str] = None
    text: str


class QueryResponse(BaseModel):
    """Schema for the RAG assistant's answer and evidence."""
    question: str
    answer: str
    sources: List[str]
    role: str
    model: str
    chunks_retrieved: List[ChunkMetadata]


class HealthResponse(BaseModel):
    """Schema for service health status."""
    status: str
    service: str
    version: str
    chunks_indexed: int


# --- API Routes ---

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Returns the operational status and indexed chunk count of the demo RAG target."""
    app_instance = get_rag_app()
    count = app_instance.vector_store.count()
    return HealthResponse(
        status="healthy",
        service="acme-demo-rag-target",
        version="1.0.0",
        chunks_indexed=count
    )


@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query_target(
    request: QueryRequest,
    x_api_key: Optional[str] = Header(None, description="Optional API key for authorization")
):
    """Queries the knowledge base and generates a grounded response.
    
    If the caller specifies an invalid API key, access is rejected with HTTP 401.
    If no key is provided, the service permits the query in demonstration mode.
    """
    app_instance = get_rag_app()

    # Demonstrate API Key validation for security testing
    if x_api_key is not None and x_api_key != EXPECTED_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unauthorized API key provided."
        )

    result = app_instance.query(
        question=request.question,
        role=request.role,
        top_k=request.top_k
    )

    return QueryResponse(**result)


def start_server(host: str = "127.0.0.1", port: int = 8001):
    """Starts the Uvicorn ASGI server."""
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Start Demo RAG HTTP API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind")
    args = parser.parse_args()
    start_server(host=args.host, port=args.port)
