"""Vulnerability Finding and Risk Assessment Models for RAGShield.

Calculates CVSS-aligned quantitative risk scores (0.0 - 10.0) and formalizes
deduplicated vulnerability findings with traceable evidence and remediation steps.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from engine.attacks.categories import AttackCategory, OWASPCategory, SeverityLevel
from engine.evaluators.models import ConfidenceLevel


# Deterministic CVSS-Aligned Risk Scoring Weights
SEVERITY_BASE_SCORES: Dict[SeverityLevel, float] = {
    SeverityLevel.CRITICAL: 9.5,
    SeverityLevel.HIGH: 7.5,
    SeverityLevel.MEDIUM: 5.0,
    SeverityLevel.LOW: 2.5,
    SeverityLevel.INFO: 0.5,
}

CONFIDENCE_MULTIPLIERS: Dict[ConfidenceLevel, float] = {
    ConfidenceLevel.CONFIRMED: 1.0,
    ConfidenceLevel.HIGH: 0.9,
    ConfidenceLevel.MEDIUM: 0.7,
    ConfidenceLevel.LOW: 0.4,
}


def calculate_risk_score(severity: SeverityLevel, confidence: ConfidenceLevel) -> float:
    """Calculates a normalized 0.0 to 10.0 risk score combining severity and confidence.
    
    Formula: Risk Score = Severity Base Score * Confidence Multiplier
    
    Example:
        - CRITICAL (9.5) with CONFIRMED (1.0) = 9.5
        - CRITICAL (9.5) with LOW (0.4)       = 3.8
    """
    base = SEVERITY_BASE_SCORES.get(severity, 5.0)
    mult = CONFIDENCE_MULTIPLIERS.get(confidence, 0.7)
    return round(base * mult, 1)


def generate_finding_id() -> str:
    """Generates a standardized security finding identifier."""
    return f"FIND-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:6].upper()}"


class EvidenceInstance(BaseModel):
    """An individual test occurrence contributing evidence to a deduplicated finding."""
    test_id: str = Field(..., description="Test case ID that triggered this finding")
    test_name: str = Field(..., description="Title of the test case")
    payload: str = Field(..., description="Attack payload sent to the target")
    evidence_snippet: str = Field(..., description="Concrete leaked string, file, or pattern matched")
    target_role: Optional[str] = Field(None, description="User role under which this occurred")
    latency_ms: float = Field(0.0, description="Response time in milliseconds")


class VulnerabilityFinding(BaseModel):
    """A prioritized, actionable vulnerability defect identified during an assessment."""
    finding_id: str = Field(default_factory=generate_finding_id)
    fingerprint: str = Field(..., description="Deterministic hash used for deduplication")
    title: str = Field(..., description="Concise, professional vulnerability headline")
    category: AttackCategory = Field(..., description="Vulnerability category")
    owasp_category: OWASPCategory = Field(..., description="Primary OWASP LLM Top 10 classification")
    severity: SeverityLevel = Field(..., description="CVSS-aligned severity rating")
    confidence: ConfidenceLevel = Field(..., description="Algorithmic certainty level")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Quantitative risk score (0.0 to 10.0)")
    
    description: str = Field(..., description="Technical explanation of the vulnerability and impact")
    affected_target: str = Field(..., description="Name or URL of the affected RAG system")
    
    # Supporting Evidence
    evidence_count: int = Field(..., description="Number of test occurrences supporting this finding")
    evidence_instances: List[EvidenceInstance] = Field(default_factory=list, description="All captured evidence items")
    
    # Actionable Remediation Guidance
    remediation_summary: str = Field(..., description="High-level engineering remediation recommendation")
    remediation_steps: List[str] = Field(default_factory=list, description="Step-by-step technical implementation instructions")
    references: List[str] = Field(default_factory=list, description="External security references and OWASP links")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
