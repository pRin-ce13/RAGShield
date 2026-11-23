"""API v1 Package."""

from fastapi import APIRouter
from .auth import router as auth_router
from .findings import router as findings_router
from .scans import router as scans_router
from .targets import router as targets_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(targets_router)
api_v1_router.include_router(scans_router)
api_v1_router.include_router(findings_router)

__all__ = ["api_v1_router"]
