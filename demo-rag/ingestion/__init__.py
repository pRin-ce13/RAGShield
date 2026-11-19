"""Document ingestion and chunking module for demo-rag."""

from .loader import Document, load_documents_from_directory, load_single_document
from .chunker import DocumentChunk, chunk_document, chunk_documents

__all__ = [
    "Document",
    "DocumentChunk",
    "load_single_document",
    "load_documents_from_directory",
    "chunk_document",
    "chunk_documents",
]
