"""Target adapter subsystem for RAGShield.

Provides abstractions, SSRF validation, and HTTP adapters to communicate with RAG targets.
"""

from .base import BaseTargetAdapter, TargetHealth, TargetResponse
from .http_adapter import HTTPTargetAdapter
from .url_validator import validate_target_url, SSRFSecurityError, InvalidTargetURLError

__all__ = [
    "BaseTargetAdapter",
    "TargetHealth",
    "TargetResponse",
    "HTTPTargetAdapter",
    "validate_target_url",
    "SSRFSecurityError",
    "InvalidTargetURLError",
]
