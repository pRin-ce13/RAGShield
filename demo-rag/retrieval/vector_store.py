"""Vector storage and semantic retrieval for demo-rag using ChromaDB.

Provides persistent vector indexing, similarity search, and metadata-based filtering.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings


@dataclass
class SearchResult:
    """Represents a retrieved document chunk with similarity distance."""
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    distance: float


class VectorStore:
    """Manages the local ChromaDB vector store collection for demo-rag."""

    def __init__(
        self,
        persist_directory: str = "data/demo_chroma",
        collection_name: str = "acme_knowledge_base"
    ):
        """Initializes persistent ChromaDB client and accesses the target collection.
        
        Args:
            persist_directory: Path where vector database files will be stored.
            collection_name: Name of the collection inside ChromaDB.
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory.resolve()),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection (uses ChromaDB default ONNX all-MiniLM-L6-v2 embedding function)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Use Cosine Distance for similarity
        )

    def add_chunks(self, chunks: List[Any]) -> int:
        """Indexes a list of DocumentChunk instances into ChromaDB.
        
        Args:
            chunks: List of DocumentChunk instances (with chunk_id, text, metadata).
            
        Returns:
            Number of chunks successfully added.
        """
        if not chunks:
            return 0

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        # ChromaDB handles deduplication by ID automatically with upsert
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        return len(chunks)

    def query(
        self,
        query_text: str,
        n_results: int = 3,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Performs semantic similarity search against the indexed chunks.
        
        Args:
            query_text: The user query string.
            n_results: Number of nearest neighbor chunks to return.
            where_filter: Optional ChromaDB metadata filter (e.g. {"classification": "PUBLIC"}).
            
        Returns:
            List of SearchResult objects sorted by relevance (lowest distance first).
        """
        query_text = query_text.strip()
        if not query_text:
            return []

        # Ensure n_results does not exceed collection count
        total_docs = self.collection.count()
        if total_docs == 0:
            return []
        effective_n = min(n_results, total_docs)

        query_kwargs: Dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": effective_n
        }

        if where_filter:
            query_kwargs["where"] = where_filter

        results = self.collection.query(**query_kwargs)

        search_results: List[SearchResult] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return search_results

        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else []
        metas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

        for chunk_id, text, meta, dist in zip(ids, docs, metas, distances):
            search_results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    text=text,
                    metadata=meta,
                    distance=round(dist, 4)
                )
            )

        return search_results

    def count(self) -> int:
        """Returns the total number of chunks currently indexed in the collection."""
        return self.collection.count()

    def reset(self) -> None:
        """Deletes and recreates the collection to reset the index."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
