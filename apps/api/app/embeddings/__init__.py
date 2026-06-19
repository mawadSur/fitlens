"""Embedding + vector-search layer."""
from .base import cosine_similarity
from .local import embed_text, embed_texts, get_embedder
from .store import get_vector_store

__all__ = [
    "cosine_similarity",
    "embed_text",
    "embed_texts",
    "get_embedder",
    "get_vector_store",
]
