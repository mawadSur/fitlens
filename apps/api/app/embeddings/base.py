"""Embedder protocol + math utilities."""
from __future__ import annotations

from typing import Protocol, Sequence

import numpy as np

EMBED_DIM = 384  # all-MiniLM-L6-v2


class Embedder(Protocol):
    dim: int

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity in [-1, 1]; 0.0 when either vector is empty/zero."""
    va, vb = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    if va.size == 0 or vb.size == 0:
        return 0.0
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))
