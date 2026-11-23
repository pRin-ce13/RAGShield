"""User and Role-Based Authorization Model for RAGShield."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.session import Base


class UserRole:
    """Standard RBAC roles for RAGShield platform."""
    ADMIN = "admin"        # Full control: system config, user management, scans, targets
    ANALYST = "analyst"    # Security engineer: configure targets, run scans, triage findings
    VIEWER = "viewer"      # Read-only stakeholder: view scan summaries, reports, dashboards


class User(Base):
    """Platform user account with role-based access permissions."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default=UserRole.ANALYST,
        nullable=False
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
    scan_runs = relationship("ScanRun", back_populates="triggered_by", lazy="selectin")
