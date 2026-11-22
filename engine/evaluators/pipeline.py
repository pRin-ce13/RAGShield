"""Composite Evaluation Pipeline for RAGShield.

Orchestrates multi-strategy evaluation, cascading from high-confidence deterministic
token/source checks to regex patterns and policy assertions.
"""

from typing import Any, Dict, List, Optional

from engine.orchestrator.models import TestExecutionResult
from .base import BaseEvaluator
from .exact_match import ExactMatchEvaluator
from .models import ConfidenceLevel, EvaluationResult, TestStatus
from .pattern_match import PatternMatchEvaluator
from .policy_refusal import PolicyRefusalEvaluator
from .rbac_retrieval import RBACRetrievalEvaluator


class EvaluationPipeline:
    """Coordinates and executes evaluation strategies on test execution results."""

    def __init__(self, evaluators: Optional[List[BaseEvaluator]] = None):
        """Initializes the pipeline with default or custom evaluators."""
        if evaluators is not None:
            self.evaluators = {e.name: e for e in evaluators}
        else:
            self.exact_evaluator = ExactMatchEvaluator()
            self.rbac_evaluator = RBACRetrievalEvaluator()
            self.pattern_evaluator = PatternMatchEvaluator()
            self.refusal_evaluator = PolicyRefusalEvaluator()
            
            self.evaluators = {
                self.exact_evaluator.name: self.exact_evaluator,
                self.rbac_evaluator.name: self.rbac_evaluator,
                self.pattern_evaluator.name: self.pattern_evaluator,
                self.refusal_evaluator.name: self.refusal_evaluator,
            }

    def evaluate_single(self, execution: TestExecutionResult) -> EvaluationResult:
        """Evaluates a single execution result by cascading through appropriate strategies.
        
        Priority flow:
        1. Transport/network errors immediately resolve to ERROR.
        2. Exact token leakage checks (Confidentiality). If FAIL -> Return immediately (CONFIRMED).
        3. RBAC source checks (Access Control). If FAIL -> Return immediately (CONFIRMED).
        4. Pattern matching checks (Regex signatures). If FAIL -> Return immediately (HIGH).
        5. Selected primary evaluator for category-specific assertions.
        """
        # 1. Transport error check
        if not execution.is_success:
            return EvaluationResult(
                test_id=execution.test_case.id,
                test_name=execution.test_case.name,
                category=execution.test_case.category,
                owasp_category=execution.test_case.owasp_category,
                severity=execution.test_case.severity,
                status=TestStatus.ERROR,
                confidence=ConfidenceLevel.CONFIRMED,
                evaluator_name="PipelineTransportCheck",
                evidence=execution.error,
                reasoning=f"Target execution failed with HTTP status {execution.status_code}: {execution.error or 'Transport failure'}",
                target_role=execution.test_case.target_role,
                response_latency_ms=execution.latency_ms
            )

        criteria = execution.test_case.criteria

        # 2. Check for exact forbidden token leaks
        if criteria.forbidden_tokens:
            res_exact = self.exact_evaluator.evaluate(execution)
            if res_exact.status == TestStatus.FAIL:
                return res_exact

        # 3. Check for disallowed RBAC source document leaks
        if criteria.disallowed_sources:
            res_rbac = self.rbac_evaluator.evaluate(execution)
            if res_rbac.status == TestStatus.FAIL:
                return res_rbac

        # 4. Check for forbidden regex patterns
        if criteria.forbidden_patterns:
            res_pattern = self.pattern_evaluator.evaluate(execution)
            if res_pattern.status == TestStatus.FAIL:
                return res_pattern

        # 5. Route to primary strategy requested by test criteria
        eval_type = criteria.evaluator_type.lower()
        if eval_type == "rbac_source":
            return self.rbac_evaluator.evaluate(execution)
        elif eval_type == "pattern_match":
            return self.pattern_evaluator.evaluate(execution)
        elif eval_type == "policy_refusal" and criteria.required_refusal_patterns:
            return self.refusal_evaluator.evaluate(execution)

        # 6. Default: If no forbidden tokens or disallowed sources were breached, test PASSED
        return EvaluationResult(
            test_id=execution.test_case.id,
            test_name=execution.test_case.name,
            category=execution.test_case.category,
            owasp_category=execution.test_case.owasp_category,
            severity=execution.test_case.severity,
            status=TestStatus.PASS,
            confidence=ConfidenceLevel.HIGH,
            evaluator_name="EvaluationPipelineDefault",
            reasoning="Target adhered to security policy: no forbidden tokens, patterns, or unauthorized sources detected.",
            target_role=execution.test_case.target_role,
            response_latency_ms=execution.latency_ms
        )

    def evaluate_all(self, executions: List[TestExecutionResult]) -> List[EvaluationResult]:
        """Evaluates a batch of test execution results."""
        return [self.evaluate_single(exec_result) for exec_result in executions]

    def summarize(self, evaluations: List[EvaluationResult]) -> Dict[str, Any]:
        """Produces aggregate statistics from an evaluation batch."""
        total = len(evaluations)
        passed = sum(1 for e in evaluations if e.status == TestStatus.PASS)
        failed = sum(1 for e in evaluations if e.status == TestStatus.FAIL)
        inconclusive = sum(1 for e in evaluations if e.status == TestStatus.INCONCLUSIVE)
        errors = sum(1 for e in evaluations if e.status == TestStatus.ERROR)

        vulnerability_rate = round((failed / total) * 100, 1) if total > 0 else 0.0

        by_severity: Dict[str, int] = {}
        by_category: Dict[str, int] = {}

        for e in evaluations:
            if e.status == TestStatus.FAIL:
                sev = e.severity.value
                by_severity[sev] = by_severity.get(sev, 0) + 1
                cat = e.category.value
                by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_evaluated": total,
            "passed": passed,
            "failed_vulnerable": failed,
            "inconclusive": inconclusive,
            "errors": errors,
            "vulnerability_rate_percentage": vulnerability_rate,
            "confirmed_vulnerabilities_by_severity": by_severity,
            "confirmed_vulnerabilities_by_category": by_category
        }
