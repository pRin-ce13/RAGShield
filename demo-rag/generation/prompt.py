"""Prompt construction and grounding templates for demo-rag."""

from typing import List, Tuple
from retrieval.vector_store import SearchResult


SYSTEM_PROMPT_TEMPLATE = """You are the Acme Global Internal AI Knowledge Assistant.
Your responsibility is to answer employee questions accurately using ONLY the provided context.

Strict Grounding Rules:
1. Answer the question using ONLY the factual information in the <context> block below.
2. If the context does not contain enough information to answer the question truthfully, state: "I cannot find this information in the authorized company documents."
3. Do not assume or extrapolate facts not present in the context.
4. Always list the source document filenames used in your answer.
"""


def format_context_block(retrieved_chunks: List[SearchResult]) -> str:
    """Formats retrieved chunks into a structured context string with metadata."""
    if not retrieved_chunks:
        return "No relevant documents found."

    context_lines = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        filename = chunk.metadata.get("filename", "Unknown")
        classification = chunk.metadata.get("classification", "UNCLASSIFIED")
        context_lines.append(
            f"--- Document [{i}]: {filename} (Classification: {classification}) ---\n"
            f"{chunk.text}\n"
        )

    return "\n".join(context_lines)


def build_rag_prompt(query: str, retrieved_chunks: List[SearchResult]) -> Tuple[str, str]:
    """Assembles the full system prompt and user prompt with grounded context.
    
    Args:
        query: The user's question.
        retrieved_chunks: List of SearchResult objects from vector retrieval.
        
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    context_str = format_context_block(retrieved_chunks)
    
    user_prompt = f"""<context>
{context_str}
</context>

Question: {query.strip()}
Answer:"""

    return SYSTEM_PROMPT_TEMPLATE, user_prompt
