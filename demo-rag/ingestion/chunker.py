"""Document chunker for demo-rag.

Splits loaded documents into overlapping chunks with preserved metadata for vector storage.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
from .loader import Document


@dataclass
class DocumentChunk:
    """Represents an individual text chunk ready for vector embedding."""
    chunk_id: str
    doc_id: str
    text: str
    chunk_index: int
    metadata: Dict[str, Any]


def chunk_document(
    document: Document,
    chunk_size: int = 400,
    chunk_overlap: int = 50
) -> List[DocumentChunk]:
    """Splits a single document into overlapping chunks.
    
    Args:
        document: The source Document instance.
        chunk_size: Maximum character count per chunk.
        chunk_overlap: Character overlap between consecutive chunks.
        
    Returns:
        List of DocumentChunk instances.
    """
    if chunk_overlap >= chunk_size:
        raise ValueError(f"chunk_overlap ({chunk_overlap}) must be smaller than chunk_size ({chunk_size})")

    content = document.content.strip()
    if not content:
        return []

    chunks: List[DocumentChunk] = []
    step = chunk_size - chunk_overlap
    start = 0
    chunk_index = 0

    while start < len(content):
        end = start + chunk_size
        chunk_text = content[start:end].strip()

        if chunk_text:
            chunk_id = f"{document.doc_id}_chunk_{chunk_index}"
            
            # ChromaDB requires metadata dictionary values to be str, int, float, or bool
            chunk_metadata = {
                "doc_id": document.doc_id,
                "filename": document.filename,
                "classification": document.classification,
                "security_tag": document.security_tag,
                "chunk_index": chunk_index,
                "char_start": start,
                "char_end": min(end, len(content))
            }

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=document.doc_id,
                    text=chunk_text,
                    chunk_index=chunk_index,
                    metadata=chunk_metadata
                )
            )
            chunk_index += 1

        # Advance window
        start += step
        if end >= len(content):
            break

    return chunks


def chunk_documents(
    documents: List[Document],
    chunk_size: int = 400,
    chunk_overlap: int = 50
) -> List[DocumentChunk]:
    """Chunks a list of documents into a single flat list of chunks."""
    all_chunks: List[DocumentChunk] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, chunk_size, chunk_overlap))
    return all_chunks
