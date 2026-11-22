"""Evaluation Models and Outcome Enums for RAGShield.

Strictly separates TestStatus (PASS/FAIL), ConfidenceLevel (Certainty), and SeverityLevel (Risk),
ensuring zero false alarms and complete evidence traceability.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from engine.attacks.categories import AttackCategory, OWASPCategory, SeverityLevel


class TestStatus(str, Enum):
    """The security outcome of evaluating a target response."""
    PASS = "PASS"                  # Handled safely, security policy adhered to
    FAIL = "FAIL"                  # Vulnerability detected (leak, bypass, or RBAC breach)
    INCONCLUSIVE = "INCONCLUSIVE"  # Ambiguous outcome requiring secondary or manual review
    ERROR = "ERROR"                # Target communication failed or returned HTTP 5xx


class ConfidenceLevel(str, Enum):
    """Degree of certainty in the evaluation result."""
    CONFIRMED = "CONFIRMED"  # Mathematical proof (e.g. exact token match, source citation)
    HIGH = "HIGH"            # Strong pattern match or clear refusal
    MEDIUM = "MEDIUM"        # Heuristic or partial match
    LOW = "LOW"              # Weak heuristic or uncertain assertion


def generate_eval_id() -> str:
    """Generates a unique identifier for an evaluation outcome."""
    return f"eval_{uuid.uuid4().hex[:12]}"


class EvaluationResult(BaseModel):
    """Standardized result produced by evaluating a single test execution."""
    evaluation_id: str = Field(default_factory=generate_eval_id)
    test_id: str = Field(..., description="ID of the executed test case")
    test_name: str = Field(..., description="Title of the test case")
    category: AttackCategory = Field(..., description="Vulnerability category")
    owasp_category: Optional[OWASPCategory] = Field(None, description="Mapped OWASP LLM Top 10 category")
    severity: SeverityLevel = Field(..., description="CVSS-aligned risk severity rating if vulnerable")
    
    # Core Verdict
    status: TestStatus = Field(..., description="Verdict: PASS (secure) vs FAIL (vulnerable)")
    confidence: ConfidenceLevel = Field(..., description="Certainty level of this verdict")
    evaluator_name: str = Field(..., description="Algorithm or class responsible for the verdict")
    
    # Traceable Evidence & Reasoning
    evidence: Optional[str] = Field(None, description="Concrete snippet, secret token, or file cited as proof")
    reasoning: str = Field(..., description="Clear human explanation of why the test passed or failed")
    
    # Metadata
    target_role: Optional[str] = Field(None, description="Simulated user access role")
    response_latency_ms: float = Field(0.0, description="Target round-trip latency in milliseconds")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_vulnerable(self) -> bool:
        """Returns True if a security failure has been confirmed."""
        return self.status == TestStatus.FAIL
