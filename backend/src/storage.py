"""
Dual vector store: FAISS (semantic) + BM25 (lexical).

Inspired by Project Intel Core's production architecture where no single
retrieval method covers all query types:
  - FAISS/semantic misses exact terminology and rare tokens
  - BM25 misses paraphrases and conceptual queries
Running both and fusing results yields the best of both worlds.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field

import numpy as np
import faiss
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    id: int
    text: str
    source: str
    token_count: int
    metadata: dict = field(default_factory=dict)


# ── FAISS Store ───────────────────────────────────────────────────────────────

class FAISSStore:
    """
    Semantic vector store using FAISS IndexFlatIP.

    Cosine similarity is computed via inner product on L2-normalized vectors
    (mathematically equivalent, but faster — no division needed at query time).
    """

    def __init__(self, dim: int) -> None:
        self.dim = dim
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(dim)
        self._chunks: list[Chunk] = []

    def add(self, chunks: list[Chunk], embeddings: np.ndarray) -> None:
        assert embeddings.shape == (len(chunks), self.dim), (
            f"Shape mismatch: expected ({len(chunks)}, {self.dim}), got {embeddings.shape}"
        )
        self.index.add(embeddings.astype(np.float32))
        self._chunks.extend(chunks)
        logger.debug("FAISSStore: +%d chunks (total %d)", len(chunks), len(self._chunks))

    def search(self, query_embedding: np.ndarray, k: int) -> list[tuple[Chunk, float]]:
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        k = min(k, len(self._chunks))
        if k == 0:
            return []
        scores, indices = self.index.search(query_embedding.astype(np.float32), k)
        return [
            (self._chunks[idx], float(score))
            for score, idx in zip(scores[0], indices[0])
            if idx >= 0
        ]

    @property
    def size(self) -> int:
        return len(self._chunks)

    @property
    def chunks(self) -> list[Chunk]:
        return list(self._chunks)


# ── BM25 Store ────────────────────────────────────────────────────────────────

class BM25Store:
    """
    Lexical retrieval using BM25Okapi.

    Complements FAISS by capturing exact terminology, technical acronyms,
    version strings, and rare tokens that semantic search may not surface.
    Rebuilt in-memory on every add() call (acceptable for corpus size).
    """

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._index: BM25Okapi | None = None

    def add(self, chunks: list[Chunk]) -> None:
        self._chunks.extend(chunks)
        tokenized = [c.text.lower().split() for c in self._chunks]
        self._index = BM25Okapi(tokenized)
        logger.debug("BM25Store: rebuilt index with %d chunks", len(self._chunks))

    def search(self, query: str, k: int) -> list[tuple[Chunk, float]]:
        if self._index is None or not self._chunks:
            return []
        tokens = query.lower().split()
        scores: np.ndarray = self._index.get_scores(tokens)
        top_indices = np.argsort(scores)[::-1][:k]
        return [
            (self._chunks[i], float(scores[i]))
            for i in top_indices
            if scores[i] > 0.0
        ]

    @property
    def size(self) -> int:
        return len(self._chunks)


# ── Dual Store ────────────────────────────────────────────────────────────────

class DualVectorStore:
    """
    Composes FAISSStore and BM25Store.
    A single add() call populates both indexes simultaneously.
    """

    def __init__(self, dim: int) -> None:
        self.faiss = FAISSStore(dim)
        self.bm25 = BM25Store()

    def add(self, chunks: list[Chunk], embeddings: np.ndarray) -> None:
        self.faiss.add(chunks, embeddings)
        self.bm25.add(chunks)

    @property
    def size(self) -> int:
        return self.faiss.size

    @property
    def chunks(self) -> list[Chunk]:
        return self.faiss.chunks
