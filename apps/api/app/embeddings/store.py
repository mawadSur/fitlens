"""Vector store abstraction. Default 'local' does cosine over embeddings held in
the relational rows. Pinecone/Weaviate/pgvector adapters activate when configured.

All third-party clients (pinecone, weaviate, psycopg, pgvector) are imported
LAZILY inside the relevant ``__init__`` so importing this module never requires
any of them to be installed."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..config import settings
from .base import cosine_similarity


@dataclass
class ScoredItem:
    id: int
    score: float


class LocalVectorStore:
    """Brute-force cosine ranking — fine for dev/MVP scale (thousands of rows)."""

    provider = "local"

    def rank(
        self, query: Sequence[float], candidates: list[tuple[int, Sequence[float] | None]]
    ) -> list[ScoredItem]:
        scored = [
            ScoredItem(cid, cosine_similarity(query, vec))
            for cid, vec in candidates
            if vec
        ]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored


class PineconeVectorStore:  # pragma: no cover - requires live account
    provider = "pinecone"

    def __init__(self) -> None:
        from pinecone import Pinecone  # type: ignore

        self._pc = Pinecone(api_key=settings.pinecone_api_key)
        self._index = self._pc.Index(settings.pinecone_index)

    def rank(self, query, candidates):  # noqa: ANN001
        res = self._index.query(vector=list(query), top_k=50, include_values=False)
        return [ScoredItem(int(m["id"]), float(m["score"])) for m in res.get("matches", [])]


class WeaviateVectorStore:  # pragma: no cover - requires live account
    provider = "weaviate"

    def __init__(self) -> None:
        import weaviate  # type: ignore
        from weaviate.classes.init import Auth  # type: ignore

        auth = Auth.api_key(settings.weaviate_api_key) if settings.weaviate_api_key else None
        self._client = weaviate.connect_to_weaviate_cloud(
            cluster_url=settings.weaviate_url,
            auth_credentials=auth,
        )
        self._collection = self._client.collections.get("FitlensItem")

    def rank(self, query, candidates):  # noqa: ANN001
        from weaviate.classes.query import MetadataQuery  # type: ignore

        res = self._collection.query.near_vector(
            near_vector=list(query),
            limit=50,
            return_metadata=MetadataQuery(distance=True),
        )
        out: list[ScoredItem] = []
        for obj in res.objects:
            # Weaviate returns cosine *distance* in [0, 2]; convert to similarity.
            distance = obj.metadata.distance if obj.metadata is not None else 0.0
            out.append(ScoredItem(int(obj.properties["item_id"]), 1.0 - float(distance)))
        return out


class PgVectorStore:  # pragma: no cover - requires a live pgvector database
    provider = "pgvector"

    def __init__(self) -> None:
        import psycopg  # type: ignore
        from pgvector.psycopg import register_vector  # type: ignore

        self._conn = psycopg.connect(settings.database_url)
        register_vector(self._conn)
        # Table name comes from trusted config; quote it defensively all the same.
        self._table = '"{}"'.format(settings.pgvector_table.replace('"', '""'))

    def rank(self, query, candidates):  # noqa: ANN001
        vec = list(query)
        sql = (
            f"SELECT item_id, 1 - (embedding <=> %s::vector) AS score "
            f"FROM {self._table} ORDER BY embedding <=> %s::vector LIMIT 50"
        )
        with self._conn.cursor() as cur:
            cur.execute(sql, (vec, vec))
            return [ScoredItem(int(row[0]), float(row[1])) for row in cur.fetchall()]


def get_vector_store():
    """Select a vector store from config. Selection is gated and never raises:
    a misconfigured provider falls back to the always-available LocalVectorStore."""
    provider = settings.vector_provider.lower()
    if provider == "pgvector" and _pgvector_available():
        return PgVectorStore()
    if provider == "weaviate" and settings.weaviate_url:
        return WeaviateVectorStore()
    if provider == "pinecone" and settings.pinecone_api_key:
        return PineconeVectorStore()
    return LocalVectorStore()


def _pgvector_available() -> bool:
    """pgvector needs a real (non-sqlite) DB url. SQLite can't run the adapter."""
    url = settings.database_url or ""
    return bool(url) and not url.startswith("sqlite")
