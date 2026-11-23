"""Scan Run Management and Lifecycle REST API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.repositories.finding_repo import FindingRepository
from backend.app.repositories.scan_repo import ScanRepository
from backend.app.schemas.finding import TestResultResponse
from backend.app.schemas.scan import ScanLaunchRequest, ScanResponse
from backend.app.security import get_current_user, require_role
from backend.app.services.scan_service import ScanService

router = APIRouter(prefix="/scans", tags=["Scans"])


@router.post("/launch", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
async def launch_scan(
    request: ScanLaunchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "analyst"]))
):
    """Triggers an automated security scan in the background."""
    scan_service = ScanService(db)
    try:
        scan = await scan_service.launch_scan(
            target_id=request.target_id,
            triggered_by_id=current_user.id,
            request=request
        )
        return scan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[ScanResponse])
async def list_scans(
    target_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists recent scan runs, optionally filtered by target."""
    scan_repo = ScanRepository(db)
    if target_id:
        scans = await scan_repo.get_by_target(target_id=target_id, skip=skip, limit=limit)
    else:
        scans = await scan_repo.get_multi(skip=skip, limit=limit)
    return scans


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves status and summary metrics for a specific scan."""
    scan_repo = ScanRepository(db)
    scan = await scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID '{scan_id}' not found."
        )
    return scan


@router.get("/{scan_id}/results", response_model=List[TestResultResponse])
async def get_scan_results(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all granular test execution results for a scan run."""
    scan_repo = ScanRepository(db)
    scan = await scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID '{scan_id}' not found."
        )

    finding_repo = FindingRepository(db)
    return await finding_repo.get_results_by_scan_run(scan_id)
