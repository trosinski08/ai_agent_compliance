"""
Singleton wrappers for the embedder and vector store so they are loaded
once per process (heavy model + network connection).
"""
from __future__ import annotations

from ingest.embedder import Embedder
from ingest.store import VectorStore
from config import settings

_embedder: Embedder | None = None
_store: VectorStore | None = None


def _get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder(settings.embedding_model)
    return _embedder


def _get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(collection_name=settings.qdrant_collection, path=settings.qdrant_path)
    return _store


def retrieve(
    query: str,
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> list[dict]:
    """Embed query and return top-k relevant legal chunks from Qdrant."""
    vec = _get_embedder().embed_query(query)
    return _get_store().search(
        query_vector=vec,
        top_k=top_k or settings.retrieval_top_k,
        score_threshold=score_threshold or settings.retrieval_score_threshold,
    )
