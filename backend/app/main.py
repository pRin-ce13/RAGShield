"""FastAPI Main Application Entrypoint for RAGShield Security Platform.

Provides REST APIs for target registration, async scan orchestration,
deduplicated vulnerability findings, and role-based access control.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.app.api.v1 import api_v1_router
from backend.app.core.config import settings
from backend.app.database.session import AsyncSessionLocal, init_db
from backend.app.models.user import User, UserRole
from backend.app.repositories.user_repo import UserRepository
from backend.app.security.passwords import get_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ragshield.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema and ensures default admin account exists."""
    logger.info("Initializing RAGShield Backend Service...")
    await init_db()

    # Seed default admin user if database is empty
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        admin = await user_repo.get_by_email("admin@ragshield.sec")
        if not admin:
            admin_user = User(
                email="admin@ragshield.sec",
                hashed_password=get_password_hash("AdminSecPass2026!"),
                full_name="RAGShield System Administrator",
                role=UserRole.ADMIN
            )
            session.add(admin_user)
            await session.commit()
            logger.info("Created default system administrator: admin@ragshield.sec")

    yield
    logger.info("Shutting down RAGShield Backend Service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Automated Security Testing and Vulnerability Assessment Platform for RAG Applications. "
        "Provides target management, asynchronous vulnerability assessments, CVSS-aligned risk scoring, "
        "and concrete remediation playbooks."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware (allows frontend dashboard access in Phase 8)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Structured Error Handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Formats HTTP exceptions into a structured, consistent JSON envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        headers=getattr(exc, "headers", None)
    )


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    """Catches unhandled server exceptions and returns a safe diagnostic response."""
    logger.exception(f"Unhandled exception at {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "detail": "An internal server error occurred.",
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# Static frontend paths
FRONTEND_DIST = WORKSPACE_ROOT / "frontend" / "dist"

# Mount static asset bundles if present
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static-assets")

# Root & Health Endpoints
@app.get("/", tags=["UI"])
async def root():
    """Serves the React DevSecOps dashboard if built, otherwise returns API discovery JSON."""
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "api_v1": settings.API_V1_STR
    }


@app.get("/api/info", tags=["Health"])
async def api_info():
    """API discovery and version metadata."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "api_v1": settings.API_V1_STR
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Service health probe."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Mount API Routers
app.include_router(api_v1_router)

# Catch-all client-side routing fallback for React SPA
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
