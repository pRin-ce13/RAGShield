"""Pydantic Request and Response Schemas for Findings and Test Results."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TestResultResponse(BaseModel):
    """Execution and evaluation result for a single test case."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    scan_run_id: str
    test_id: str
    test_name: str
    category: str
    owasp_category: Optional[str] = None
    severity: str
    status: str
    confidence: str
    evaluator_name: str
    evidence: Optional[str] = None
    reasoning: str
    target_role: Optional[str] = None
    latency_ms: float
    executed_at: datetime


class FindingResponse(BaseModel):
    """Deduplicated vulnerability finding with evidence instances and remediation playbooks."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    scan_run_id: str
    finding_id: str
    fingerprint: str
    title: str
    category: str
    owasp_category: Optional[str] = None
    severity: str
    confidence: str
    risk_score: float
    description: str
    affected_target: str
    evidence_count: int
    evidence_instances: List[Dict[str, Any]] = Field(default_factory=list)
    remediation_summary: str
    remediation_steps: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    created_at: datetime


class RiskProfileResponse(BaseModel):
    """Overall posture rating and risk score breakdown for a scan."""
    total_findings: int
    overall_posture: str
    max_risk_score: float
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
