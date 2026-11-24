"""Security Audit Reporting and Scan Diffing REST API Endpoints."""

import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.repositories.finding_repo import FindingRepository
from backend.app.repositories.scan_repo import ScanRepository
from backend.app.repositories.target_repo import TargetRepository
from backend.app.security import get_current_user
from engine.attacks.categories import AttackCategory, OWASPCategory, SeverityLevel
from engine.evaluators.models import ConfidenceLevel, EvaluationResult, TestStatus
from engine.orchestrator.models import ScanStatus, ScanSummary, TestExecutionResult
from engine.attacks.schema import TestCase
from engine.scoring.models import VulnerabilityFinding, EvidenceInstance
from engine.reporting import (
    build_security_report,
    generate_pdf_report,
    compare_scans,
    ScanComparisonResult,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


async def _assemble_report_data(
    scan_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """Helper to reconstruct structured report data from database models."""
    scan_repo = ScanRepository(db)
    scan = await scan_repo.get(scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with ID '{scan_id}' not found."
        )

    target_repo = TargetRepository(db)
    target = await target_repo.get(scan.target_id)
    target_name = target.name if target else "Evaluated Target"
    target_url = target.target_url if target else "Unknown"

    finding_repo = FindingRepository(db)
    db_findings = await finding_repo.get_by_scan_run(scan_id)
    db_results = await finding_repo.get_results_by_scan_run(scan_id)

    # Reconstruct VulnerabilityFinding objects
    findings: List[VulnerabilityFinding] = []
    for f in db_findings:
        raw_evidence = json.loads(f.evidence_json or "[]")
        evidence_instances = [
            EvidenceInstance(
                test_id=ev.get("test_id", "N/A"),
                test_name=ev.get("test_name", "N/A"),
                payload=ev.get("payload", ""),
                evidence_snippet=ev.get("evidence_snippet", ""),
                target_role=ev.get("target_role"),
                latency_ms=float(ev.get("latency_ms", 0.0))
            )
            for ev in raw_evidence
        ]
        remediation_steps = json.loads(f.remediation_steps_json or "[]")
        references = json.loads(f.references_json or "[]")

        findings.append(
            VulnerabilityFinding(
                finding_id=f.finding_id,
                fingerprint=f.fingerprint,
                title=f.title,
                category=AttackCategory(f.category) if f.category in [c.value for c in AttackCategory] else AttackCategory.DIRECT_PROMPT_INJECTION,
                owasp_category=OWASPCategory(f.owasp_category) if f.owasp_category in [o.value for o in OWASPCategory] else None,
                severity=SeverityLevel(f.severity.upper()) if f.severity.upper() in [s.value for s in SeverityLevel] else SeverityLevel.MEDIUM,
                confidence=ConfidenceLevel(f.confidence.upper()) if f.confidence.upper() in [c.value for c in ConfidenceLevel] else ConfidenceLevel.HIGH,
                risk_score=f.risk_score,
                description=f.description,
                affected_target=f.affected_target or target_name,
                evidence_count=f.evidence_count,
                evidence_instances=evidence_instances,
                remediation_summary=f.remediation_summary,
                remediation_steps=remediation_steps,
                references=references,
                created_at=f.created_at
            )
        )

    # Reconstruct EvaluationResult objects
    evaluations: List[EvaluationResult] = []
    for r in db_results:
        evaluations.append(
            EvaluationResult(
                test_id=r.test_id,
                test_name=r.test_name,
                category=AttackCategory(r.category) if r.category in [c.value for c in AttackCategory] else AttackCategory.DIRECT_PROMPT_INJECTION,
                owasp_category=OWASPCategory(r.owasp_category) if r.owasp_category in [o.value for o in OWASPCategory] else None,
                severity=SeverityLevel(r.severity.upper()) if r.severity.upper() in [s.value for s in SeverityLevel] else SeverityLevel.MEDIUM,
                status=TestStatus(r.status.upper()) if r.status.upper() in [s.value for s in TestStatus] else TestStatus.ERROR,
                confidence=ConfidenceLevel(r.confidence.upper()) if r.confidence.upper() in [c.value for c in ConfidenceLevel] else ConfidenceLevel.MEDIUM,
                evaluator_name=r.evaluator_name or "EvaluationPipeline",
                evidence=r.evidence,
                reasoning=r.reasoning or "Evaluated verdict"
            )
        )

    # Reconstruct ScanSummary
    exec_results: List[TestExecutionResult] = []
    for r in db_results:
        exec_results.append(
            TestExecutionResult(
                test_case=TestCase(
                    id=r.test_id,
                    name=r.test_name,
                    category=AttackCategory(r.category) if r.category in [c.value for c in AttackCategory] else AttackCategory.DIRECT_PROMPT_INJECTION,
                    description=r.test_name,
                    payload="Synthetic attack payload",
                    severity=SeverityLevel(r.severity.upper()) if r.severity.upper() in [s.value for s in SeverityLevel] else SeverityLevel.MEDIUM,
                    expected_behavior="Secure baseline response",
                    vulnerable_behavior="Security boundary violation"
                ),
                status_code=200 if r.status != "ERROR" else 500,
                answer="Observed response",
                latency_ms=r.latency_ms,
                is_success=(r.status != "ERROR")
            )
        )

    duration = 0.0
    if scan.completed_at and scan.started_at:
        duration = round((scan.completed_at - scan.started_at).total_seconds(), 2)

    summary = ScanSummary(
        scan_id=scan.id,
        target_name=target_name,
        target_url=target_url,
        status=ScanStatus(scan.status) if scan.status in [s.value for s in ScanStatus] else ScanStatus.COMPLETED,
        total_tests=scan.total_tests,
        successful_executions=scan.successful_calls,
        failed_executions=scan.failed_calls,
        duration_seconds=duration,
        started_at=scan.started_at or scan.created_at,
        completed_at=scan.completed_at,
        results=exec_results
    )

    crit = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
    high = sum(1 for f in findings if f.severity == SeverityLevel.HIGH)
    med = sum(1 for f in findings if f.severity == SeverityLevel.MEDIUM)
    low = sum(1 for f in findings if f.severity == SeverityLevel.LOW)

    risk_profile = {
        "overall_posture": scan.overall_posture or "SECURE",
        "max_risk_score": scan.max_risk_score,
        "total_findings": len(findings),
        "critical_count": crit,
        "high_count": high,
        "medium_count": med,
        "low_count": low
    }

    return build_security_report(
        summary=summary,
        evaluations=evaluations,
        findings=findings,
        risk_profile=risk_profile
    )


@router.get("/{scan_id}/json")
async def get_json_report(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generates and returns the standardized JSON security audit report."""
    return await _assemble_report_data(scan_id, db)


@router.get("/{scan_id}/pdf")
async def get_pdf_report(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates and streams the publication-quality executive PDF report."""
    report_data = await _assemble_report_data(scan_id, db)
    pdf_bytes = generate_pdf_report(report_data)

    short_id = scan_id[:8]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="RAGShield_Report_{short_id}.pdf"'
        }
    )


@router.get("/compare", response_model=ScanComparisonResult)
async def compare_two_scans(
    base_scan_id: str = Query(..., description="ID of baseline reference scan"),
    remediation_scan_id: str = Query(..., description="ID of follow-up retest scan"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compares baseline and remediation scans to compute regression differential."""
    scan_repo = ScanRepository(db)
    base_scan = await scan_repo.get(base_scan_id)
    rem_scan = await scan_repo.get(remediation_scan_id)

    if not base_scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline scan '{base_scan_id}' not found."
        )
    if not rem_scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Remediation scan '{remediation_scan_id}' not found."
        )

    target_repo = TargetRepository(db)
    target = await target_repo.get(base_scan.target_id)
    target_name = target.name if target else "Target RAG System"

    finding_repo = FindingRepository(db)
    db_base_findings = await finding_repo.get_by_scan_run(base_scan_id)
    db_rem_findings = await finding_repo.get_by_scan_run(remediation_scan_id)

    def _to_finding_models(db_items):
        res = []
        for f in db_items:
            res.append(
                VulnerabilityFinding(
                    finding_id=f.finding_id,
                    fingerprint=f.fingerprint,
                    title=f.title,
                    category=AttackCategory(f.category) if f.category in [c.value for c in AttackCategory] else AttackCategory.DIRECT_PROMPT_INJECTION,
                    owasp_category=OWASPCategory(f.owasp_category) if f.owasp_category in [o.value for o in OWASPCategory] else None,
                    severity=SeverityLevel(f.severity.upper()) if f.severity.upper() in [s.value for s in SeverityLevel] else SeverityLevel.MEDIUM,
                    confidence=ConfidenceLevel(f.confidence.upper()) if f.confidence.upper() in [c.value for c in ConfidenceLevel] else ConfidenceLevel.HIGH,
                    risk_score=f.risk_score,
                    description=f.description,
                    affected_target=target_name,
                    evidence_count=f.evidence_count,
                    remediation_summary=f.remediation_summary,
                    created_at=f.created_at
                )
            )
        return res

    base_findings = _to_finding_models(db_base_findings)
    rem_findings = _to_finding_models(db_rem_findings)

    base_posture = {
        "overall_posture": base_scan.overall_posture or "UNKNOWN",
        "max_risk_score": base_scan.max_risk_score
    }
    rem_posture = {
        "overall_posture": rem_scan.overall_posture or "UNKNOWN",
        "max_risk_score": rem_scan.max_risk_score
    }

    return compare_scans(
        baseline_scan_id=base_scan_id,
        baseline_posture=base_posture,
        baseline_findings=base_findings,
        remediation_scan_id=remediation_scan_id,
        remediation_posture=rem_posture,
        remediation_findings=rem_findings,
        target_name=target_name
    )
