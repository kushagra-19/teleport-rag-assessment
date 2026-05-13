"""
FastAPI backend for the RAG Intelligence Engine UI.

Endpoints:
  GET  /health          → liveness check
  GET  /system-info     → index stats, model names, observability data
  GET  /corpus          → all indexed chunks
  POST /query           → run Strategy A, B, or both
  POST /benchmark       → run all 3 preset queries, return full comparison

Run:
    cd rag-pipeline
    uvicorn api:app --reload --port 8000
"""

from __future__ import annotations
import logging
import sys
import os
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(__file__))

from backend.src.pipeline import RAGPipeline
from backend.src.retrieval import RetrievalResult
from backend.src.storage import Chunk
from backend.data.corpus import CORPUS, BENCHMARK_QUERIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


# ── Pydantic models ───────────────────────────────────────────────────────────

class ChunkOut(BaseModel):
    id: int
    text: str
    source: str
    token_count: int

    @classmethod
    def from_chunk(cls, c: Chunk) -> "ChunkOut":
        return cls(id=c.id, text=c.text, source=c.source, token_count=c.token_count)


class RetrievalResultOut(BaseModel):
    chunk: ChunkOut
    score: float
    rank: int
    strategy: str
    expanded_query: Optional[str]
    expansion_terms: list[str]
    retrieval_path: str
    latency_ms: int

    @classmethod
    def from_result(cls, r: RetrievalResult) -> "RetrievalResultOut":
        return cls(
            chunk=ChunkOut.from_chunk(r.chunk),
            score=r.score,
            rank=r.rank,
            strategy=r.strategy,
            expanded_query=r.expanded_query,
            expansion_terms=r.expansion_terms,
            retrieval_path=r.retrieval_path,
            latency_ms=r.latency_ms,
        )


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    strategy: Literal["A", "B", "both"] = "both"
    k: int = Field(default=3, ge=1, le=10)


class QueryResponseOut(BaseModel):
    query: str
    strategy_a: Optional[list[RetrievalResultOut]]
    strategy_b: Optional[list[RetrievalResultOut]]
    expanded_query: Optional[str]
    expansion_terms: list[str]
    retrieval_time_ms: dict[str, int]


class SystemInfoOut(BaseModel):
    doc_count: int
    embedding_dim: int
    embedding_model: str
    faiss_index_type: str
    bm25_enabled: bool
    reranker_model: str
    generative_model: str


# ── Lifespan: initialize pipeline once at startup ─────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing RAG pipeline...")
    pipeline = RAGPipeline()
    report = pipeline.ingest(CORPUS)
    logger.info(
        "Pipeline ready: %d docs, %d dims, %dms ingestion",
        report.doc_count, report.embedding_dim, report.ingestion_time_ms,
    )
    app.state.pipeline = pipeline
    yield
    logger.info("Shutting down.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="RAG Intelligence Engine",
    description="Semantic RAG pipeline with Strategy A vs B benchmarking",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_pipeline() -> RAGPipeline:
    return app.state.pipeline


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/system-info", response_model=SystemInfoOut)
def system_info():
    info = get_pipeline().system_info()
    return SystemInfoOut(
        doc_count=info.doc_count,
        embedding_dim=info.embedding_dim,
        embedding_model=info.embedding_model,
        faiss_index_type=info.faiss_index_type,
        bm25_enabled=info.bm25_enabled,
        reranker_model=info.reranker_model,
        generative_model=info.generative_model,
    )


@app.get("/corpus", response_model=list[ChunkOut])
def get_corpus():
    return [ChunkOut.from_chunk(c) for c in get_pipeline().get_chunks()]


@app.post("/query", response_model=QueryResponseOut)
def query(req: QueryRequest):
    try:
        response = get_pipeline().query(req.query, strategy=req.strategy, k=req.k)
    except Exception as exc:
        logger.exception("Query failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return QueryResponseOut(
        query=response.query,
        strategy_a=[RetrievalResultOut.from_result(r) for r in response.strategy_a] if response.strategy_a else None,
        strategy_b=[RetrievalResultOut.from_result(r) for r in response.strategy_b] if response.strategy_b else None,
        expanded_query=response.expanded_query,
        expansion_terms=response.expansion_terms,
        retrieval_time_ms=response.retrieval_time_ms,
    )


@app.post("/benchmark")
def benchmark():
    pipeline = get_pipeline()
    results = []
    for query_text in BENCHMARK_QUERIES:
        try:
            response = pipeline.query(query_text, strategy="both", k=3)
            results.append({
                "query": query_text,
                "strategy_a": [RetrievalResultOut.from_result(r).dict() for r in response.strategy_a] if response.strategy_a else [],
                "strategy_b": [RetrievalResultOut.from_result(r).dict() for r in response.strategy_b] if response.strategy_b else [],
                "expanded_query": response.expanded_query,
                "expansion_terms": response.expansion_terms,
                "retrieval_time_ms": response.retrieval_time_ms,
            })
        except Exception as exc:
            logger.exception("Benchmark query failed: %s", exc)
            results.append({"query": query_text, "error": str(exc)})
    return {"benchmark_queries": results}
