"""Scan Run and Lifecycle Execution Model for RAGShield."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.session import Base


class ScanStatus:
    """Execution status for a scan run."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ScanRun(Base):
    """Execution instance of a security assessment against a Target."""
    __tablename__ = "scan_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    target_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("targets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    triggered_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=ScanStatus.PENDING,
        nullable=False,
        index=True
    )

    # Risk & Posture Outcomes
    overall_posture: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    max_risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    # Execution Progress & Metrics
    total_tests: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    completed_tests: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    successful_calls: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    failed_calls: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Filters & Config Snapshots
    categories_filter_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    severities_filter_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    target = relationship("Target", back_populates="scan_runs", lazy="selectin")
    triggered_by = relationship("User", back_populates="scan_runs", lazy="selectin")
    test_results = relationship(
        "TestResultRecord",
        back_populates="scan_run",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    findings = relationship(
        "VulnerabilityFindingRecord",
        back_populates="scan_run",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
