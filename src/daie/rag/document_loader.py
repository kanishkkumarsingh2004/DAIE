"""
Document loader for RAG (Retrieval-Augmented Generation).

Loads TXT and PDF files from a directory for use by the RAG engine.
"""

import logging
import os
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A loaded document with its content and metadata."""

    content: str
    """The text content of the document."""

    source: str
    """The file path of the source document."""

    doc_type: str
    """The type of document (txt, pdf, etc.)."""


def _load_txt(file_path: str) -> str:
    """Load a plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _load_pdf(file_path: str) -> str:
    """Load a PDF file. Requires PyPDF2 to be installed."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except ImportError:
        logger.warning(f"PyPDF2 is not installed. Skipping PDF file: {file_path}. " "Install with: pip install PyPDF2")
        return ""
    except Exception as exc:
        logger.error(f"Error reading PDF '{file_path}': {exc}")
        return ""


# Mapping of file extensions to loader functions
_LOADERS = {
    ".txt": _load_txt,
    ".md": _load_txt,
    ".csv": _load_txt,
    ".json": _load_txt,
    ".yaml": _load_txt,
    ".yml": _load_txt,
    ".pdf": _load_pdf,
}


def load_directory(directory_path: str) -> List[Document]:
    """
    Load all supported documents from a directory (non-recursive).

    Supported formats: .txt, .md, .csv, .json, .yaml, .yml, .pdf

    Args:
        directory_path: Path to the directory containing documents.

    Returns:
        List of Document objects with extracted text content.
    """
    if not os.path.isdir(directory_path):
        logger.error(f"Document directory does not exist: {directory_path}")
        return []

    documents: List[Document] = []

    for filename in sorted(os.listdir(directory_path)):
        file_path = os.path.join(directory_path, filename)
        if not os.path.isfile(file_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        loader = _LOADERS.get(ext)
        if loader is None:
            continue

        content = loader(file_path)
        if content and content.strip():
            documents.append(
                Document(
                    content=content.strip(),
                    source=file_path,
                    doc_type=ext.lstrip("."),
                )
            )
            logger.info(f"Loaded document: {filename} ({len(content)} chars)")

    logger.info(f"Loaded {len(documents)} document(s) from '{directory_path}'")
    return documents
