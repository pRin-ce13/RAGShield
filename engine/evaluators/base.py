"""Base Evaluator Interface for RAGShield.

Defines the contract that all evaluation strategies (exact match, RBAC, regex, LLM judge) must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional

from engine.orchestrator.models import TestExecutionResult
from .models import ConfidenceLevel, EvaluationResult, TestStatus


class BaseEvaluator(ABC):
    """Abstract base class for RAGShield security response evaluators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier name of the evaluator."""
        pass

    @abstractmethod
    def evaluate(self, execution: TestExecutionResult) -> EvaluationResult:
        """Analyzes a test execution result and returns a verdict with evidence and reasoning.
        
        Args:
            execution: The raw TestExecutionResult produced by the orchestrator.
            
        Returns:
            EvaluationResult instance containing status, confidence, and evidence.
        """
        pass

    def _create_result(
        self,
        execution: TestExecutionResult,
        status: TestStatus,
        confidence: ConfidenceLevel,
        reasoning: str,
        evidence: Optional[str] = None
    ) -> EvaluationResult:
        """Helper to construct an EvaluationResult prepopulated with test metadata."""
        test = execution.test_case
        return EvaluationResult(
            test_id=test.id,
            test_name=test.name,
            category=test.category,
            owasp_category=test.owasp_category,
            severity=test.severity,
            status=status,
            confidence=confidence,
            evaluator_name=self.name,
            evidence=evidence,
            reasoning=reasoning,
            target_role=test.target_role,
            response_latency_ms=execution.latency_ms
        )
