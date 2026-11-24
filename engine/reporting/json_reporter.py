"""Standardized JSON Security Audit Report Generator for RAGShield.

Transforms raw scan metrics, evaluations, deduplicated findings, and remediation
guidance into an enterprise-ready, machine-readable security assessment report.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from engine.attacks.categories import OWASPCategory
from engine.evaluators.models import EvaluationResult, TestStatus
from engine.orchestrator.models import ScanSummary
from engine.scoring.models import VulnerabilityFinding


REPORT_SCHEMA_VERSION = "1.0.0"


def _build_owasp_coverage_matrix(
    evaluations: List[EvaluationResult]
) -> Dict[str, Dict[str, Any]]:
    """Calculates coverage and pass/fail posture for OWASP LLM Top 10 categories."""
    matrix: Dict[str, Dict[str, Any]] = {}

    for ev in evaluations:
        owasp_key = ev.owasp_category.value if ev.owasp_category else "OWASP-LLM: Unmapped"
        if owasp_key not in matrix:
            matrix[owasp_key] = {
                "category": owasp_key,
                "total_probes": 0,
                "passed_probes": 0,
                "failed_probes": 0,
                "compliance_status": "COMPLIANT",
            }

        matrix[owasp_key]["total_probes"] += 1
        if ev.status == TestStatus.PASS:
            matrix[owasp_key]["passed_probes"] += 1
        else:
            matrix[owasp_key]["failed_probes"] += 1
            matrix[owasp_key]["compliance_status"] = "DEFICIENT"

    return matrix


def build_security_report(
    summary: ScanSummary,
    evaluations: List[EvaluationResult],
    findings: List[VulnerabilityFinding],
    risk_profile: Dict[str, Any],
    scanner_version: str = "0.10.0"
) -> Dict[str, Any]:
    """Assembles a comprehensive, standardized security assessment report dictionary.
    
    Args:
        summary: Raw scan execution summary from the orchestrator.
        evaluations: Evaluated test results from the EvaluationPipeline.
        findings: Deduplicated root-cause vulnerabilities from FindingsManager.
        risk_profile: Aggregate quantitative risk scorecard.
        scanner_version: Version identifier of the RAGShield platform.
        
    Returns:
        Structured dictionary adhering to the RAGShield Audit Report Schema v1.0.
    """
    total_evals = len(evaluations)
    passed_count = sum(1 for e in evaluations if e.status == TestStatus.PASS)
    failed_count = sum(1 for e in evaluations if e.status == TestStatus.FAIL)
    error_count = sum(1 for e in evaluations if e.status == TestStatus.ERROR)

    latencies = [r.latency_ms for r in summary.results if r.latency_ms > 0]
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0
    max_latency = round(max(latencies), 1) if latencies else 0.0

    owasp_matrix = _build_owasp_coverage_matrix(evaluations)

    report: Dict[str, Any] = {
        "report_metadata": {
            "report_id": f"REP-{summary.scan_id}",
            "schema_version": REPORT_SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scanner": "RAGShield Security Platform",
            "scanner_version": scanner_version,
            "scan_id": summary.scan_id,
        },
        "target_information": {
            "target_name": summary.target_name,
            "target_url": summary.target_url,
            "scan_status": summary.status.value,
            "duration_seconds": summary.duration_seconds,
            "completed_tests": summary.total_tests,
        },
        "executive_summary": {
            "overall_posture": risk_profile.get("overall_posture", "UNKNOWN"),
            "max_risk_score": risk_profile.get("max_risk_score", 0.0),
            "risk_score_scale": "0.0 (Secure) to 10.0 (Critical Risk)",
            "total_vulnerabilities": risk_profile.get("total_findings", len(findings)),
            "severity_distribution": {
                "critical": risk_profile.get("critical_count", 0),
                "high": risk_profile.get("high_count", 0),
                "medium": risk_profile.get("medium_count", 0),
                "low": risk_profile.get("low_count", 0),
            },
            "test_verdict_summary": {
                "total_probes": total_evals,
                "passed_probes": passed_count,
                "vulnerable_probes": failed_count,
                "error_probes": error_count,
                "pass_rate_percentage": round((passed_count / total_evals) * 100, 1) if total_evals > 0 else 0.0,
            },
        },
        "owasp_compliance_matrix": list(owasp_matrix.values()),
        "vulnerability_findings": [
            {
                "finding_id": f.finding_id,
                "fingerprint": f.fingerprint,
                "title": f.title,
                "severity": f.severity.value,
                "confidence": f.confidence.value,
                "risk_score": f.risk_score,
                "category": f.category.value,
                "owasp_category": f.owasp_category.value if f.owasp_category else None,
                "description": f.description,
                "evidence_count": f.evidence_count,
                "evidence_instances": [ev.model_dump() for ev in f.evidence_instances],
                "remediation": {
                    "summary": f.remediation_summary,
                    "action_steps": f.remediation_steps,
                    "references": f.references,
                },
                "created_at": f.created_at.isoformat(),
            }
            for f in findings
        ],
        "telemetry_statistics": {
            "average_latency_ms": avg_latency,
            "max_latency_ms": max_latency,
            "successful_transport_calls": summary.successful_executions,
            "failed_transport_calls": summary.failed_executions,
        },
    }

    return report


def export_json_report(
    report_data: Dict[str, Any],
    output_path: Optional[Union[str, Path]] = None,
    indent: int = 2
) -> str:
    """Serializes security report dictionary to formatted JSON string and optionally writes to disk.
    
    Args:
        report_data: Dictionary generated by build_security_report().
        output_path: Optional file path to persist JSON report.
        indent: JSON indentation spaces for human readability.
        
    Returns:
        JSON string representation.
    """
    serialized = json.dumps(report_data, indent=indent, default=str)
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")
    return serialized
