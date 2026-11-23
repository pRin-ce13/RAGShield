"""Target RAG Application Configuration Model for RAGShield."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.session import Base


class Target(Base):
    """Configuration record for a target RAG system subjected to security evaluations."""
    __tablename__ = "targets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    target_url: Mapped[str] = mapped_column(
        String(1024),
        nullable=False
    )
    api_key: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True
    )
    custom_headers_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default="{}"
    )
    request_mapping_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default="{}"
    )
    response_mapping_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default="{}"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    scan_runs = relationship(
        "ScanRun",
        back_populates="target",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
