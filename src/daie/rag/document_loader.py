"""
Document loader for RAG (Retrieval-Augmented Generation).

Loads TXT, PDF, HTML, and other text-based files from a directory
for use by the RAG engine.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

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

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the document."""


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
        logger.warning(
            f"PyPDF2 is not installed. Skipping PDF file: {file_path}. "
            "Install with: pip install PyPDF2"
        )
        return ""
    except Exception as exc:
        logger.error(f"Error reading PDF '{file_path}': {exc}")
        return ""


def _load_html(file_path: str) -> str:
    """Load an HTML file, stripping tags."""
    import re

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()

    # Strip HTML tags
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# Mapping of file extensions to loader functions
_LOADERS: Dict[str, Callable[[str], str]] = {
    ".txt": _load_txt,
    ".md": _load_txt,
    ".csv": _load_txt,
    ".json": _load_txt,
    ".yaml": _load_txt,
    ".yml": _load_txt,
    ".pdf": _load_pdf,
    ".html": _load_html,
    ".htm": _load_html,
    ".rst": _load_txt,
    ".py": _load_txt,
    ".log": _load_txt,
    ".xml": _load_txt,
    ".toml": _load_txt,
    ".ini": _load_txt,
    ".cfg": _load_txt,
}


def _get_file_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a file."""
    stat = os.stat(file_path)
    return {
        "file_size": stat.st_size,
        "created_at": stat.st_ctime,
        "modified_at": stat.st_mtime,
        "filename": os.path.basename(file_path),
        "extension": os.path.splitext(file_path)[1].lower(),
    }


def load_directory(
    directory_path: str,
    recursive: bool = False,
) -> List[Document]:
    """
    Load all supported documents from a directory.

    Supported formats: .txt, .md, .csv, .json, .yaml, .yml, .pdf,
    .html, .htm, .rst, .py, .log, .xml, .toml, .ini, .cfg

    Args:
        directory_path: Path to the directory containing documents.
        recursive: If True, also load from subdirectories.

    Returns:
        List of Document objects with extracted text content.
    """
    if not os.path.isdir(directory_path):
        logger.error(f"Document directory does not exist: {directory_path}")
        return []

    documents: List[Document] = []

    if recursive:
        file_paths = []
        for root, _dirs, files in os.walk(directory_path):
            for filename in sorted(files):
                file_paths.append(os.path.join(root, filename))
        file_paths.sort()
    else:
        file_paths = [
            os.path.join(directory_path, f)
            for f in sorted(os.listdir(directory_path))
        ]

    for file_path in file_paths:
        if not os.path.isfile(file_path):
            continue

        ext = os.path.splitext(file_path)[1].lower()
        loader = _LOADERS.get(ext)
        if loader is None:
            continue

        try:
            content = loader(file_path)
        except Exception as e:
            logger.error(f"Error loading '{file_path}': {e}")
            continue

        if content and content.strip():
            metadata = _get_file_metadata(file_path)
            documents.append(
                Document(
                    content=content.strip(),
                    source=file_path,
                    doc_type=ext.lstrip("."),
                    metadata=metadata,
                )
            )
            logger.info(f"Loaded document: {os.path.basename(file_path)} ({len(content)} chars)")

    logger.info(f"Loaded {len(documents)} document(s) from '{directory_path}'")
    return documents
