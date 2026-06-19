"""Local embedder: ONNX all-MiniLM-L6-v2 via fastembed, with a deterministic
hashing fallback so the platform always runs (offline / no model download / low disk)."""
from __future__ import annotations

import hashlib
import re
from functools import lru_cache
from typing import Sequence

import numpy as np

from .base import EMBED_DIM, Embedder

_TOKEN_RE = re.compile(r"[a-zA-Z0-9+#.]+")


class HashingEmbedder:
    """Deterministic bag-of-words hashed into EMBED_DIM, L2-normalized.

    Not semantically rich, but stable and dependency-free — guarantees the
    matching pipeline works without network or heavy ML libraries.
    """

    backend = "hashing-fallback"
    dim = EMBED_DIM

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float32)
            tokens = _TOKEN_RE.findall((text or "").lower())
            for tok in tokens:
                h = int.from_bytes(hashlib.md5(tok.encode()).digest()[:4], "little")
                vec[h % self.dim] += 1.0
                # a second hashed slot adds a little signal/robustness
                vec[(h >> 8) % self.dim] += 0.5
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            out.append(vec.tolist())
        return out


class FastEmbedEmbedder:
    """ONNX all-MiniLM-L6-v2 (384d) via fastembed — no torch required."""

    backend = "onnx-all-MiniLM-L6-v2"
    dim = EMBED_DIM

    def __init__(self) -> None:
        from fastembed import TextEmbedding  # imported lazily

        self._model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [v.tolist() for v in self._model.embed(list(texts))]


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Prefer real ONNX embeddings; degrade gracefully to the hashing fallback."""
    try:
        emb = FastEmbedEmbedder()
        emb.embed(["warmup"])  # force model load now so failures surface here
        return emb
    except Exception:  # noqa: BLE001 — any import/download/runtime issue => fallback
        return HashingEmbedder()


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    return get_embedder().embed(texts)


def embed_text(text: str) -> list[float]:
    return get_embedder().embed([text])[0]
