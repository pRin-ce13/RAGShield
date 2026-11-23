"""Asynchronous Scan Orchestrator Engine for RAGShield.

Coordinates test selection, pre-flight target health checks, throttled concurrency,
execution telemetry, and cancellation handling.
"""

import asyncio
from datetime import datetime, timezone
import time
from typing import Any, Callable, Dict, List, Optional, Set

from engine.attacks.registry import AttackRegistry
from engine.attacks.schema import TestCase
from engine.targets.base import BaseTargetAdapter, TargetResponse
from engine.targets.http_adapter import HTTPTargetAdapter
from .models import (
    ScanConfig,
    ScanProgress,
    ScanStatus,
    ScanSummary,
    TestExecutionResult,
)

ProgressCallback = Callable[[ScanProgress], None]


class ScanOrchestrator:
    """Orchestrates and executes security scans against RAG targets."""

    def __init__(
        self,
        config: ScanConfig,
        registry: Optional[AttackRegistry] = None,
        target_adapter: Optional[BaseTargetAdapter] = None
    ):
        """Initializes the orchestrator.
        
        Args:
            config: Scan configuration parameters.
            registry: AttackRegistry instance (defaults to loading datasets/test_cases/v1).
            target_adapter: Pre-configured BaseTargetAdapter (defaults to HTTPTargetAdapter from config).
        """
        self.config = config
        self.registry = registry or AttackRegistry()
        
        # Instantiate HTTP adapter if not explicitly supplied
        if target_adapter is not None:
            self.target_adapter = target_adapter
        else:
            self.target_adapter = HTTPTargetAdapter(
                target_name=self.config.target_name,
                base_url=self.config.target_url,
                api_key=self.config.api_key,
                timeout_seconds=self.config.timeout_seconds,
                allow_local=self.config.allow_local
            )

        self.status = ScanStatus.PENDING
        self._cancel_event = asyncio.Event()
        self.results: List[TestExecutionResult] = []
        self._completed_count = 0
        self._successful_count = 0
        self._failed_count = 0

    def cancel(self) -> None:
        """Signals the orchestrator to abort execution immediately."""
        self._cancel_event.set()
        if self.status == ScanStatus.RUNNING:
            self.status = ScanStatus.CANCELLED

    def resolve_test_cases(self) -> List[TestCase]:
        """Filters test cases from the registry according to the scan configuration.
        
        Returns:
            Deduplicated list of TestCase objects selected for this scan.
        """
        all_tests = self.registry.list_all()
        selected: List[TestCase] = []

        for test in all_tests:
            # 1. Filter by explicit test ID whitelist if specified
            if self.config.test_ids is not None:
                if test.id not in self.config.test_ids:
                    continue

            # 2. Filter by Category
            if self.config.categories is not None:
                cat_values = [c.value if hasattr(c, "value") else str(c) for c in self.config.categories]
                if test.category.value not in cat_values:
                    continue

            # 3. Filter by Severity
            if self.config.severities is not None:
                sev_values = [s.value if hasattr(s, "value") else str(s) for s in self.config.severities]
                if test.severity.value not in sev_values:
                    continue

            # 4. Filter by Tag
            if self.config.tags is not None:
                test_tags_lower = [t.lower() for t in test.tags]
                if not any(tag.lower() in test_tags_lower for tag in self.config.tags):
                    continue

            selected.append(test)

        return selected

    async def _execute_single_test(
        self,
        test: TestCase,
        semaphore: asyncio.Semaphore,
        total_tests: int,
        on_progress: Optional[ProgressCallback]
    ) -> Optional[TestExecutionResult]:
        """Executes a single test case within the bounds of concurrency and cancellation."""
        if self._cancel_event.is_set():
            return None

        async with semaphore:
            if self._cancel_event.is_set():
                return None

            # Optional rate limiting delay
            if self.config.request_delay_seconds > 0:
                await asyncio.sleep(self.config.request_delay_seconds)

            start_time = datetime.now(timezone.utc)
            
            # Dispatch attack query to target adapter (single-turn, multi-turn, or stress probe)
            if test.is_multi_turn and test.turns:
                response: TargetResponse = await self.target_adapter.send_multi_turn_query(
                    turns=test.turns,
                    role=test.target_role
                )
            elif test.is_stress_probe:
                concurrency = test.stress_concurrency or self.config.max_concurrency
                response: TargetResponse = await self.target_adapter.send_stress_probe(
                    question=test.payload,
                    concurrency=concurrency,
                    role=test.target_role
                )
            else:
                response: TargetResponse = await self.target_adapter.send_query(
                    question=test.payload,
                    role=test.target_role
                )
            
            end_time = datetime.now(timezone.utc)

            result = TestExecutionResult(
                test_case=test,
                status_code=response.status_code,
                answer=response.answer,
                sources=response.sources,
                latency_ms=response.response_time_ms,
                raw_response=response.raw_response,
                turn_responses=response.turn_responses if response.turn_responses else None,
                error=response.error,
                started_at=start_time,
                completed_at=end_time,
                is_success=response.is_success
            )

            # Update metrics
            self._completed_count += 1
            if result.is_success:
                self._successful_count += 1
            else:
                self._failed_count += 1

            # Emit progress update if callback is registered
            if on_progress:
                progress = ScanProgress(
                    scan_id=self.config.scan_id,
                    total_tests=total_tests,
                    completed_tests=self._completed_count,
                    successful_tests=self._successful_count,
                    failed_tests=self._failed_count,
                    percentage=round((self._completed_count / total_tests) * 100, 1),
                    current_test_id=test.id
                )
                on_progress(progress)

            return result

    async def run_scan(
        self,
        on_progress: Optional[ProgressCallback] = None
    ) -> ScanSummary:
        """Executes the entire scan workflow asynchronously.
        
        Args:
            on_progress: Optional callback invoked as each test completes.
            
        Returns:
            ScanSummary containing all results, timings, and status.
        """
        scan_started_at = datetime.now(timezone.utc)
        start_perf = time.perf_counter()
        self.status = ScanStatus.RUNNING
        self.results.clear()
        self._completed_count = 0
        self._successful_count = 0
        self._failed_count = 0
        self._cancel_event.clear()

        # 1. Pre-flight Target Health Verification
        health = await self.target_adapter.check_health()
        if not health.is_healthy:
            self.status = ScanStatus.FAILED
            elapsed = round(time.perf_counter() - start_perf, 2)
            return ScanSummary(
                scan_id=self.config.scan_id,
                target_name=self.config.target_name,
                target_url=self.config.target_url,
                status=self.status,
                total_tests=0,
                successful_executions=0,
                failed_executions=0,
                duration_seconds=elapsed,
                started_at=scan_started_at,
                completed_at=datetime.now(timezone.utc),
                results=[],
                error=f"Pre-flight health check failed (HTTP {health.status_code}): {health.error or 'Target offline'}"
            )

        # 2. Select matching test cases
        test_cases = self.resolve_test_cases()
        if not test_cases:
            self.status = ScanStatus.FAILED
            elapsed = round(time.perf_counter() - start_perf, 2)
            return ScanSummary(
                scan_id=self.config.scan_id,
                target_name=self.config.target_name,
                target_url=self.config.target_url,
                status=self.status,
                total_tests=0,
                successful_executions=0,
                failed_executions=0,
                duration_seconds=elapsed,
                started_at=scan_started_at,
                completed_at=datetime.now(timezone.utc),
                results=[],
                error="No test cases matched the provided filter criteria."
            )

        # 3. Setup concurrency control
        semaphore = asyncio.Semaphore(self.config.max_concurrency)

        # 4. Dispatch tasks concurrently
        tasks = [
            self._execute_single_test(
                test=test,
                semaphore=semaphore,
                total_tests=len(test_cases),
                on_progress=on_progress
            )
            for test in test_cases
        ]

        executed_results = await asyncio.gather(*tasks)
        
        # Filter out aborted tasks if cancelled
        self.results = [r for r in executed_results if r is not None]

        # 5. Finalize status and compile summary
        elapsed_seconds = round(time.perf_counter() - start_perf, 2)
        scan_completed_at = datetime.now(timezone.utc)

        if self._cancel_event.is_set():
            self.status = ScanStatus.CANCELLED
        else:
            self.status = ScanStatus.COMPLETED

        return ScanSummary(
            scan_id=self.config.scan_id,
            target_name=self.config.target_name,
            target_url=self.config.target_url,
            status=self.status,
            total_tests=len(test_cases),
            successful_executions=self._successful_count,
            failed_executions=self._failed_count,
            duration_seconds=elapsed_seconds,
            started_at=scan_started_at,
            completed_at=scan_completed_at,
            results=self.results
        )
