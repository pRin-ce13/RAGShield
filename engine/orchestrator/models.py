"""Data Models and State Enums for RAGShield Scan Orchestration.

Encapsulates scan configurations, lifecycle states, individual test execution results,
and aggregate scan summaries.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

from engine.attacks.categories import AttackCategory, SeverityLevel
from engine.attacks.schema import TestCase


class ScanStatus(str, Enum):
    """Lifecycle states of a security scan."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


def generate_id(prefix: str = "scan") -> str:
    """Generates a unique prefixed identifier."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ScanConfig(BaseModel):
    """Configuration options governing the execution of a security scan."""
    scan_id: str = Field(default_factory=lambda: generate_id("scan"))
    target_name: str = Field("Demo RAG Target", description="Identifier for the target application")
    target_url: str = Field("http://127.0.0.1:8001", description="Base URL of the target RAG API")
    api_key: Optional[str] = Field(None, description="Optional target API key credential")
    allow_local: bool = Field(True, description="Whether to allow scanning loopback/private target IPs")
    
    # Test suite selection filters (if None, all are included)
    categories: Optional[List[AttackCategory]] = Field(None, description="Filter tests by vulnerability category")
    severities: Optional[List[SeverityLevel]] = Field(None, description="Filter tests by CVSS severity rating")
    test_ids: Optional[List[str]] = Field(None, description="Explicit whitelist of test IDs to run")
    tags: Optional[List[str]] = Field(None, description="Filter tests by keyword tag")

    # Execution controls
    max_concurrency: int = Field(3, ge=1, le=20, description="Max simultaneous requests sent to the target")
    request_delay_seconds: float = Field(0.0, ge=0.0, le=5.0, description="Rate limit delay between requests")
    timeout_seconds: float = Field(10.0, ge=1.0, le=60.0, description="Request timeout in seconds")


class TestExecutionResult(BaseModel):
    """Raw execution result capturing target response and network telemetry for a single test."""
    execution_id: str = Field(default_factory=lambda: generate_id("exec"))
    test_case: TestCase = Field(..., description="The test case executed")
    status_code: int = Field(..., description="HTTP status code returned by target")
    answer: str = Field(..., description="Observed text answer from target")
    sources: List[str] = Field(default_factory=list, description="Observed document source citations")
    latency_ms: float = Field(..., description="Network round-trip response time in milliseconds")
    raw_response: Dict[str, Any] = Field(default_factory=dict, description="Full raw JSON response from target")
    error: Optional[str] = Field(None, description="Error message if network communication failed")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_success: bool = Field(..., description="True if target returned 2xx response without transport error")


class ScanProgress(BaseModel):
    """Real-time progress telemetry emitted during scan execution."""
    scan_id: str
    total_tests: int
    completed_tests: int
    successful_tests: int
    failed_tests: int
    percentage: float
    current_test_id: Optional[str] = None


class ScanSummary(BaseModel):
    """Complete summary of an executed scan containing all raw results and timings."""
    scan_id: str
    target_name: str
    target_url: str
    status: ScanStatus
    total_tests: int
    successful_executions: int
    failed_executions: int
    duration_seconds: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: List[TestExecutionResult] = Field(default_factory=list)
    error: Optional[str] = None
