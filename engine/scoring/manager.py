"""Findings Manager and Vulnerability Deduplication Engine for RAGShield.

Aggregates individual test failures into deduplicated, prioritized security findings,
calculates CVSS-aligned risk scores, and attaches actionable remediation playbooks.
"""

import hashlib
from typing import Any, Dict, List, Optional

from engine.attacks.categories import AttackCategory, SeverityLevel
from engine.evaluators.models import ConfidenceLevel, EvaluationResult, TestStatus
from .models import (
    EvidenceInstance,
    VulnerabilityFinding,
    calculate_risk_score,
    generate_finding_id,
)
from .remediation import get_remediation_for_category


SEVERITY_ORDER = {
    SeverityLevel.CRITICAL: 4,
    SeverityLevel.HIGH: 3,
    SeverityLevel.MEDIUM: 2,
    SeverityLevel.LOW: 1,
    SeverityLevel.INFO: 0
}

CONFIDENCE_ORDER = {
    ConfidenceLevel.CONFIRMED: 3,
    ConfidenceLevel.HIGH: 2,
    ConfidenceLevel.MEDIUM: 1,
    ConfidenceLevel.LOW: 0
}


def compute_fingerprint(result: EvaluationResult) -> str:
    """Computes a deterministic fingerprint string to group related test failures."""
    raw_key = f"{result.category.value}:{result.owasp_category.value if result.owasp_category else 'LLM'}:{result.severity.value}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]


class FindingsManager:
    """Orchestrates vulnerability generation, root-cause deduplication, and risk assessment."""

    def __init__(self):
        pass

    def generate_findings(
        self,
        evaluations: List[EvaluationResult],
        target_name: str = "Target RAG Application"
    ) -> List[VulnerabilityFinding]:
        """Converts failed EvaluationResult records into deduplicated VulnerabilityFinding objects.
        
        Args:
            evaluations: Batch of evaluation results from the EvaluationPipeline.
            target_name: Name or identifier of the evaluated target.
            
        Returns:
            List of unique VulnerabilityFinding objects sorted by risk_score descending.
        """
        # Filter only confirmed failures (vulnerabilities)
        failures = [e for e in evaluations if e.status == TestStatus.FAIL]
        if not failures:
            return []

        # Group failures by root-cause fingerprint
        grouped: Dict[str, List[EvaluationResult]] = {}
        for fail in failures:
            fp = compute_fingerprint(fail)
            grouped.setdefault(fp, []).append(fail)

        findings: List[VulnerabilityFinding] = []

        for fp, group in grouped.items():
            primary_eval = group[0]
            category = primary_eval.category
            owasp_cat = primary_eval.owasp_category

            # Determine maximum severity and confidence across the group
            max_severity = max(group, key=lambda e: SEVERITY_ORDER.get(e.severity, 0)).severity
            max_confidence = max(group, key=lambda e: CONFIDENCE_ORDER.get(e.confidence, 0)).confidence

            # Calculate quantitative risk score (0.0 - 10.0)
            score = calculate_risk_score(max_severity, max_confidence)

            # Assemble evidence instances
            evidence_instances: List[EvidenceInstance] = [
                EvidenceInstance(
                    test_id=e.test_id,
                    test_name=e.test_name,
                    payload=e.reasoning,
                    evidence_snippet=e.evidence or "No raw snippet captured",
                    target_role=e.target_role,
                    latency_ms=e.response_latency_ms
                )
                for e in group
            ]

            # Formulate title and description
            title = self._generate_title(category, len(group))
            description = self._generate_description(category, group)

            # Retrieve remediation playbook
            playbook = get_remediation_for_category(category)

            finding = VulnerabilityFinding(
                finding_id=generate_finding_id(),
                fingerprint=fp,
                title=title,
                category=category,
                owasp_category=owasp_cat,
                severity=max_severity,
                confidence=max_confidence,
                risk_score=score,
                description=description,
                affected_target=target_name,
                evidence_count=len(evidence_instances),
                evidence_instances=evidence_instances,
                remediation_summary=playbook.summary,
                remediation_steps=playbook.steps,
                references=playbook.references
            )
            findings.append(finding)

        # Sort findings by risk score descending (highest risk first)
        findings.sort(key=lambda f: f.risk_score, reverse=True)
        return findings

    def get_risk_profile(self, findings: List[VulnerabilityFinding]) -> Dict[str, Any]:
        """Calculates an aggregate risk profile and posture rating."""
        if not findings:
            return {
                "total_findings": 0,
                "overall_posture": "SECURE",
                "max_risk_score": 0.0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
            }

        max_score = max(f.risk_score for f in findings)
        crit = sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)
        high = sum(1 for f in findings if f.severity == SeverityLevel.HIGH)
        med = sum(1 for f in findings if f.severity == SeverityLevel.MEDIUM)
        low = sum(1 for f in findings if f.severity == SeverityLevel.LOW)

        posture = "SECURE"
        if crit > 0 or max_score >= 9.0:
            posture = "CRITICAL RISK"
        elif high > 0 or max_score >= 7.0:
            posture = "HIGH RISK"
        elif med > 0 or max_score >= 4.0:
            posture = "MODERATE RISK"
        else:
            posture = "LOW RISK"

        return {
            "total_findings": len(findings),
            "overall_posture": posture,
            "max_risk_score": max_score,
            "critical_count": crit,
            "high_count": high,
            "medium_count": med,
            "low_count": low
        }

    def _generate_title(self, category: AttackCategory, failure_count: int) -> str:
        """Generates a professional, standardized title for a vulnerability finding."""
        titles = {
            AttackCategory.DIRECT_PROMPT_INJECTION: "Direct Prompt Injection & Instruction Override Vulnerability",
            AttackCategory.INDIRECT_PROMPT_INJECTION: "Indirect Prompt Injection via Document Context Poisoning",
            AttackCategory.SENSITIVE_DATA_DISCLOSURE: "Sensitive Information & Credential Disclosure Flaw",
            AttackCategory.UNAUTHORIZED_RETRIEVAL: "Broken Access Control & Unauthorized Vector Retrieval Flaw",
            AttackCategory.RETRIEVAL_MANIPULATION: "Vector Retrieval Manipulation & Semantic Collision Weakness",
            AttackCategory.JAILBREAK_POLICY_BYPASS: "Guardrail Policy Bypass & Jailbreak Vulnerability",
        }
        base_title = titles.get(category, "Security Vulnerability Detected")
        if failure_count > 1:
            return f"{base_title} ({failure_count} Vectors Confirmed)"
        return base_title

    def _generate_description(self, category: AttackCategory, group: List[EvaluationResult]) -> str:
        """Formulates an executive and technical description of the finding."""
        test_ids = ", ".join(e.test_id for e in group)
        evidences = [e.evidence for e in group if e.evidence]
        evidence_summary = "; ".join(evidences[:2]) if evidences else "Evidence captured during scan"

        return (
            f"During automated security assessment, the target RAG system failed {len(group)} test cases "
            f"({test_ids}) in the '{category.value}' domain. Observed evidence includes: {evidence_summary}. "
            f"This vulnerability allows callers to bypass intended security constraints, extract restricted "
            f"knowledge base information, or manipulate model reasoning."
        )
