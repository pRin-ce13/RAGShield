"""Document loader for demo-rag.

Reads synthetic documents from disk and extracts text along with security metadata.
"""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Dict, List, Optional


@dataclass
class Document:
    """Represents a loaded raw document before chunking."""
    doc_id: str
    filename: str
    content: str
    classification: str = "PUBLIC"
    security_tag: str = "GENERAL"
    metadata: Dict[str, str] = field(default_factory=dict)


def _extract_header_metadata(content: str) -> Dict[str, str]:
    """Helper to parse Classification and Security Tag from initial document headers."""
    extracted = {
        "classification": "PUBLIC",
        "security_tag": "GENERAL"
    }
    
    # Check for 'Classification: <VALUE>'
    class_match = re.search(r"Classification:\s*([^\r\n]+)", content, re.IGNORECASE)
    if class_match:
        extracted["classification"] = class_match.group(1).strip()

    # Check for 'Security Tag: <VALUE>'
    tag_match = re.search(r"Security Tag:\s*([^\r\n]+)", content, re.IGNORECASE)
    if tag_match:
        extracted["security_tag"] = tag_match.group(1).strip()

    return extracted


def load_single_document(file_path: Path) -> Document:
    """Loads a single document file from disk and parses its metadata.
    
    Args:
        file_path: Path to the document.
        
    Returns:
        Document instance populated with content and metadata.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Document file not found: {file_path}")

    # Read UTF-8 text safely
    content = path.read_text(encoding="utf-8")
    header_meta = _extract_header_metadata(content)

    doc_id = path.stem.lower()

    return Document(
        doc_id=doc_id,
        filename=path.name,
        content=content,
        classification=header_meta["classification"],
        security_tag=header_meta["security_tag"],
        metadata={
            "source_path": str(path.resolve()),
            "file_size_bytes": str(len(content.encode("utf-8")))
        }
    )


def load_documents_from_directory(directory_path: Path) -> List[Document]:
    """Loads all supported documents (.txt, .md) from a directory.
    
    Args:
        directory_path: Directory path to scan.
        
    Returns:
        List of loaded Document objects.
    """
    dir_path = Path(directory_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {directory_path}")

    documents: List[Document] = []
    # Collect .txt and .md files
    for file_path in sorted(dir_path.glob("*")):
        if file_path.suffix.lower() in [".txt", ".md"] and file_path.is_file():
            documents.append(load_single_document(file_path))

    return documents
