"""Scan Comparison and Vulnerability Regression Diffing Engine for RAGShield.

Enables DevSecOps teams to compare a Baseline scan against a Remediation scan
to deterministically track fixed vulnerabilities, recurring defects, and newly
introduced security regressions.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from engine.scoring.models import VulnerabilityFinding


class FindingDiffStatus(str, Enum):
    """Classification of a vulnerability status when comparing two scans."""
    FIXED = "FIXED"           # Present in baseline, absent in remediation scan
    RECURRING = "RECURRING"   # Present in both baseline and remediation scan
    NEW = "NEW"               # Absent in baseline, present in remediation scan


class FindingDiffItem(BaseModel):
    """Detailed differential state of a single vulnerability finding."""
    fingerprint: str = Field(..., description="Deterministic vulnerability fingerprint")
    status: FindingDiffStatus = Field(..., description="Differential state: FIXED, RECURRING, or NEW")
    title: str = Field(..., description="Vulnerability title")
    severity: str = Field(..., description="Severity level")
    category: str = Field(..., description="Attack category")
    owasp_category: Optional[str] = Field(None, description="OWASP classification")
    baseline_risk_score: Optional[float] = Field(None, description="Risk score in baseline scan")
    remediation_risk_score: Optional[float] = Field(None, description="Risk score in remediation scan")
    risk_score_delta: float = Field(0.0, description="Change in risk score (negative indicates risk reduction)")
    remediation_summary: Optional[str] = Field(None, description="Recommended remediation guidance")


class ScanComparisonResult(BaseModel):
    """Comprehensive regression diff report comparing two scans."""
    comparison_id: str = Field(default_factory=lambda: f"DIFF-{uuid.uuid4().hex[:8].upper()}")
    target_name: str
    baseline_scan_id: str
    remediation_scan_id: str
    compared_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Quantitative Delta
    baseline_posture: str
    remediation_posture: str
    posture_transition: str
    baseline_max_risk: float
    remediation_max_risk: float
    max_risk_delta: float = Field(..., description="Change in max risk score (remediation - baseline)")
    is_risk_reduced: bool = Field(..., description="True if max risk score decreased or vulnerabilities were eliminated")

    # Counts
    fixed_count: int
    recurring_count: int
    new_count: int
    total_findings_delta: int = Field(..., description="Net change in total vulnerability findings")

    # Detailed Categorized Findings
    fixed_findings: List[FindingDiffItem] = Field(default_factory=list)
    recurring_findings: List[FindingDiffItem] = Field(default_factory=list)
    new_findings: List[FindingDiffItem] = Field(default_factory=list)


def compare_scans(
    baseline_scan_id: str,
    baseline_posture: Dict[str, Any],
    baseline_findings: List[VulnerabilityFinding],
    remediation_scan_id: str,
    remediation_posture: Dict[str, Any],
    remediation_findings: List[VulnerabilityFinding],
    target_name: str = "Target RAG System"
) -> ScanComparisonResult:
    """Compares baseline and remediation scans to compute regression differential.
    
    Uses deterministic finding fingerprints to identify which defects were resolved,
    which defects persist, and whether any new vulnerabilities emerged.
    
    Args:
        baseline_scan_id: Identifier of the earlier / reference scan.
        baseline_posture: Dict containing overall_posture and max_risk_score of baseline.
        baseline_findings: List of VulnerabilityFinding objects from baseline.
        remediation_scan_id: Identifier of the follow-up / retested scan.
        remediation_posture: Dict containing overall_posture and max_risk_score of remediation scan.
        remediation_findings: List of VulnerabilityFinding objects from remediation scan.
        target_name: Name of evaluated target.
        
    Returns:
        ScanComparisonResult with categorized diff items and quantitative deltas.
    """
    base_map: Dict[str, VulnerabilityFinding] = {f.fingerprint: f for f in baseline_findings}
    rem_map: Dict[str, VulnerabilityFinding] = {f.fingerprint: f for f in remediation_findings}

    all_fingerprints = set(base_map.keys()).union(set(rem_map.keys()))

    fixed_items: List[FindingDiffItem] = []
    recurring_items: List[FindingDiffItem] = []
    new_items: List[FindingDiffItem] = []

    for fp in all_fingerprints:
        in_base = fp in base_map
        in_rem = fp in rem_map

        if in_base and not in_rem:
            # FIXED: Was present in baseline, eliminated in remediation
            f = base_map[fp]
            fixed_items.append(
                FindingDiffItem(
                    fingerprint=fp,
                    status=FindingDiffStatus.FIXED,
                    title=f.title,
                    severity=f.severity.value,
                    category=f.category.value,
                    owasp_category=f.owasp_category.value if f.owasp_category else None,
                    baseline_risk_score=f.risk_score,
                    remediation_risk_score=None,
                    risk_score_delta=-f.risk_score,
                    remediation_summary=f.remediation_summary
                )
            )
        elif in_base and in_rem:
            # RECURRING: Defect still present in both scans
            f_base = base_map[fp]
            f_rem = rem_map[fp]
            delta = round(f_rem.risk_score - f_base.risk_score, 1)
            recurring_items.append(
                FindingDiffItem(
                    fingerprint=fp,
                    status=FindingDiffStatus.RECURRING,
                    title=f_rem.title,
                    severity=f_rem.severity.value,
                    category=f_rem.category.value,
                    owasp_category=f_rem.owasp_category.value if f_rem.owasp_category else None,
                    baseline_risk_score=f_base.risk_score,
                    remediation_risk_score=f_rem.risk_score,
                    risk_score_delta=delta,
                    remediation_summary=f_rem.remediation_summary
                )
            )
        elif not in_base and in_rem:
            # NEW: Regression introduced in remediation scan
            f = rem_map[fp]
            new_items.append(
                FindingDiffItem(
                    fingerprint=fp,
                    status=FindingDiffStatus.NEW,
                    title=f.title,
                    severity=f.severity.value,
                    category=f.category.value,
                    owasp_category=f.owasp_category.value if f.owasp_category else None,
                    baseline_risk_score=None,
                    remediation_risk_score=f.risk_score,
                    risk_score_delta=f.risk_score,
                    remediation_summary=f.remediation_summary
                )
            )

    # Sort each list by highest severity / risk first
    fixed_items.sort(key=lambda x: x.baseline_risk_score or 0.0, reverse=True)
    recurring_items.sort(key=lambda x: x.remediation_risk_score or 0.0, reverse=True)
    new_items.sort(key=lambda x: x.remediation_risk_score or 0.0, reverse=True)

    base_max = baseline_posture.get("max_risk_score", 0.0)
    rem_max = remediation_posture.get("max_risk_score", 0.0)
    max_risk_delta = round(rem_max - base_max, 1)

    base_pos = baseline_posture.get("overall_posture", "UNKNOWN")
    rem_pos = remediation_posture.get("overall_posture", "UNKNOWN")

    is_reduced = (max_risk_delta < 0) or (len(fixed_items) > 0 and len(new_items) == 0 and max_risk_delta <= 0)

    return ScanComparisonResult(
        target_name=target_name,
        baseline_scan_id=baseline_scan_id,
        remediation_scan_id=remediation_scan_id,
        baseline_posture=base_pos,
        remediation_posture=rem_pos,
        posture_transition=f"{base_pos} ➔ {rem_pos}",
        baseline_max_risk=base_max,
        remediation_max_risk=rem_max,
        max_risk_delta=max_risk_delta,
        is_risk_reduced=is_reduced,
        fixed_count=len(fixed_items),
        recurring_count=len(recurring_items),
        new_count=len(new_items),
        total_findings_delta=len(remediation_findings) - len(baseline_findings),
        fixed_findings=fixed_items,
        recurring_findings=recurring_items,
        new_findings=new_items,
    )
