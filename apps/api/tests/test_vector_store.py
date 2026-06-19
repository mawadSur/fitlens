"""Unit tests for the vector-store layer. All must pass fully offline — no
pgvector/weaviate/psycopg/pinecone installed, no network, no live accounts."""
import importlib

import pytest

from app.config import settings
from app.embeddings.store import LocalVectorStore, ScoredItem, get_vector_store


# ─── LocalVectorStore.rank ──────────────────────────────────────────────────────

def test_rank_sorts_by_descending_score():
    store = LocalVectorStore()
    query = [1.0, 0.0, 0.0]
    candidates = [
        (1, [0.0, 1.0, 0.0]),  # orthogonal -> ~0.0
        (2, [1.0, 0.0, 0.0]),  # identical  -> ~1.0
        (3, [1.0, 1.0, 0.0]),  # 45 degrees -> ~0.707
    ]
    ranked = store.rank(query, candidates)

    assert [item.id for item in ranked] == [2, 3, 1]
    scores = [item.score for item in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_skips_none_and_empty_vectors():
    store = LocalVectorStore()
    query = [1.0, 0.0, 0.0]
    candidates = [
        (1, [1.0, 0.0, 0.0]),
        (2, None),
        (3, []),
    ]
    ranked = store.rank(query, candidates)

    assert [item.id for item in ranked] == [1]


def test_rank_identical_vectors_score_near_one():
    store = LocalVectorStore()
    query = [0.3, 0.6, 0.9]
    ranked = store.rank(query, [(7, [0.3, 0.6, 0.9])])

    assert len(ranked) == 1
    assert isinstance(ranked[0], ScoredItem)
    assert ranked[0].score == pytest.approx(1.0, abs=1e-6)


def test_rank_empty_candidates_returns_empty_list():
    assert LocalVectorStore().rank([1.0, 0.0], []) == []


# ─── get_vector_store selection (gated, never crashes) ──────────────────────────

def test_get_vector_store_returns_local_for_local_provider(monkeypatch):
    monkeypatch.setattr(settings, "vector_provider", "local")
    assert isinstance(get_vector_store(), LocalVectorStore)


def test_get_vector_store_pgvector_without_db_falls_back_to_local(monkeypatch):
    # pgvector selected but DB is sqlite (the test DB) -> gated, falls back.
    monkeypatch.setattr(settings, "vector_provider", "pgvector")
    monkeypatch.setattr(settings, "database_url", "sqlite:///./.fitlens.db")
    assert isinstance(get_vector_store(), LocalVectorStore)


def test_get_vector_store_pgvector_with_empty_db_falls_back_to_local(monkeypatch):
    monkeypatch.setattr(settings, "vector_provider", "pgvector")
    monkeypatch.setattr(settings, "database_url", "")
    assert isinstance(get_vector_store(), LocalVectorStore)


def test_get_vector_store_weaviate_without_url_falls_back_to_local(monkeypatch):
    monkeypatch.setattr(settings, "vector_provider", "weaviate")
    monkeypatch.setattr(settings, "weaviate_url", "")
    assert isinstance(get_vector_store(), LocalVectorStore)


def test_get_vector_store_pinecone_without_key_falls_back_to_local(monkeypatch):
    monkeypatch.setattr(settings, "vector_provider", "pinecone")
    monkeypatch.setattr(settings, "pinecone_api_key", "")
    assert isinstance(get_vector_store(), LocalVectorStore)


def test_get_vector_store_unknown_provider_falls_back_to_local(monkeypatch):
    monkeypatch.setattr(settings, "vector_provider", "nonsense")
    assert isinstance(get_vector_store(), LocalVectorStore)


# ─── lazy imports: module is importable without optional backends ───────────────

def test_importing_store_requires_no_optional_backends():
    """Importing the module must not pull in pgvector/weaviate/psycopg."""
    import sys

    # Re-import fresh and confirm none of the heavy optional deps got imported
    # as a side effect of importing app.embeddings.store.
    importlib.reload(importlib.import_module("app.embeddings.store"))
    for mod in ("pgvector", "weaviate", "psycopg", "psycopg2", "pinecone"):
        assert mod not in sys.modules or sys.modules[mod] is None, (
            f"{mod} was imported at module load time; it must stay lazy"
        )
