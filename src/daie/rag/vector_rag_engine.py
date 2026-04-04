"""
Vector RAG (Retrieval-Augmented Generation) Engine.

Provides document chunking, vector embeddings, and semantic search
using ChromaDB and sentence-transformers for high-quality retrieval.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from daie.rag.document_loader import Document, load_directory

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A chunk of text extracted from a document."""

    text: str
    """The text content of the chunk."""

    source: str
    """Source file path."""

    chunk_index: int
    """Index of this chunk within the source document."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata for the chunk."""


class VectorRAGEngine:
    """
    Vector-based Retrieval-Augmented Generation engine.

    Loads documents, chunks them, generates vector embeddings using
    sentence-transformers, and stores them in ChromaDB for semantic search.

    Example:
        >>> engine = VectorRAGEngine("/path/to/docs")
        >>> engine.load()
        >>> context = engine.build_context("What is DAIE?")
    """

    def __init__(
        self,
        document_path: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: Optional[str] = None,
        persist_directory: Optional[str] = None,
    ):
        """
        Args:
            document_path: Path to directory containing documents.
            chunk_size: Maximum number of characters per chunk.
            chunk_overlap: Number of overlapping characters between chunks.
            embedding_model: Name of sentence-transformers model to use.
            collection_name: Name for ChromaDB collection (auto-generated if None).
            persist_directory: Directory to persist ChromaDB data (default: .chroma in document_path).
        """
        self.document_path = document_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model_name = embedding_model

        # Auto-generate collection name from document path if not provided
        if collection_name is None:
            collection_name = os.path.basename(os.path.abspath(document_path))
        self.collection_name = collection_name

        # Set persist directory
        if persist_directory is None:
            persist_directory = os.path.join(document_path, ".chroma")
        self.persist_directory = persist_directory

        self._chunks: List[Chunk] = []
        self._collection = None
        self._embedding_model = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def num_chunks(self) -> int:
        return len(self._chunks)

    # ── public API ────────────────────────────────────────────────────────

    def load(self) -> int:
        """
        Load documents, chunk them, generate embeddings, and store in ChromaDB.

        Returns:
            Number of chunks created.
        """
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            logger.error("ChromaDB not installed. Install with: pip install chromadb")
            raise

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            logger.error(
                "sentence-transformers not installed. Install with: pip install sentence-transformers"
            )
            raise

        # Load documents
        documents = load_directory(self.document_path)
        if not documents:
            logger.warning(f"No documents found in '{self.document_path}'")
            self._loaded = True
            return 0

        # Chunk documents
        self._chunks = self._chunk_documents(documents)
        if not self._chunks:
            logger.warning("No chunks were created from documents")
            self._loaded = True
            return 0

        # Initialize embedding model
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self._embedding_model = SentenceTransformer(self.embedding_model_name)

        # Initialize ChromaDB
        os.makedirs(self.persist_directory, exist_ok=True)
        client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )

        # Get or create collection
        self._collection = client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

        # Generate embeddings and store in ChromaDB
        self._index_chunks()

        self._loaded = True
        logger.info(
            f"Vector RAG engine loaded: {len(documents)} doc(s), "
            f"{len(self._chunks)} chunk(s), "
            f"embedding model: {self.embedding_model_name}"
        )
        return len(self._chunks)

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[Chunk, float]]:
        """
        Retrieve the most relevant chunks for a query using semantic search.

        Args:
            query: The search query string.
            top_k: Number of top results to return.

        Returns:
            List of (Chunk, similarity_score) tuples, highest score first.
        """
        if not self._loaded or self._collection is None:
            logger.warning("Vector RAG engine not loaded. Call load() first.")
            return []

        if not self._chunks:
            return []

        # Generate query embedding
        query_embedding = self._embedding_model.encode([query])[0].tolist()

        # Query ChromaDB
        results = self._collection.query(query_embeddings=[query_embedding], n_results=top_k)

        # Convert results to Chunk objects with scores
        chunks_with_scores = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # Find the corresponding chunk
                chunk_idx = int(doc_id.split("_")[-1])
                if 0 <= chunk_idx < len(self._chunks):
                    chunk = self._chunks[chunk_idx]
                    # ChromaDB returns distances, convert to similarity
                    # For cosine similarity: 1 - distance
                    distance = results["distances"][0][i] if results["distances"] else 0
                    similarity = 1.0 - distance
                    chunks_with_scores.append((chunk, similarity))

        return chunks_with_scores

    def build_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve relevant chunks and format them as a context string
        suitable for injection into an LLM prompt.

        Args:
            query: The user's query.
            top_k: Number of chunks to include.

        Returns:
            Formatted context string, or empty string if no matches.
        """
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""

        context_parts = []
        for i, (chunk, score) in enumerate(results, 1):
            context_parts.append(f"[Document {i}: {chunk.source}]\n{chunk.text}")

        return "\n\n".join(context_parts)

    # ── chunking ──────────────────────────────────────────────────────────

    def _chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        """Split documents into overlapping chunks."""
        chunks: List[Chunk] = []

        for doc in documents:
            text = doc.content
            if len(text) <= self.chunk_size:
                chunks.append(
                    Chunk(
                        text=text, source=doc.source, chunk_index=0, metadata={"source": doc.source}
                    )
                )
                continue

            start = 0
            chunk_idx = 0
            while start < len(text):
                end = start + self.chunk_size

                # Try to break at a sentence or paragraph boundary
                if end < len(text):
                    # Look for paragraph break
                    para_break = text.rfind("\n\n", start, end)
                    if para_break > start + self.chunk_size // 2:
                        end = para_break + 2
                    else:
                        # Look for sentence break
                        sent_break = text.rfind(". ", start, end)
                        if sent_break > start + self.chunk_size // 2:
                            end = sent_break + 2

                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append(
                        Chunk(
                            text=chunk_text,
                            source=doc.source,
                            chunk_index=chunk_idx,
                            metadata={"source": doc.source, "chunk_index": chunk_idx},
                        )
                    )
                    chunk_idx += 1

                start = end - self.chunk_overlap
                if start >= len(text):
                    break

        return chunks

    # ── indexing ──────────────────────────────────────────────────────────

    def _index_chunks(self) -> None:
        """Generate embeddings for chunks and store in ChromaDB."""
        if not self._chunks or self._collection is None:
            return

        # Check if collection already has data
        count = self._collection.count()
        if count > 0:
            logger.info(f"Collection already has {count} documents, skipping indexing")
            return

        # Prepare data for ChromaDB
        ids = [f"chunk_{i}" for i in range(len(self._chunks))]
        documents = [chunk.text for chunk in self._chunks]
        metadatas = [chunk.metadata for chunk in self._chunks]

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(self._chunks)} chunks...")
        embeddings = self._embedding_model.encode(documents, show_progress_bar=True)
        embeddings_list = embeddings.tolist()

        # Store in ChromaDB
        self._collection.add(
            ids=ids, documents=documents, embeddings=embeddings_list, metadatas=metadatas
        )

        logger.info(f"Indexed {len(self._chunks)} chunks in ChromaDB")

    def clear(self) -> None:
        """Clear all indexed data."""
        if self._collection is not None:
            try:
                self._collection.delete(where={})
                logger.info("Cleared vector RAG index")
            except Exception as e:
                logger.error(f"Failed to clear index: {e}")

        self._chunks = []
        self._loaded = False
