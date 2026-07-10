"""
Sentence-BERT embedding module with LRU caching for performance.
Uses `all-MiniLM-L6-v2` — fast, lightweight, strong semantic quality.
"""

import hashlib
from functools import lru_cache
from typing import Optional

import numpy as np

# Lazy-load to avoid slow startup
_model = None


def _get_model():
    """Lazy-load SentenceTransformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _hash_text(text: str) -> str:
    """Create a cache key from text content."""
    return hashlib.sha256(text.encode()).hexdigest()


# Cache up to 512 embedding results to avoid recomputing
_embedding_cache: dict[str, np.ndarray] = {}
_MAX_CACHE_SIZE = 512


def get_embedding(text: str) -> np.ndarray:
    """
    Compute sentence embedding for a text string.
    Uses in-memory cache to avoid recomputing embeddings for same text.

    Args:
        text: Input text (will be truncated to 512 tokens internally by SBERT)

    Returns:
        1D numpy array of shape (384,) for MiniLM-L6-v2
    """
    if not text or not text.strip():
        # Return zero vector for empty text
        return np.zeros(384, dtype=np.float32)

    cache_key = _hash_text(text[:2000])  # Hash first 2k chars for cache key

    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]

    model = _get_model()
    # Truncate to reasonable length to keep inference fast
    truncated = text[:4000]
    embedding = model.encode(truncated, normalize_embeddings=True, show_progress_bar=False)

    # Manage cache size
    if len(_embedding_cache) >= _MAX_CACHE_SIZE:
        # Remove oldest entry (FIFO)
        oldest_key = next(iter(_embedding_cache))
        del _embedding_cache[oldest_key]

    _embedding_cache[cache_key] = embedding
    return embedding


def get_batch_embeddings(texts: list[str]) -> list[np.ndarray]:
    """
    Compute embeddings for a batch of texts efficiently.

    Args:
        texts: List of text strings

    Returns:
        List of 1D numpy arrays
    """
    if not texts:
        return []

    model = _get_model()
    truncated = [t[:4000] for t in texts]
    embeddings = model.encode(truncated, normalize_embeddings=True, show_progress_bar=False, batch_size=32)
    return [emb for emb in embeddings]


def clear_cache() -> None:
    """Clear the embedding cache (useful for testing)."""
    _embedding_cache.clear()
