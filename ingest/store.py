"""
Qdrant operations: create collection, upsert chunks, similarity search.
"""
from __future__ import annotations

import uuid

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from .chunker import Chunk

_BATCH = 100


class VectorStore:
    def __init__(self, collection_name: str, path: str | None = None, url: str | None = None):
        # Local file mode (no Docker) takes priority over server URL.
        # qdrant-client persists data to `path` between runs.
        if path:
            self.client = QdrantClient(path=path)
        else:
            self.client = QdrantClient(url=url)
        self.collection = collection_name

    def ensure_collection(self, embedding_dim: int) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
            )
            print(f"Created Qdrant collection: {self.collection} (dim={embedding_dim})")
        else:
            # Verify existing collection matches the model's dimension
            info = self.client.get_collection(self.collection)
            existing_dim = info.config.params.vectors.size
            if existing_dim != embedding_dim:
                print(f"  Dimension mismatch: collection={existing_dim}, model={embedding_dim}")
                print(f"  Recreating collection with dim={embedding_dim}")
                self.client.delete_collection(self.collection)
                self.client.create_collection(
                    collection_name=self.collection,
                    vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
                )
                print(f"  Recreated: {self.collection} (dim={embedding_dim})")
            else:
                print(f"Qdrant collection OK: {self.collection} (dim={existing_dim})")

    def upsert(self, chunks: list[Chunk], embeddings: np.ndarray) -> int:
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec.tolist(),
                payload={
                    "text": chunk.text,
                    "source": chunk.source,
                    "law_name": chunk.law_name,
                    "article_ref": chunk.article_ref,
                    "chunk_index": chunk.chunk_index,
                },
            )
            for chunk, vec in zip(chunks, embeddings)
        ]
        for i in range(0, len(points), _BATCH):
            self.client.upsert(
                collection_name=self.collection,
                points=points[i : i + _BATCH],
            )
        return len(points)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 6,
        score_threshold: float = 0.60,
        law_filter: str | None = None,
    ) -> list[dict]:
        query_filter = None
        if law_filter:
            query_filter = Filter(
                must=[FieldCondition(key="law_name", match=MatchValue(value=law_filter))]
            )

        # qdrant-client ≥1.9 uses query_points() instead of search()
        result = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True,
        )
        return [
            {
                "text": h.payload["text"],
                "law_name": h.payload.get("law_name", ""),
                "article_ref": h.payload.get("article_ref", ""),
                "source": h.payload.get("source", ""),
                "score": h.score,
            }
            for h in result.points
        ]

    def count(self) -> int:
        return self.client.get_collection(self.collection).points_count
