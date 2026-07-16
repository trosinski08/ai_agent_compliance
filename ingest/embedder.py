"""
Batch embedding generator using a Polish retrieval model.
mmlw-retrieval-roberta-large outputs 768-dim normalised vectors.
"""
from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from .chunker import Chunk


class Embedder:
    def __init__(self, model_name: str, batch_size: int = 32, device: str = "cpu"):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = batch_size
        # Read actual output dimension from the loaded model — avoids hardcode mismatch
        self.embedding_dim: int = self.model.get_sentence_embedding_dimension()

    def embed_chunks(self, chunks: list[Chunk]) -> np.ndarray:
        return self.embed_texts([c.text for c in chunks])

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        batches = []
        for i in tqdm(range(0, len(texts), self.batch_size), desc="Embedding"):
            vecs = self.model.encode(
                texts[i : i + self.batch_size],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            batches.append(vecs)
        return np.vstack(batches)

    def embed_query(self, query: str) -> list[float]:
        vec = self.model.encode([query], normalize_embeddings=True)[0]
        return vec.tolist()
