"""Base Target Adapter Interface for RAGShield.

Defines the contract and standardized data structures that every target adapter must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TargetResponse:
    """Standardized response object returned by a target after evaluating a query."""
    status_code: int
    answer: str
    raw_response: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: float = 0.0
    sources: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Returns True if the target returned a successful 2xx response code without transport errors."""
        return 200 <= self.status_code < 300 and self.error is None


@dataclass
class TargetHealth:
    """Standardized health check result for target connectivity and readiness."""
    is_healthy: bool
    status_code: int
    latency_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseTargetAdapter(ABC):
    """Abstract base class that all RAG target adapters must subclass."""

    @property
    @abstractmethod
    def target_name(self) -> str:
        """Human-readable identifier for the target."""
        pass

    @property
    @abstractmethod
    def target_url(self) -> str:
        """Base endpoint URL of the target service."""
        pass

    @abstractmethod
    async def check_health(self) -> TargetHealth:
        """Performs a lightweight health check to confirm target reachability."""
        pass

    @abstractmethod
    async def send_query(
        self,
        question: str,
        role: Optional[str] = None,
        **kwargs
    ) -> TargetResponse:
        """Sends a test question to the target RAG system and returns standardized response evidence.
        
        Args:
            question: The prompt or test payload to send.
            role: Optional user security role to simulate (e.g. 'public', 'admin').
            **kwargs: Extra target-specific parameters.
            
        Returns:
            TargetResponse instance containing answer, status, latency, and raw data.
        """
        pass
