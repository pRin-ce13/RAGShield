"""Pydantic Request and Response Schemas for Scan Runs and Lifecycle Telemetry."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScanLaunchRequest(BaseModel):
    """Payload to trigger an automated security scan against a registered target."""
    target_id: str = Field(..., description="UUID of the Target RAG to assess")
    categories: Optional[List[str]] = Field(None, description="Optional category filters (e.g. direct_prompt_injection)")
    severities: Optional[List[str]] = Field(None, description="Optional severity filters (e.g. CRITICAL, HIGH)")
    max_concurrency: Optional[int] = Field(3, ge=1, le=10, description="Max concurrent HTTP probes")
    timeout_seconds: Optional[float] = Field(15.0, ge=1.0, le=60.0, description="Per-probe timeout in seconds")


class ScanProgressResponse(BaseModel):
    """Real-time scan execution telemetry."""
    scan_id: str
    status: str
    percentage: float
    completed_tests: int
    total_tests: int
    current_test_id: Optional[str] = None


class ScanResponse(BaseModel):
    """Public Scan Run record response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    target_id: str
    triggered_by_id: Optional[str] = None
    status: str
    overall_posture: Optional[str] = None
    max_risk_score: float = 0.0
    total_tests: int
    completed_tests: int
    successful_calls: int
    failed_calls: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
