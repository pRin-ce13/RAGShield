"""Vulnerability Findings and Risk Posture REST API Endpoints."""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.repositories.finding_repo import FindingRepository
from backend.app.repositories.scan_repo import ScanRepository
from backend.app.schemas.finding import FindingResponse, RiskProfileResponse
from backend.app.security import get_current_user

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("/{scan_id}", response_model=List[FindingResponse])
async def get_scan_findings(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all deduplicated vulnerability findings for a scan run."""
    scan_repo = ScanRepository(db)
    scan = await scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID '{scan_id}' not found."
        )

    finding_repo = FindingRepository(db)
    db_findings = await finding_repo.get_by_scan_run(scan_id)

    response_list: List[FindingResponse] = []
    for f in db_findings:
        evidence_instances = json.loads(f.evidence_json or "[]")
        remediation_steps = json.loads(f.remediation_steps_json or "[]")
        references = json.loads(f.references_json or "[]")

        response_list.append(
            FindingResponse(
                id=f.id,
                scan_run_id=f.scan_run_id,
                finding_id=f.finding_id,
                fingerprint=f.fingerprint,
                title=f.title,
                category=f.category,
                owasp_category=f.owasp_category,
                severity=f.severity,
                confidence=f.confidence,
                risk_score=f.risk_score,
                description=f.description,
                affected_target=f.affected_target,
                evidence_count=f.evidence_count,
                evidence_instances=evidence_instances,
                remediation_summary=f.remediation_summary,
                remediation_steps=remediation_steps,
                references=references,
                created_at=f.created_at
            )
        )

    return response_list


@router.get("/{scan_id}/posture", response_model=RiskProfileResponse)
async def get_scan_risk_posture(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculates overall security posture rating and severity distribution."""
    scan_repo = ScanRepository(db)
    scan = await scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID '{scan_id}' not found."
        )

    finding_repo = FindingRepository(db)
    findings = await finding_repo.get_by_scan_run(scan_id)

    crit = sum(1 for f in findings if f.severity.upper() == "CRITICAL")
    high = sum(1 for f in findings if f.severity.upper() == "HIGH")
    med = sum(1 for f in findings if f.severity.upper() == "MEDIUM")
    low = sum(1 for f in findings if f.severity.upper() == "LOW")

    return RiskProfileResponse(
        total_findings=len(findings),
        overall_posture=scan.overall_posture or "SECURE",
        max_risk_score=scan.max_risk_score,
        critical_count=crit,
        high_count=high,
        medium_count=med,
        low_count=low
    )
