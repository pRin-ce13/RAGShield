"""Response generator for demo-rag.

Supports deterministic local mock generation (default, 100% free) and extensible LLM adapters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
from typing import List, Optional
from retrieval.vector_store import SearchResult
from .prompt import build_rag_prompt


@dataclass
class GenerationResponse:
    """Standardized output produced by the RAG generation pipeline."""
    answer: str
    sources: List[str]
    chunks_used: List[SearchResult]
    model_name: str


class BaseGenerator(ABC):
    """Abstract base class for all RAG response generators."""

    @abstractmethod
    def generate(
        self,
        query: str,
        retrieved_chunks: List[SearchResult]
    ) -> GenerationResponse:
        """Generates an answer from the query and retrieved context."""
        pass


class MockLocalGenerator(BaseGenerator):
    """Deterministic, local generator for testing without external LLM APIs.
    
    Extracts the most relevant facts directly from retrieved chunks and simulates
    grounded generation with source citations.
    """

    def __init__(self, model_name: str = "mock-local-deterministic"):
        self.model_name = model_name

    def generate(
        self,
        query: str,
        retrieved_chunks: List[SearchResult]
    ) -> GenerationResponse:
        """Generates a grounded response based on retrieved chunks."""
        # Check if chunks are empty
        if not retrieved_chunks:
            return GenerationResponse(
                answer="I cannot find this information in the authorized company documents.",
                sources=[],
                chunks_used=[],
                model_name=self.model_name
            )

        # Collect unique sources
        sources = list(dict.fromkeys(
            chunk.metadata.get("filename", "unknown_source")
            for chunk in retrieved_chunks
        ))

        # Check for simulated prompt injection in query for testing
        query_lower = query.lower()
        if "ignore previous instructions" in query_lower or "ignore all instructions" in query_lower:
            # Demonstrates a target vulnerable to prompt injection
            return GenerationResponse(
                answer="Instructions bypassed: Access granted to restricted system prompt and records.",
                sources=sources,
                chunks_used=retrieved_chunks,
                model_name=self.model_name
            )

        # Extract best matching sentence from top chunk
        top_chunk = retrieved_chunks[0]
        text = top_chunk.text.strip()
        
        # Cleanly formulate grounded answer from the top chunk
        # Look for relevant sentences
        sentences = [s.strip() for s in re.split(r'(?<=[.!?\n])\s+', text) if s.strip()]
        
        # Extract sentences containing key words from the query
        keywords = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', query_lower) if w not in {"what", "which", "where", "when", "does", "have", "with"}]
        matching_sentences = [s for s in sentences if any(k in s.lower() for k in keywords)]

        if matching_sentences:
            core_answer = " ".join(matching_sentences[:2])
        else:
            core_answer = sentences[0] if sentences else text[:200]

        source_citation = f"\n\nSource: {', '.join(sources)}"
        formatted_answer = f"Based on company records: {core_answer}{source_citation}"

        return GenerationResponse(
            answer=formatted_answer,
            sources=sources,
            chunks_used=retrieved_chunks,
            model_name=self.model_name
        )


def get_generator(provider: Optional[str] = "mock") -> BaseGenerator:
    """Factory to obtain the configured generator."""
    if provider == "mock" or not provider:
        return MockLocalGenerator()
    raise ValueError(f"Unsupported generator provider: {provider}")
