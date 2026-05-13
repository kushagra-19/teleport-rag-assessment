"""
Retrieval strategies: A (raw vector search) and B (AI-enhanced retrieval).

Strategy B is the core differentiator — it layers three production-grade
techniques (query expansion + BM25 + RRF + CrossEncoder reranker) on top
of basic FAISS search, inspired by the Project Intel Core production system.
"""

from __future__ import annotations
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sentence_transformers import CrossEncoder

from backend.src.storage import DualVectorStore, Chunk
from backend.src.embeddings import EmbeddingProvider
from backend.config.settings import (
    STRATEGY_A_TOP_K,
    STRATEGY_B_FAISS_K,
    STRATEGY_B_BM25_K,
    STRATEGY_B_RERANK_TOP_N,
    STRATEGY_B_FINAL_K,
    RRF_K,
    RERANKER_MODEL,
    RERANKER_MAX_LENGTH,
)

logger = logging.getLogger(__name__)


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class RetrievalResult:
    chunk: Chunk
    score: float
    rank: int
    strategy: str                                    # "A" or "B"
    expanded_query: Optional[str] = None            # None for Strategy A
    expansion_terms: list[str] = field(default_factory=list)
    retrieval_path: str = "faiss"                   # "faiss" | "bm25" | "rrf_fused"
    latency_ms: int = 0


# ── Abstract base ─────────────────────────────────────────────────────────────

class RetrievalStrategy(ABC):
    @abstractmethod
    def retrieve(self, query: str, k: int) -> list[RetrievalResult]: ...

    @property
    @abstractmethod
    def name(self) -> str: ...


# ── RRF fusion ────────────────────────────────────────────────────────────────

def rrf_fuse(
    list_a: list[tuple[Chunk, float]],
    list_b: list[tuple[Chunk, float]],
    k: int = RRF_K,
) -> list[tuple[Chunk, float]]:
    """
    Reciprocal Rank Fusion.

        score(doc) = Σ  1 / (k + rank_in_list_i)

    Documents that rank highly in both FAISS and BM25 are boosted to the top.
    This is parameter-robust and avoids the score-scale mismatch between
    cosine similarity and BM25 relevance scores.
    """
    scores: dict[int, float] = {}
    chunk_map: dict[int, Chunk] = {}

    for rank, (chunk, _) in enumerate(list_a, start=1):
        scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank)
        chunk_map[chunk.id] = chunk

    for rank, (chunk, _) in enumerate(list_b, start=1):
        scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank)
        chunk_map[chunk.id] = chunk

    sorted_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)
    return [(chunk_map[cid], scores[cid]) for cid in sorted_ids]


# ── CrossEncoder reranker ─────────────────────────────────────────────────────

class CrossEncoderReranker:
    """
    Reranks (query, chunk) pairs using a cross-encoder.

    Unlike bi-encoder cosine similarity (which encodes query and chunk
    independently), the cross-encoder reads them together and captures
    their semantic interaction. This produces far more accurate relevance
    scores but is too slow to run over thousands of candidates — hence it
    is applied only after RRF narrows the pool.

    Uses a singleton to avoid reloading the model on every query.
    """

    _instance: Optional["CrossEncoderReranker"] = None

    def __init__(self) -> None:
        logger.info("Loading CrossEncoder: %s", RERANKER_MODEL)
        self._model = CrossEncoder(RERANKER_MODEL, max_length=RERANKER_MAX_LENGTH)

    @classmethod
    def get(cls) -> "CrossEncoderReranker":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def rerank(
        self,
        query: str,
        candidates: list[tuple[Chunk, float]],
        top_n: int,
    ) -> list[tuple[Chunk, float]]:
        if not candidates:
            return []
        pairs = [(query, chunk.text[:512]) for chunk, _ in candidates]
        scores: np.ndarray = self._model.predict(pairs)
        ranked = sorted(zip(candidates, scores.tolist()), key=lambda x: x[1], reverse=True)
        return [(chunk, float(score)) for (chunk, _), score in ranked[:top_n]]


# ── Strategy A ────────────────────────────────────────────────────────────────

class StrategyA(RetrievalStrategy):
    """
    Baseline: Raw Vector Search.

    Query → embed → FAISS cosine search → top-k chunks.
    No query expansion, no BM25, no reranking.
    """

    def __init__(self, store: DualVectorStore, embedder: EmbeddingProvider) -> None:
        self._store = store
        self._embedder = embedder

    @property
    def name(self) -> str:
        return "Strategy A — Raw Vector Search"

    def retrieve(self, query: str, k: int = STRATEGY_A_TOP_K) -> list[RetrievalResult]:
        t0 = time.perf_counter()
        embedding = self._embedder.embed([query])[0]
        raw = self._store.faiss.search(embedding, k=k)
        latency = int((time.perf_counter() - t0) * 1000)

        return [
            RetrievalResult(
                chunk=chunk,
                score=round(score, 4),
                rank=i + 1,
                strategy="A",
                retrieval_path="faiss",
                latency_ms=latency,
            )
            for i, (chunk, score) in enumerate(raw)
        ]


# ── Strategy B ────────────────────────────────────────────────────────────────

class StrategyB(RetrievalStrategy):
    """
    AI-Enhanced Retrieval (PIC-inspired production pattern).

    Pipeline:
      1. MockGenerativeModel expands the query (vocabulary bridging)
      2. Embed expanded query → FAISS search (k=STRATEGY_B_FAISS_K)
      3. Original query → BM25 search (k=STRATEGY_B_BM25_K)   [lexical path]
      4. RRF fusion of FAISS + BM25 results                    [rank fusion]
      5. CrossEncoder reranker → final top-k                   [interaction rerank]

    Why each step matters:
      - Expansion: bridges vocabulary gap between user language and corpus
      - BM25: catches exact technical terms semantic search may miss
      - RRF: combines ranks robustly without score-scale issues
      - CrossEncoder: reads (query, chunk) together for true relevance scoring
    """

    def __init__(
        self,
        store: DualVectorStore,
        embedder: EmbeddingProvider,
        generative_model,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._generative = generative_model
        self._reranker = CrossEncoderReranker.get()

    @property
    def name(self) -> str:
        return "Strategy B — AI-Enhanced Retrieval"

    def expand_query(self, query: str) -> tuple[str, list[str]]:
        """Returns (expanded_query, expansion_terms_list)."""
        prompt = (
            "You are a technical search query optimizer. Rewrite the following query "
            "to be semantically richer and retrieve better results from a technical "
            "knowledge base about distributed systems and cloud infrastructure. "
            "Include relevant technical terms, synonyms, and related concepts. "
            f"Query: {query}"
        )
        response = self._generative.generate_content(prompt)
        terms = self._generative.get_expansion_terms(query)
        return response.text, terms

    def retrieve(self, query: str, k: int = STRATEGY_B_FINAL_K) -> list[RetrievalResult]:
        t0 = time.perf_counter()

        # Step 1 — Query expansion
        expanded_query, expansion_terms = self.expand_query(query)

        # Step 2 — FAISS search on expanded query (semantic path)
        expanded_embedding = self._embedder.embed([expanded_query])[0]
        faiss_results = self._store.faiss.search(expanded_embedding, k=STRATEGY_B_FAISS_K)

        # Step 3 — BM25 search on original query (lexical path)
        bm25_results = self._store.bm25.search(query, k=STRATEGY_B_BM25_K)

        # Step 4 — RRF fusion
        fused = rrf_fuse(faiss_results, bm25_results, k=RRF_K)

        # Step 5 — CrossEncoder rerank
        reranked = self._reranker.rerank(
            query, fused[: STRATEGY_B_RERANK_TOP_N], top_n=k
        )

        latency = int((time.perf_counter() - t0) * 1000)

        return [
            RetrievalResult(
                chunk=chunk,
                score=round(score, 4),
                rank=i + 1,
                strategy="B",
                expanded_query=expanded_query,
                expansion_terms=expansion_terms,
                retrieval_path="rrf_fused",
                latency_ms=latency,
            )
            for i, (chunk, score) in enumerate(reranked)
        ]
