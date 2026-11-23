"""Scan Orchestration Service and Background Execution Engine for RAGShield."""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.database.session import AsyncSessionLocal
from backend.app.models.scan import ScanRun, ScanStatus
from backend.app.models.target import Target
from backend.app.repositories.finding_repo import FindingRepository
from backend.app.repositories.scan_repo import ScanRepository
from backend.app.repositories.target_repo import TargetRepository
from backend.app.schemas.scan import ScanLaunchRequest
from engine.attacks.categories import AttackCategory, SeverityLevel
from engine.evaluators import EvaluationPipeline
from engine.orchestrator import ScanConfig, ScanOrchestrator, ScanProgress
from engine.scoring import FindingsManager

logger = logging.getLogger(__name__)


class ScanService:
    """Manages the full assessment lifecycle from API triggering to background evaluation and persistence."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    async def launch_scan(
        self,
        target_id: str,
        triggered_by_id: Optional[str],
        request: ScanLaunchRequest
    ) -> ScanRun:
        """Initializes a scan run in the DB and launches non-blocking background execution."""
        if not self.session:
            raise RuntimeError("Database session required for launch_scan")

        target_repo = TargetRepository(self.session)
        target = await target_repo.get(target_id)
        if not target:
            raise ValueError(f"Target with ID '{target_id}' not found.")
        if not target.is_active:
            raise ValueError(f"Target '{target.name}' is currently marked inactive.")

        scan_repo = ScanRepository(self.session)
        scan = await scan_repo.create_scan_run(
            target_id=target.id,
            triggered_by_id=triggered_by_id,
            total_tests=0,
            categories=request.categories,
            severities=request.severities
        )
        await self.session.commit()

        # Launch background async task with isolated DB session
        asyncio.create_task(
            self._execute_scan_background(
                scan_id=scan.id,
                target=target,
                request=request
            )
        )

        return scan

    async def _execute_scan_background(
        self,
        scan_id: str,
        target: Target,
        request: ScanLaunchRequest
    ) -> None:
        """Asynchronous worker executing the security test suite in the background."""
        logger.info(f"Starting background scan execution for Scan ID: {scan_id}")
        
        # Open dedicated async session for the lifetime of this background task
        async with AsyncSessionLocal() as bg_session:
            scan_repo = ScanRepository(bg_session)
            finding_repo = FindingRepository(bg_session)

            try:
                # 1. Parse categories and severities filters
                cat_filters = (
                    [AttackCategory(c) for c in request.categories]
                    if request.categories else None
                )
                sev_filters = (
                    [SeverityLevel(s.upper()) for s in request.severities]
                    if request.severities else None
                )

                custom_headers = json.loads(target.custom_headers_json or "{}")
                request_mapping = json.loads(target.request_mapping_json or "{}")
                response_mapping = json.loads(target.response_mapping_json or "{}")

                # 2. Build Engine ScanConfig
                config = ScanConfig(
                    target_name=target.name,
                    target_url=target.target_url,
                    api_key=target.api_key,
                    custom_headers=custom_headers,
                    request_mapping=request_mapping,
                    response_mapping=response_mapping,
                    allow_local=settings.ALLOW_LOCAL_TARGETS,
                    categories=cat_filters,
                    severities=sev_filters,
                    max_concurrency=request.max_concurrency or settings.DEFAULT_MAX_CONCURRENCY,
                    timeout_seconds=request.timeout_seconds or settings.DEFAULT_TIMEOUT_SECONDS
                )

                orchestrator = ScanOrchestrator(config=config)
                await scan_repo.mark_running(scan_id, total_tests=0)
                await bg_session.commit()

                # Progress callback tracking live execution
                def on_progress(p: ScanProgress):
                    # Progress is tracked; DB update done periodically or at milestones
                    pass

                # 3. Execute probe execution suite
                summary = await orchestrator.run_scan(on_progress=on_progress)

                if summary.error:
                    logger.error(f"Scan {scan_id} pre-flight or execution error: {summary.error}")
                    await scan_repo.complete_scan(
                        scan_id=scan_id,
                        status=ScanStatus.FAILED,
                        error_message=summary.error
                    )
                    await bg_session.commit()
                    return

                # Update progress counts
                await scan_repo.update_progress(
                    scan_id=scan_id,
                    completed_tests=summary.completed_tests,
                    successful_calls=summary.successful_executions,
                    failed_calls=summary.failed_executions
                )

                # 4. Evaluate scan execution results via EvaluationPipeline
                pipeline = EvaluationPipeline()
                evaluations = pipeline.evaluate_all(summary.results)

                # 5. Deduplicate and score findings via FindingsManager
                findings_mgr = FindingsManager()
                findings = findings_mgr.generate_findings(evaluations, target_name=target.name)
                risk_profile = findings_mgr.get_risk_profile(findings)

                # 6. Bulk persist evaluation results & deduplicated findings
                await finding_repo.bulk_create_results(scan_id, evaluations)
                await finding_repo.bulk_create_findings(scan_id, findings)

                # 7. Finalize scan run
                await scan_repo.complete_scan(
                    scan_id=scan_id,
                    status=ScanStatus.COMPLETED,
                    overall_posture=risk_profile["overall_posture"],
                    max_risk_score=risk_profile["max_risk_score"]
                )
                await bg_session.commit()
                logger.info(
                    f"Scan {scan_id} successfully completed. "
                    f"Posture: {risk_profile['overall_posture']} (Risk: {risk_profile['max_risk_score']})"
                )

            except Exception as exc:
                logger.exception(f"Unhandled error during background scan {scan_id}: {exc}")
                await scan_repo.complete_scan(
                    scan_id=scan_id,
                    status=ScanStatus.FAILED,
                    error_message=str(exc)
                )
                await bg_session.commit()
