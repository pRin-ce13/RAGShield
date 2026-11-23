"""Vulnerability Finding and Remediation Persistence Model for RAGShield."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.session import Base


class VulnerabilityFindingRecord(Base):
    """Database record for a deduplicated security defect with remediation guidance."""
    __tablename__ = "findings"

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
    finding_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # e.g., FIND-2026-A1B2C3
    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
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
        nullable=False,
        index=True
    )
    confidence: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )

    # Technical Details
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    affected_target: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    evidence_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    evidence_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]"
    )

    # Remediation Guidance
    remediation_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    remediation_steps_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]"
    )
    references_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    scan_run = relationship("ScanRun", back_populates="findings", lazy="selectin")
