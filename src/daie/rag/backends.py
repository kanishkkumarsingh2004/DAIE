"""
Pluggable RAG retrieval backends.

Provides multiple backends for indexing and searching document chunks:
- TFIDFBackend: Pure numpy TF-IDF with cosine similarity (no external deps)
- ChromaBackend: ChromaDB with sentence-transformers embeddings
- FAISSBackend: FAISS vector index with sentence-transformers embeddings
"""

import logging
import math
import os
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from daie.rag.chunking import Chunk

logger = logging.getLogger(__name__)


class RAGBackend(ABC):
    """Abstract base class for RAG retrieval backends."""

    @abstractmethod
    def index(self, chunks: List[Chunk]) -> None:
        """
        Index a list of chunks for later retrieval.

        Args:
            chunks: List of Chunk objects to index.
        """

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Chunk, float]]:
        """
        Search indexed chunks for the most relevant matches.

        Args:
            query: The search query.
            top_k: Number of top results to return.
            filters: Optional metadata filters (e.g., {"source": "*.pdf"}).

        Returns:
            List of (Chunk, similarity_score) tuples, highest first.
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear all indexed data."""

    def _apply_metadata_filters(
        self,
        results: List[Tuple[Chunk, float]],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[Chunk, float]]:
        """
        Apply metadata filters to search results.

        Supports:
        - Exact match: {"key": "value"}
        - Glob pattern on source: {"source": "*.pdf"}
        """
        if not filters:
            return results

        import fnmatch

        filtered = []
        for chunk, score in results:
            match = True
            for key, value in filters.items():
                chunk_value = chunk.metadata.get(key)
                if chunk_value is None:
                    # Also check direct attributes
                    chunk_value = getattr(chunk, key, None)

                if chunk_value is None:
                    match = False
                    break

                # Glob matching for source paths
                if key == "source" and isinstance(value, str) and ("*" in value or "?" in value):
                    if not fnmatch.fnmatch(str(chunk_value), value):
                        match = False
                        break
                elif str(chunk_value) != str(value):
                    match = False
                    break

            if match:
                filtered.append((chunk, score))

        return filtered


# ──────────────────────────────────────────────────────────────────────────────
# TF-IDF Backend
# ──────────────────────────────────────────────────────────────────────────────


class TFIDFBackend(RAGBackend):
    """
    TF-IDF retrieval backend using only numpy.

    Fast, lightweight, zero external ML dependencies.
    Best for small to medium document collections.
    """

    _STOP_WORDS = {
        "a",
        "an",
        "the",
        "is",
        "it",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "and",
        "or",
        "but",
        "not",
        "with",
        "by",
        "from",
        "as",
        "this",
        "that",
        "be",
        "are",
        "was",
        "were",
        "been",
        "has",
        "have",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "can",
        "i",
        "you",
        "he",
        "she",
        "we",
        "they",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "what",
        "where",
        "how",
        "when",
        "why",
        "who",
        "which",
    }

    def __init__(self):
        self._chunks: List[Chunk] = []
        self._vocabulary: Dict[str, int] = {}
        self._idf: Optional[np.ndarray] = None
        self._tfidf_matrix: Optional[np.ndarray] = None

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer with lowercasing."""
        text = text.lower()
        tokens = re.findall(r"[a-z0-9]+", text)
        return [t for t in tokens if len(t) > 1 and t not in TFIDFBackend._STOP_WORDS]

    def index(self, chunks: List[Chunk]) -> None:
        self._chunks = chunks

        if not chunks:
            return

        # Build vocabulary
        vocab: Dict[str, int] = {}
        chunk_token_lists: List[List[str]] = []

        for chunk in chunks:
            tokens = self._tokenize(chunk.text)
            chunk_token_lists.append(tokens)
            for token in set(tokens):
                if token not in vocab:
                    vocab[token] = len(vocab)

        self._vocabulary = vocab
        vocab_size = len(vocab)
        num_chunks = len(chunks)

        if vocab_size == 0:
            self._tfidf_matrix = np.zeros((num_chunks, 1))
            self._idf = np.zeros(1)
            return

        # IDF: log(N / df) smoothed
        df = np.zeros(vocab_size)
        for tokens in chunk_token_lists:
            for token in set(tokens):
                if token in vocab:
                    df[vocab[token]] += 1

        self._idf = np.log((num_chunks + 1) / (df + 1)) + 1

        # TF-IDF matrix
        self._tfidf_matrix = np.zeros((num_chunks, vocab_size))
        for i, tokens in enumerate(chunk_token_lists):
            if not tokens:
                continue
            tf = Counter(tokens)
            for token, count in tf.items():
                if token in vocab:
                    j = vocab[token]
                    self._tfidf_matrix[i, j] = math.log(1 + count) * self._idf[j]

        logger.info(f"TF-IDF index built: {num_chunks} chunks, {vocab_size} terms")

    def search(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Chunk, float]]:
        if self._tfidf_matrix is None or not self._chunks:
            return []

        query_vec = self._text_to_tfidf(query)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        chunk_norms = np.linalg.norm(self._tfidf_matrix, axis=1)
        chunk_norms = np.where(chunk_norms == 0, 1.0, chunk_norms)
        similarities = self._tfidf_matrix.dot(query_vec) / (chunk_norms * query_norm)

        # Get ALL indices sorted, we'll filter after
        top_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.05:
                results.append((self._chunks[idx], score))
            if len(results) >= top_k * 3:  # Over-fetch for filtering
                break

        results = self._apply_metadata_filters(results, filters)
        return results[:top_k]

    def _text_to_tfidf(self, text: str) -> np.ndarray:
        vocab_size = len(self._vocabulary)
        if vocab_size == 0:
            return np.zeros(1)

        vec = np.zeros(vocab_size)
        tokens = self._tokenize(text)
        tf = Counter(tokens)

        for token, count in tf.items():
            if token in self._vocabulary:
                j = self._vocabulary[token]
                vec[j] = math.log(1 + count) * self._idf[j]

        return vec

    def clear(self) -> None:
        self._chunks = []
        self._vocabulary = {}
        self._idf = None
        self._tfidf_matrix = None


# ──────────────────────────────────────────────────────────────────────────────
# ChromaDB Backend
# ──────────────────────────────────────────────────────────────────────────────


class ChromaBackend(RAGBackend):
    """
    ChromaDB retrieval backend with sentence-transformers embeddings.

    Provides semantic search with persistent storage.
    Requires: chromadb, sentence-transformers
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: Optional[str] = None,
        persist_directory: Optional[str] = None,
    ):
        self.embedding_model_name = embedding_model
        self.collection_name = collection_name or "daie_rag"
        self.persist_directory = persist_directory
        self._chunks: List[Chunk] = []
        self._collection = None
        self._embedding_model = None
        self._client = None

    def _init_deps(self):
        """Lazy-init chromadb and sentence-transformers."""
        if self._embedding_model is not None:
            return

        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise ImportError("ChromaDB not installed. Install with: pip install chromadb")

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        self._embedding_model = SentenceTransformer(self.embedding_model_name)

        if self.persist_directory:
            os.makedirs(self.persist_directory, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )
        else:
            self._client = chromadb.Client(Settings(anonymized_telemetry=False))

        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def index(self, chunks: List[Chunk]) -> None:
        self._init_deps()
        self._chunks = chunks

        if not chunks or self._collection is None:
            return

        # Skip if already indexed
        if self._collection.count() > 0:
            logger.info(
                f"ChromaDB collection already has {self._collection.count()} docs, skipping"
            )
            return

        ids = [f"chunk_{i}" for i in range(len(chunks))]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self._embedding_model.encode(documents, show_progress_bar=True)
        embeddings_list = embeddings.tolist()

        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings_list,
            metadatas=metadatas,
        )
        logger.info(f"Indexed {len(chunks)} chunks in ChromaDB")

    def search(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Chunk, float]]:
        self._init_deps()

        if not self._chunks or self._collection is None:
            return []

        query_embedding = self._embedding_model.encode([query])[0].tolist()

        # Build ChromaDB where filter if metadata filters provided
        where_filter = None
        if filters:
            # ChromaDB supports direct metadata filtering
            simple_filters = {
                k: v
                for k, v in filters.items()
                if isinstance(v, str) and "*" not in v and "?" not in v
            }
            if simple_filters:
                if len(simple_filters) == 1:
                    key, val = next(iter(simple_filters.items()))
                    where_filter = {key: val}
                else:
                    where_filter = {"$and": [{k: v} for k, v in simple_filters.items()]}

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
            )
        except Exception as e:
            logger.warning(f"ChromaDB query with filter failed, retrying without: {e}")
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

        chunks_with_scores = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                chunk_idx = int(doc_id.split("_")[-1])
                if 0 <= chunk_idx < len(self._chunks):
                    chunk = self._chunks[chunk_idx]
                    distance = results["distances"][0][i] if results["distances"] else 0
                    similarity = 1.0 - distance
                    chunks_with_scores.append((chunk, similarity))

        # Apply glob-style filters that ChromaDB can't handle natively
        if filters:
            glob_filters = {
                k: v for k, v in filters.items() if isinstance(v, str) and ("*" in v or "?" in v)
            }
            if glob_filters:
                chunks_with_scores = self._apply_metadata_filters(chunks_with_scores, glob_filters)

        return chunks_with_scores

    def clear(self) -> None:
        if self._collection is not None:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as e:
                logger.error(f"Failed to clear ChromaDB: {e}")
        self._chunks = []


# ──────────────────────────────────────────────────────────────────────────────
# FAISS Backend
# ──────────────────────────────────────────────────────────────────────────────


class FAISSBackend(RAGBackend):
    """
    FAISS retrieval backend with sentence-transformers embeddings.

    Excellent for large-scale vector similarity search.
    Metadata filtering is applied post-search.
    Requires: faiss-cpu, sentence-transformers
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        index_type: str = "flat",
    ):
        self.embedding_model_name = embedding_model
        self.index_type = index_type
        self._chunks: List[Chunk] = []
        self._embedding_model = None
        self._index = None
        self._dimension: Optional[int] = None

    def _init_deps(self):
        """Lazy-init faiss and sentence-transformers."""
        if self._embedding_model is not None:
            return

        try:
            import faiss  # noqa: F401
        except ImportError:
            raise ImportError("faiss-cpu not installed. Install with: pip install faiss-cpu")

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        self._embedding_model = SentenceTransformer(self.embedding_model_name)

    def index(self, chunks: List[Chunk]) -> None:
        import faiss

        self._init_deps()
        self._chunks = chunks

        if not chunks:
            return

        logger.info(f"Generating FAISS embeddings for {len(chunks)} chunks...")
        texts = [c.text for c in chunks]
        embeddings = self._embedding_model.encode(texts, show_progress_bar=True)
        embeddings = np.array(embeddings, dtype=np.float32)

        self._dimension = embeddings.shape[1]

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)

        if self.index_type == "flat":
            self._index = faiss.IndexFlatIP(self._dimension)
        elif self.index_type == "ivf":
            nlist = min(100, len(chunks))
            quantizer = faiss.IndexFlatIP(self._dimension)
            self._index = faiss.IndexIVFFlat(quantizer, self._dimension, nlist)
            self._index.train(embeddings)
        else:
            self._index = faiss.IndexFlatIP(self._dimension)

        self._index.add(embeddings)
        logger.info(f"FAISS index built: {self._index.ntotal} vectors, dim={self._dimension}")

    def search(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Chunk, float]]:
        import faiss

        self._init_deps()

        if self._index is None or not self._chunks:
            return []

        query_embedding = self._embedding_model.encode([query])
        query_embedding = np.array(query_embedding, dtype=np.float32)
        faiss.normalize_L2(query_embedding)

        # Over-fetch if we have filters to apply
        fetch_k = top_k * 3 if filters else top_k
        scores, indices = self._index.search(query_embedding, min(fetch_k, len(self._chunks)))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue
            score = float(scores[0][i])
            if score > 0.05:
                results.append((self._chunks[idx], score))

        results = self._apply_metadata_filters(results, filters)
        return results[:top_k]

    def clear(self) -> None:
        self._chunks = []
        self._index = None
        self._dimension = None


# ── Factory ───────────────────────────────────────────────────────────────────

_BACKEND_REGISTRY = {
    "tfidf": TFIDFBackend,
    "chroma": ChromaBackend,
    "faiss": FAISSBackend,
}


def create_backend(
    backend: str = "tfidf",
    **kwargs,
) -> RAGBackend:
    """
    Factory function to create a RAG backend.

    Args:
        backend: One of "tfidf", "chroma", "faiss".
        **kwargs: Backend-specific configuration.

    Returns:
        A RAGBackend instance.
    """
    cls = _BACKEND_REGISTRY.get(backend)
    if cls is None:
        raise ValueError(
            f"Unknown RAG backend '{backend}'. " f"Available: {list(_BACKEND_REGISTRY.keys())}"
        )

    if backend == "tfidf":
        return cls()
    elif backend == "chroma":
        return cls(
            embedding_model=kwargs.get("embedding_model", "all-MiniLM-L6-v2"),
            collection_name=kwargs.get("collection_name"),
            persist_directory=kwargs.get("persist_directory"),
        )
    elif backend == "faiss":
        return cls(
            embedding_model=kwargs.get("embedding_model", "all-MiniLM-L6-v2"),
            index_type=kwargs.get("index_type", "flat"),
        )
    return cls()
