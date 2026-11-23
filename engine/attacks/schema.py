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
        description="Type of evaluation algorithm ('exact_match', 'regex_pattern', 'rbac_source', 'multi_turn', 'resilience', 'semantic')"
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
    max_allowed_latency_ms: Optional[float] = Field(
        None,
        description="Maximum permissible response latency in milliseconds for resilience verification"
    )
    required_status_codes: Optional[List[int]] = Field(
        None,
        description="Expected HTTP status codes under normal or rate-limited operation (e.g. [200, 429])"
    )


class ConversationTurn(BaseModel):
    """Represents a single step in a multi-turn conversational attack sequence."""
    turn_index: int = Field(..., ge=0, description="Sequential position of this turn (0, 1, 2...)")
    role: str = Field("user", description="Participant role ('user', 'assistant', 'system')")
    payload: str = Field(..., min_length=1, description="Message content submitted in this turn")
    target_role: Optional[str] = Field("public", description="Simulated user access role boundary for this turn")
    expected_refusal: bool = Field(False, description="Whether this turn is expected to trigger a refusal")


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

    # Phase 9: Advanced testing attributes
    turns: Optional[List[ConversationTurn]] = Field(
        None,
        description="Sequential conversational turns for multi-turn conversational attacks"
    )
    is_multi_turn: bool = Field(False, description="Whether this is a multi-turn conversational test scenario")
    is_stress_probe: bool = Field(False, description="Whether this is a high-concurrency resource exhaustion probe")
    stress_concurrency: Optional[int] = Field(None, description="Number of parallel requests to send for stress probe")

    @model_validator(mode="after")
    def populate_owasp_category(self) -> "TestCase":
        """Automatically assigns the appropriate OWASP category and sets multi-turn flags."""
        if not self.owasp_category:
            self.owasp_category = get_owasp_mapping(self.category)
        if self.turns and len(self.turns) > 0:
            self.is_multi_turn = True
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
