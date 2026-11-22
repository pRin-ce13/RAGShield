"""RAGShield Findings, Severity Scoring, and Risk Assessment Module."""

from .models import (
    ConfidenceLevel,
    EvidenceInstance,
    SEVERITY_BASE_SCORES,
    CONFIDENCE_MULTIPLIERS,
    VulnerabilityFinding,
    calculate_risk_score,
    generate_finding_id,
)
from .remediation import (
    RemediationPlaybook,
    REMEDIATION_CATALOG,
    get_remediation_for_category,
)
from .manager import (
    FindingsManager,
    compute_fingerprint,
)

__all__ = [
    "ConfidenceLevel",
    "EvidenceInstance",
    "SEVERITY_BASE_SCORES",
    "CONFIDENCE_MULTIPLIERS",
    "VulnerabilityFinding",
    "calculate_risk_score",
    "generate_finding_id",
    "RemediationPlaybook",
    "REMEDIATION_CATALOG",
    "get_remediation_for_category",
    "FindingsManager",
    "compute_fingerprint",
]
