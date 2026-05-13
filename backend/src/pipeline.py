"""
RAGPipeline: main orchestrator.

Manages document ingestion into the dual vector store and
routes queries to Strategy A, Strategy B, or both.
"""

from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import Literal, Optional

from backend.src.embeddings import EmbeddingProvider, MockEmbeddingProvider
from backend.src.storage import DualVectorStore, Chunk
from backend.src.retrieval import RetrievalResult, StrategyA, StrategyB
from backend.src.mock_vertexai import GenerativeModel
from backend.config.settings import (
    EMBEDDING_DIM,
    GENERATIVE_MODEL_NAME,
    FAISS_INDEX_TYPE,
    RERANKER_MODEL,
)

logger = logging.getLogger(__name__)


# ── Response dataclasses ──────────────────────────────────────────────────────

@dataclass
class IngestionReport:
    doc_count: int
    chunk_count: int
    embedding_dim: int
    ingestion_time_ms: int


@dataclass
class QueryResponse:
    query: str
    strategy_a: Optional[list[RetrievalResult]]
    strategy_b: Optional[list[RetrievalResult]]
    expanded_query: Optional[str]
    expansion_terms: list[str]
    retrieval_time_ms: dict[str, int]


@dataclass
class SystemInfo:
    doc_count: int
    embedding_dim: int
    embedding_model: str
    faiss_index_type: str
    bm25_enabled: bool
    reranker_model: str
    generative_model: str


# ── Pipeline ──────────────────────────────────────────────────────────────────

class RAGPipeline:
    """
    Orchestrates the full RAG pipeline:
      - ingest()  → embed documents → populate dual vector store
      - query()   → run Strategy A, B, or both → return results + metadata
      - system_info() → expose observability data
    """

    def __init__(self, embedder: Optional[EmbeddingProvider] = None) -> None:
        self._embedder = embedder or MockEmbeddingProvider()
        self._store = DualVectorStore(dim=EMBEDDING_DIM)
        self._generative = GenerativeModel(GENERATIVE_MODEL_NAME)
        self._strategy_a = StrategyA(self._store, self._embedder)
        self._strategy_b = StrategyB(self._store, self._embedder, self._generative)
        logger.info("RAGPipeline initialized")

    # ── public API ────────────────────────────────────────────────────────────

    def ingest(self, documents: list[str], source: str = "corpus") -> IngestionReport:
        """
        Embeds documents in batches and populates both FAISS and BM25 indexes.
        Returns an IngestionReport with timing and count metadata.
        """
        t0 = time.perf_counter()

        chunks = [
            Chunk(
                id=i,
                text=doc,
                source=f"{source}[{i}]",
                token_count=len(doc.split()),
            )
            for i, doc in enumerate(documents)
        ]

        embeddings = self._embedder.embed([c.text for c in chunks])
        self._store.add(chunks, embeddings)

        elapsed = int((time.perf_counter() - t0) * 1000)
        logger.info("Ingested %d documents in %dms", len(documents), elapsed)

        return IngestionReport(
            doc_count=len(documents),
            chunk_count=len(chunks),
            embedding_dim=self._embedder.embedding_dim,
            ingestion_time_ms=elapsed,
        )

    def query(
        self,
        query: str,
        strategy: Literal["A", "B", "both"] = "both",
        k: int = 3,
    ) -> QueryResponse:
        result_a: Optional[list[RetrievalResult]] = None
        result_b: Optional[list[RetrievalResult]] = None
        timings: dict[str, int] = {}

        if strategy in ("A", "both"):
            t0 = time.perf_counter()
            result_a = self._strategy_a.retrieve(query, k=k)
            timings["A"] = int((time.perf_counter() - t0) * 1000)

        if strategy in ("B", "both"):
            t0 = time.perf_counter()
            result_b = self._strategy_b.retrieve(query, k=k)
            timings["B"] = int((time.perf_counter() - t0) * 1000)

        expanded_query = result_b[0].expanded_query if result_b else None
        expansion_terms = result_b[0].expansion_terms if result_b else []

        return QueryResponse(
            query=query,
            strategy_a=result_a,
            strategy_b=result_b,
            expanded_query=expanded_query,
            expansion_terms=expansion_terms,
            retrieval_time_ms=timings,
        )

    def system_info(self) -> SystemInfo:
        return SystemInfo(
            doc_count=self._store.size,
            embedding_dim=self._embedder.embedding_dim,
            embedding_model=self._embedder.model_name,
            faiss_index_type=FAISS_INDEX_TYPE,
            bm25_enabled=True,
            reranker_model=RERANKER_MODEL,
            generative_model=GENERATIVE_MODEL_NAME,
        )

    def get_chunks(self) -> list[Chunk]:
        return self._store.chunks

    # ── internals exposed for testing ─────────────────────────────────────────

    @property
    def strategy_a(self) -> StrategyA:
        return self._strategy_a

    @property
    def strategy_b(self) -> StrategyB:
        return self._strategy_b

    @property
    def store(self) -> DualVectorStore:
        return self._store

    def __len__(self) -> int:
        return self._store.size
