"""Scan Repository for Managing Assessment Lifecycles."""

from datetime import datetime, timezone
import json
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.scan import ScanRun, ScanStatus
from backend.app.repositories.base import BaseRepository


class ScanRepository(BaseRepository[ScanRun]):
    """Data access layer for ScanRun lifecycle records."""

    def __init__(self, session: AsyncSession):
        super().__init__(ScanRun, session)

    async def create_scan_run(
        self,
        target_id: str,
        triggered_by_id: Optional[str] = None,
        total_tests: int = 0,
        categories: Optional[List[str]] = None,
        severities: Optional[List[str]] = None
    ) -> ScanRun:
        """Initializes a new pending scan run."""
        scan = ScanRun(
            target_id=target_id,
            triggered_by_id=triggered_by_id,
            status=ScanStatus.PENDING,
            total_tests=total_tests,
            categories_filter_json=json.dumps(categories) if categories else None,
            severities_filter_json=json.dumps(severities) if severities else None
        )
        return await self.create(scan)

    async def mark_running(self, scan_id: str, total_tests: int) -> Optional[ScanRun]:
        """Transitions scan to RUNNING status."""
        scan = await self.get(scan_id)
        if scan:
            scan.status = ScanStatus.RUNNING
            scan.total_tests = total_tests
            scan.started_at = datetime.now(timezone.utc)
            await self.session.flush()
        return scan

    async def update_progress(
        self,
        scan_id: str,
        completed_tests: int,
        successful_calls: int,
        failed_calls: int
    ) -> None:
        """Updates live execution progress metrics."""
        scan = await self.get(scan_id)
        if scan:
            scan.completed_tests = completed_tests
            scan.successful_calls = successful_calls
            scan.failed_calls = failed_calls
            await self.session.flush()

    async def complete_scan(
        self,
        scan_id: str,
        status: str,
        overall_posture: Optional[str] = None,
        max_risk_score: float = 0.0,
        error_message: Optional[str] = None
    ) -> Optional[ScanRun]:
        """Finalizes scan execution and persists summary security verdicts."""
        scan = await self.get(scan_id)
        if scan:
            scan.status = status
            scan.overall_posture = overall_posture
            scan.max_risk_score = max_risk_score
            scan.error_message = error_message
            scan.completed_at = datetime.now(timezone.utc)
            await self.session.flush()
        return scan

    async def get_by_target(self, target_id: str, skip: int = 0, limit: int = 50) -> List[ScanRun]:
        """Fetches scan history for a specific target."""
        result = await self.session.execute(
            select(ScanRun)
            .where(ScanRun.target_id == target_id)
            .order_by(ScanRun.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
