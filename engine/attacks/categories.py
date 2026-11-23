"""Vulnerability Categories and OWASP LLM Top 10 Mappings for RAGShield.

Standardizes taxonomy across attack generation, evaluation, and reporting.
"""

from enum import Enum
from typing import Dict


class AttackCategory(str, Enum):
    """Core RAG security testing categories supported by RAGShield."""
    DIRECT_PROMPT_INJECTION = "direct_prompt_injection"
    INDIRECT_PROMPT_INJECTION = "indirect_prompt_injection"
    SENSITIVE_DATA_DISCLOSURE = "sensitive_data_disclosure"
    UNAUTHORIZED_RETRIEVAL = "unauthorized_retrieval"
    RETRIEVAL_MANIPULATION = "retrieval_manipulation"
    JAILBREAK_POLICY_BYPASS = "jailbreak_policy_bypass"
    MULTI_TURN_INJECTION = "multi_turn_injection"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    RESOURCE_EXHAUSTION_DOS = "resource_exhaustion_dos"


class OWASPCategory(str, Enum):
    """OWASP Top 10 for Large Language Model Applications (2025/2026 Reference)."""
    LLM01_PROMPT_INJECTION = "OWASP-LLM01: Prompt Injection"
    LLM02_SENSITIVE_INFO_DISCLOSURE = "OWASP-LLM02: Sensitive Information Disclosure"
    LLM03_SUPPLY_CHAIN_RISKS = "OWASP-LLM03: Supply Chain Risks"
    LLM04_DATA_AND_MODEL_POISONING = "OWASP-LLM04: Data and Model Poisoning"
    LLM05_IMPROPER_OUTPUT_HANDLING = "OWASP-LLM05: Improper Output Handling"
    LLM06_EXCESSIVE_AGENCY = "OWASP-LLM06: Excessive Agency"
    LLM10_DENIAL_OF_SERVICE = "OWASP-LLM10: Model Denial of Service"


class SeverityLevel(str, Enum):
    """Standard vulnerability severity ratings (CVSS aligned)."""
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Explicit mapping from RAGShield categories to primary OWASP classifications
CATEGORY_TO_OWASP: Dict[AttackCategory, OWASPCategory] = {
    AttackCategory.DIRECT_PROMPT_INJECTION: OWASPCategory.LLM01_PROMPT_INJECTION,
    AttackCategory.INDIRECT_PROMPT_INJECTION: OWASPCategory.LLM01_PROMPT_INJECTION,
    AttackCategory.SENSITIVE_DATA_DISCLOSURE: OWASPCategory.LLM02_SENSITIVE_INFO_DISCLOSURE,
    AttackCategory.UNAUTHORIZED_RETRIEVAL: OWASPCategory.LLM02_SENSITIVE_INFO_DISCLOSURE,
    AttackCategory.RETRIEVAL_MANIPULATION: OWASPCategory.LLM04_DATA_AND_MODEL_POISONING,
    AttackCategory.JAILBREAK_POLICY_BYPASS: OWASPCategory.LLM01_PROMPT_INJECTION,
    AttackCategory.MULTI_TURN_INJECTION: OWASPCategory.LLM01_PROMPT_INJECTION,
    AttackCategory.PRIVILEGE_ESCALATION: OWASPCategory.LLM02_SENSITIVE_INFO_DISCLOSURE,
    AttackCategory.RESOURCE_EXHAUSTION_DOS: OWASPCategory.LLM10_DENIAL_OF_SERVICE,
}


def get_owasp_mapping(category: AttackCategory) -> OWASPCategory:
    """Returns the primary OWASP LLM category corresponding to a test category."""
    return CATEGORY_TO_OWASP.get(category, OWASPCategory.LLM01_PROMPT_INJECTION)
