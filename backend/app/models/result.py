"""Individual Test Execution Evaluation Result Model for RAGShield."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.session import Base


class TestResultRecord(Base):
    """Database record for an individual security test evaluation outcome."""
    __tablename__ = "test_results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    scan_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("scan_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    test_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    test_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    owasp_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    # Outcome
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # PASS, FAIL, INCONCLUSIVE, ERROR
    confidence: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # CONFIRMED, HIGH, MEDIUM, LOW
    evaluator_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Forensic Traceability
    evidence: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    reasoning: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    target_role: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    latency_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    scan_run = relationship("ScanRun", back_populates="test_results", lazy="selectin")
