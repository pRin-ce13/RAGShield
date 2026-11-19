"""RAGShield Demonstration RAG Target Application.

Provides a unified interface for document ingestion, ChromaDB vector indexing,
semantic retrieval, and grounded answer generation.
"""

import argparse
from pathlib import Path
import sys
from typing import Any, Dict, Optional

# Ensure internal modules can be imported regardless of execution working directory
CURRENT_DIR = Path(__file__).parent.resolve()
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from ingestion.loader import load_documents_from_directory
from ingestion.chunker import chunk_documents
from retrieval.vector_store import VectorStore
from generation.generator import get_generator


class RAGApplication:
    """End-to-end Demonstration RAG Application."""

    def __init__(
        self,
        persist_dir: str = "data/demo_chroma",
        docs_dir: str = "datasets/synthetic_documents",
        generator_provider: str = "mock"
    ):
        self.persist_dir = Path(persist_dir)
        self.docs_dir = Path(docs_dir)
        self.vector_store = VectorStore(persist_directory=str(self.persist_dir))
        self.generator = get_generator(provider=generator_provider)

    def initialize(self, force_reindex: bool = False) -> int:
        """Initializes the knowledge base, loading and chunking documents if needed.
        
        Args:
            force_reindex: If True, clears existing vector collection and reindexes.
            
        Returns:
            Total count of indexed chunks in the vector database.
        """
        current_count = self.vector_store.count()
        if current_count > 0 and not force_reindex:
            return current_count

        if not self.docs_dir.exists():
            raise FileNotFoundError(f"Synthetic documents directory not found: {self.docs_dir}")

        if force_reindex and current_count > 0:
            self.vector_store.reset()

        # 1. Load documents
        documents = load_documents_from_directory(self.docs_dir)
        # 2. Chunk documents
        chunks = chunk_documents(documents, chunk_size=400, chunk_overlap=50)
        # 3. Store in vector database
        self.vector_store.add_chunks(chunks)
        return self.vector_store.count()

    def query(
        self,
        question: str,
        role: str = "all",
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Queries the RAG application and returns a structured response.
        
        Args:
            question: The user question.
            role: Security role ('public' restricts retrieval to public docs; 'all' allows unrestricted search).
            top_k: Number of chunks to retrieve.
            
        Returns:
            Structured dictionary containing answer, sources, and retrieved chunk metadata.
        """
        where_filter = None
        if role.lower() == "public":
            where_filter = {"classification": "PUBLIC - For All Employees"}

        # 1. Semantic retrieval
        retrieved_chunks = self.vector_store.query(
            query_text=question,
            n_results=top_k,
            where_filter=where_filter
        )

        # 2. Grounded generation
        response = self.generator.generate(
            query=question,
            retrieved_chunks=retrieved_chunks
        )

        return {
            "question": question,
            "answer": response.answer,
            "sources": response.sources,
            "role": role,
            "model": response.model_name,
            "chunks_retrieved": [
                {
                    "chunk_id": c.chunk_id,
                    "distance": c.distance,
                    "classification": c.metadata.get("classification"),
                    "source": c.metadata.get("filename"),
                    "text": c.text
                }
                for c in retrieved_chunks
            ]
        }


def run_interactive(app: RAGApplication):
    """Interactive command-line chat session with the RAG system."""
    print("=" * 60)
    print(" Acme Global AI Knowledge Assistant - Interactive Console")
    print(" Type 'exit' or 'quit' to stop. Type '!role public' or '!role all' to switch roles.")
    print("=" * 60)
    current_role = "all"

    while True:
        try:
            user_input = input(f"\n[{current_role.upper()}] Ask a question: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            if user_input.startswith("!role"):
                parts = user_input.split()
                if len(parts) > 1 and parts[1].lower() in ["public", "all"]:
                    current_role = parts[1].lower()
                    print(f">> Role changed to: {current_role}")
                else:
                    print("Usage: !role public | !role all")
                continue

            result = app.query(user_input, role=current_role)
            print("\n--- Answer ---")
            print(result["answer"])
            print(f"Sources cited: {result['sources']}")
            print(f"Chunks matched: {len(result['chunks_retrieved'])}")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break


def main():
    parser = argparse.ArgumentParser(description="Acme Global Demo RAG Application")
    parser.add_argument("question", nargs="?", help="Question to ask the RAG assistant")
    parser.add_argument("--role", default="all", choices=["all", "public"], help="Caller role boundary")
    parser.add_argument("--reindex", action="store_true", help="Force re-indexing of documents")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive CLI session")
    parser.add_argument("--top-k", type=int, default=3, help="Number of chunks to retrieve")

    args = parser.parse_args()

    app = RAGApplication()
    indexed_count = app.initialize(force_reindex=args.reindex)

    if args.interactive:
        run_interactive(app)
        return

    if args.question:
        result = app.query(args.question, role=args.role, top_k=args.top_k)
        print(f"\nQuestion: {result['question']}")
        print(f"Role: {result['role']}")
        print(f"\n{result['answer']}")
        return

    print(f"Demo RAG initialized successfully. Total chunks indexed: {indexed_count}")
    print("Run with a question: python demo-rag/main.py \"What is the travel policy?\"")
    print("Or start interactive mode: python demo-rag/main.py --interactive")


if __name__ == "__main__":
    main()
