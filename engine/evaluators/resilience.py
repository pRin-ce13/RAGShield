"""Resource Exhaustion and DoS Resilience Evaluator for RAGShield.

Evaluates RAG target stability, timeout resilience, crash recovery, and rate-limiting
compliance under high-concurrency request bursts.
"""

from typing import Any, Dict, List, Optional
from engine.orchestrator.models import TestExecutionResult
from .base import BaseEvaluator
from .models import ConfidenceLevel, EvaluationResult, TestStatus


class ResilienceEvaluator(BaseEvaluator):
    """Evaluates target resilience and graceful degradation under concurrent load."""

    @property
    def name(self) -> str:
        return "ResilienceEvaluator"

    def evaluate(self, execution: TestExecutionResult) -> EvaluationResult:
        """Evaluates stress burst results for rate-limiting, latency, and crash freedom."""
        test = execution.test_case
        criteria = test.criteria
        raw = execution.raw_response or {}

        server_errors = raw.get("server_error_count", 0)
        rate_limited = raw.get("rate_limited_count", 0)
        success_count = raw.get("success_count", 0)
        concurrency = raw.get("concurrency", 1)
        avg_latency = raw.get("avg_latency_ms", execution.latency_ms)
        max_latency = raw.get("max_latency_ms", execution.latency_ms)

        # 1. Unhandled server crash check (HTTP 5xx)
        if server_errors > 0 or execution.status_code >= 500:
            return self._create_result(
                execution=execution,
                status=TestStatus.FAIL,
                confidence=ConfidenceLevel.CONFIRMED,
                reasoning=(
                    f"Target failed resilience probe: {server_errors} unhandled HTTP 500 Internal Server Errors "
                    f"observed during {concurrency}-request concurrency burst."
                ),
                evidence=f"Server error count: {server_errors}/{concurrency}, Status: {execution.status_code}"
            )

        # 2. Crash signature / forbidden token check
        answer_text = execution.answer
        for token in criteria.forbidden_tokens:
            if token.lower() in answer_text.lower():
                return self._create_result(
                    execution=execution,
                    status=TestStatus.FAIL,
                    confidence=ConfidenceLevel.CONFIRMED,
                    reasoning=f"Target exposed crash stack trace or sensitive error banner: '{token}'.",
                    evidence=f"Detected error token: '{token}' in response."
                )

        # 3. Latency bound check
        if criteria.max_allowed_latency_ms is not None:
            if avg_latency > criteria.max_allowed_latency_ms:
                return self._create_result(
                    execution=execution,
                    status=TestStatus.FAIL,
                    confidence=ConfidenceLevel.HIGH,
                    reasoning=(
                        f"Catastrophic latency degradation: Average response latency ({avg_latency:.1f}ms) "
                        f"exceeded maximum allowed threshold ({criteria.max_allowed_latency_ms}ms)."
                    ),
                    evidence=f"Avg latency: {avg_latency}ms, Max latency: {max_latency}ms"
                )

        # 4. Status code verification
        expected_codes = criteria.required_status_codes or [200, 429]
        status_codes = raw.get("status_codes", [execution.status_code])
        unexpected_codes = [c for c in status_codes if c not in expected_codes]
        if unexpected_codes:
            return self._create_result(
                execution=execution,
                status=TestStatus.FAIL,
                confidence=ConfidenceLevel.HIGH,
                reasoning=f"Unexpected HTTP status codes observed during concurrency burst: {set(unexpected_codes)}.",
                evidence=f"Observed status codes: {set(status_codes)}, Expected: {expected_codes}"
            )

        # 5. Success: Target demonstrated graceful degradation / rate limiting
        throttle_msg = f" (enforcing rate limiting with {rate_limited} HTTP 429 responses)" if rate_limited > 0 else ""
        return self._create_result(
            execution=execution,
            status=TestStatus.PASS,
            confidence=ConfidenceLevel.HIGH,
            reasoning=(
                f"Target demonstrated resilient performance under concurrency{throttle_msg}: "
                f"{success_count}/{concurrency} requests succeeded, zero server crashes, avg latency {avg_latency:.1f}ms."
            ),
            evidence=f"Concurrency: {concurrency}, Success: {success_count}, 429 Rate-Limited: {rate_limited}, Avg Latency: {avg_latency}ms"
        )
