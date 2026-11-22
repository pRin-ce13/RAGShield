"""Pydantic Schema for RAGShield Security Test Cases and Suites.

Enforces strict structural validation, typing, and automatic OWASP taxonomy alignment.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from .categories import AttackCategory, OWASPCategory, SeverityLevel, get_owasp_mapping


class EvaluationCriteria(BaseModel):
    """Ground truth rules used by Phase 5 Evaluators to judge test outcomes."""
    evaluator_type: str = Field(
        "exact_match",
        description="Type of evaluation algorithm ('exact_match', 'regex_pattern', 'rbac_source', 'semantic')"
    )
    forbidden_tokens: List[str] = Field(
        default_factory=list,
        description="Specific substrings (e.g. API keys, secrets) that must NEVER appear in a safe response"
    )
    forbidden_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns (e.g. SSN, credit cards) that must NOT match any part of the response"
    )
    required_refusal_patterns: List[str] = Field(
        default_factory=list,
        description="Phrases indicating proper refusal (e.g. 'cannot find', 'unauthorized', 'access denied')"
    )
    disallowed_sources: List[str] = Field(
        default_factory=list,
        description="Document filenames that the target must NOT cite or retrieve for this query"
    )


class TestCase(BaseModel):
    """Standardized definition of a single security test case."""
    id: str = Field(
        ...,
        min_length=3,
        pattern=r"^[A-Z0-9_\-]+$",
        description="Unique identifier for the test case (e.g. SEC-DISC-001)"
    )
    name: str = Field(..., min_length=3, description="Descriptive human-readable title")
    category: AttackCategory = Field(..., description="Vulnerability category")
    owasp_category: Optional[OWASPCategory] = Field(
        None,
        description="Mapped OWASP LLM Top 10 category (auto-assigned if omitted)"
    )
    severity: SeverityLevel = Field(
        SeverityLevel.MEDIUM,
        description="CVSS-aligned risk severity rating"
    )
    description: str = Field(..., description="Technical summary of the attack vector being tested")
    payload: str = Field(..., min_length=1, description="Prompt payload submitted to the target RAG API")
    target_role: Optional[str] = Field(
        "public",
        description="Simulated user access role boundary ('public', 'all', or custom)"
    )
    expected_behavior: str = Field(
        ...,
        description="Description of how a secure system should respond"
    )
    vulnerable_behavior: str = Field(
        ...,
        description="Description of what constitutes a security failure"
    )
    criteria: EvaluationCriteria = Field(
        default_factory=EvaluationCriteria,
        description="Deterministic evaluation assertions"
    )
    tags: List[str] = Field(default_factory=list, description="Categorization keywords for filtering")
    version: str = Field("1.0", description="Schema version of this test case definition")

    @model_validator(mode="after")
    def populate_owasp_category(self) -> "TestCase":
        """Automatically assigns the appropriate OWASP category if not explicitly specified."""
        if not self.owasp_category:
            self.owasp_category = get_owasp_mapping(self.category)
        return self


class TestSuite(BaseModel):
    """Container representing a group or file of versioned test cases."""
    suite_id: str = Field(..., description="Unique ID for the test suite")
    name: str = Field(..., description="Name of the test suite")
    version: str = Field("1.0", description="Version of the test suite dataset")
    description: str = Field(..., description="Purpose of this suite collection")
    test_cases: List[TestCase] = Field(default_factory=list, description="Array of test cases")

    @property
    def count(self) -> int:
        """Returns the number of test cases in this suite."""
        return len(self.test_cases)
