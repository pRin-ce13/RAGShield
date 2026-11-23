"""Target RAG Application Management REST API Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.repositories.target_repo import TargetRepository
from backend.app.schemas.target import (
    TargetCreate,
    TargetHealthResponse,
    TargetResponse,
    TargetUpdate,
)
from backend.app.security import get_current_user, require_role
from backend.app.services.target_service import TargetService

router = APIRouter(prefix="/targets", tags=["Targets"])


@router.post("/", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_in: TargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "analyst"]))
):
    """Registers a new target RAG application."""
    target_repo = TargetRepository(db)
    existing = await target_repo.get_by_name(target_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target with name '{target_in.name}' already exists."
        )

    target = await target_repo.create_target(target_in)
    return target


@router.get("/", response_model=List[TargetResponse])
async def list_targets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists registered target RAG applications."""
    target_repo = TargetRepository(db)
    targets = await target_repo.get_active_targets(skip=skip, limit=limit)
    return targets


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves target details by ID."""
    target_repo = TargetRepository(db)
    target = await target_repo.get(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target with ID '{target_id}' not found."
        )
    return target


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: str,
    target_in: TargetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "analyst"]))
):
    """Updates target RAG configuration."""
    target_repo = TargetRepository(db)
    updated = await target_repo.update_target(target_id, target_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target with ID '{target_id}' not found."
        )
    return updated


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Deletes a target configuration (Admin only)."""
    target_repo = TargetRepository(db)
    deleted = await target_repo.delete(target_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target with ID '{target_id}' not found."
        )
    return None


@router.post("/{target_id}/check", response_model=TargetHealthResponse)
async def check_target_connectivity(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers an active pre-flight connectivity check and SSRF verification."""
    target_repo = TargetRepository(db)
    target = await target_repo.get(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target with ID '{target_id}' not found."
        )

    return await TargetService.verify_connectivity(target)
