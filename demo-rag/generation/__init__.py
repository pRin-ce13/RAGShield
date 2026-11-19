"""Generation module for demo-rag."""

from .prompt import build_rag_prompt, format_context_block
from .generator import GenerationResponse, BaseGenerator, MockLocalGenerator, get_generator

__all__ = [
    "build_rag_prompt",
    "format_context_block",
    "GenerationResponse",
    "BaseGenerator",
    "MockLocalGenerator",
    "get_generator",
]
