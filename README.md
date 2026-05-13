# RAG Intelligence Engine

**Senior GenAI Assessment — Semantic Retrieval, Embeddings & Vector Search**  
*GCP / Vertex AI focus · Local implementation · Production-grade architecture*

---

## Overview

A production-quality Retrieval-Augmented Generation (RAG) pipeline that compares two retrieval strategies on a 10-paragraph technical corpus about distributed systems and cloud infrastructure.

```
Strategy A  ──  Raw Vector Search
                query → embed → FAISS cosine search → top-k

Strategy B  ──  AI-Enhanced Retrieval
                query → MockGenerativeModel (expand) → expanded query
                      → FAISS semantic search (k=10)
                      + BM25 lexical search (k=10)
                      → RRF fusion
                      → CrossEncoder rerank
                      → top-k
```

---

## Architecture

```
rag-pipeline/
│
├── backend/
│   ├── config/
│   │   └── settings.py          # All constants — no hardcoded values anywhere else
│   ├── src/
│   │   ├── mock_vertexai.py     # Mock TextEmbeddingModel + GenerativeModel (Vertex AI interface)
│   │   ├── embeddings.py        # EmbeddingProvider ABC + MockEmbeddingProvider
│   │   ├── storage.py           # FAISSStore + BM25Store + DualVectorStore
│   │   ├── retrieval.py         # StrategyA, StrategyB, rrf_fuse(), CrossEncoderReranker
│   │   └── pipeline.py          # RAGPipeline orchestrator
│   └── data/
│       └── corpus.py            # 10 technical paragraphs + benchmark queries
│
├── tests/
│   └── test_pipeline.py         # 56 pytest tests, GCP SDK fully mocked
│
├── frontend/                    # React 18 + Vite + Tailwind — dark UI
│   └── src/
│       ├── components/          # QueryPanel, ComparisonView, ChunkCard, ExpansionPanel,
│       │                        # BenchmarkDashboard, SystemInfo, CorpusExplorer
│       ├── hooks/useQuery.ts    # API call hooks
│       └── types/index.ts       # Shared TypeScript types
│
├── api.py                       # FastAPI — /query, /benchmark, /corpus, /system-info
├── benchmark.py                 # Benchmark runner → JSON + retrieval_benchmark.md
├── retrieval_benchmark.md       # Pre-generated Strategy A vs B comparison (submission artifact)
└── requirements.txt
```

---

## Quick Start

### Backend

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run benchmark (generates retrieval_benchmark.md)
python benchmark.py

# 3. Run tests
pytest tests/ -v

# 4. Start API server
uvicorn api:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

The Vite dev server proxies all API calls to `localhost:8000`.

---

## Similarity Metric: Cosine vs Euclidean

### Cosine Similarity

```
cos(A, B) = (A · B) / (|A| × |B|)   ∈ [-1, 1]
```

Measures the **angle** between two vectors. Invariant to magnitude — two documents that say the same thing at different lengths produce identical cosine similarity. This is exactly what semantic search requires: we care about *meaning*, not *verbosity*.

**Implementation:** We use FAISS `IndexFlatIP` (inner product) on L2-normalized vectors:

```python
# L2-normalize once at index time
vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

# Inner product on normalized vectors = cosine similarity
# (A · B) = |A||B| cos(θ) = cos(θ)  when |A| = |B| = 1
index = faiss.IndexFlatIP(dim)
```

This is mathematically equivalent to cosine similarity but faster at query time — no division needed per query.

### Euclidean Distance

```
d(A, B) = √Σ(Aᵢ - Bᵢ)²   ∈ [0, ∞)
```

Measures the straight-line distance between points. **Sensitive to magnitude.** A long document and a short document about the same topic can be far apart in Euclidean space even if semantically identical, because longer texts have embeddings with larger norms.

### Why We Chose Cosine

| Property | Cosine | Euclidean |
|---|---|---|
| Magnitude invariant | Yes | No |
| Suitable for text embeddings | Yes | No |
| Handles varying document lengths | Yes | No |
| Implementation (FAISS) | `IndexFlatIP` + normalize | `IndexFlatL2` |
| Query-time cost | O(d) | O(d) |

For semantic text search, cosine similarity is the standard choice. The only case where Euclidean might be preferred is when magnitude carries meaningful information (e.g., frequency-weighted vectors), which is not the case for transformer embeddings.

---

## Migration to Vertex AI Vector Search (Matching Engine)

This local implementation is designed for production migration with **one-class changes per layer**.

### Step-by-Step Migration

#### 1. Swap the Embedding Provider

```python
# Current (local)
from backend.src.embeddings import MockEmbeddingProvider
embedder = MockEmbeddingProvider()  # sentence-transformers/all-MiniLM-L6-v2

# Production (Vertex AI)
class VertexEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        import vertexai
        from vertexai.language_models import TextEmbeddingModel
        vertexai.init(project="my-project", location="us-central1")
        self._model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")

    def embed(self, texts):
        results = self._model.get_embeddings(texts)
        return np.array([r.values for r in results], dtype=np.float32)
```

No changes to `pipeline.py`, `retrieval.py`, or `storage.py`.

#### 2. Swap the Generative Model

```python
# Current (mock)
from backend.src.mock_vertexai import GenerativeModel

# Production (real Vertex AI)
from vertexai.generative_models import GenerativeModel  # drop-in replacement
```

#### 3. Swap the Vector Store

Replace `FAISSStore` with a `VertexVectorStore` implementing the same `search()` interface:

```python
from google.cloud import aiplatform

class VertexVectorStore:
    def __init__(self, index_endpoint: str, deployed_index_id: str):
        self._endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint)
        self._deployed_id = deployed_index_id

    def search(self, query_embedding: np.ndarray, k: int):
        response = self._endpoint.find_neighbors(
            deployed_index_id=self._deployed_id,
            queries=[query_embedding.tolist()],
            num_neighbors=k,
        )
        return [(self._chunks[int(m.id)], m.distance) for m in response[0]]
```

#### 4. Deploy to Cloud Run

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
```

```bash
gcloud run deploy rag-engine \
  --source . \
  --region us-central1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=my-project
```

#### 5. Scale to Production

| Concern | Local | Vertex AI Production |
|---|---|---|
| Index type | Flat (exact, O(n)) | HNSW / ScaNN (ANN, O(log n)) |
| Corpus size | Thousands | Billions |
| Ingestion | In-process, synchronous | Vertex AI batch indexing jobs |
| Index updates | Full rebuild | Streaming index updates |
| Embedding cache | None | Cloud Memorystore (Redis) |
| Multi-tenancy | Single store | One index per project (same pattern) |
| Latency | ~20ms local | ~50ms (network + ANN overhead) |
| Throughput | Single node | Horizontal Cloud Run scaling |

### Scalability Considerations

**Approximate Nearest Neighbor (ANN):** For corpora beyond ~1M vectors, switch from `IndexFlatIP` (exact, O(n)) to `IndexHNSWFlat` or `IndexIVFFlat` in FAISS — or use Vertex AI Matching Engine which runs ScaNN internally.

**Embedding caching:** Cache frequent query embeddings in Redis with a 1-hour TTL. Cache hit rate of 40%+ is common for repetitive enterprise queries.

**Batch ingestion:** For large document uploads, run embedding generation as async background jobs rather than in-request, exactly as the watchdog pattern in production systems.

**Distributed retrieval:** For multi-region deployments, Vertex AI Matching Engine natively supports geo-distributed indexes with regional failover.

---

## Retrieval Strategy Comparison

### Why Strategy B Performs Better

**Strategy A** embeds the query literally. The word "peak load" is close in embedding space to corpus sentences that use the exact phrase "peak load" — but the corpus may use "traffic spikes", "burst events", "demand surge" to describe the same concept.

**Strategy B** bridges this vocabulary gap in three layers:

```
1. Query Expansion (vocabulary bridging)
   "peak load" → + "traffic spikes, burst events, demand surge, capacity limits, ..."
   The expanded query finds semantically equivalent content even with different wording.

2. BM25 Lexical Search (exact-term coverage)
   Runs on the ORIGINAL query — catches exact technical terms, product names,
   acronyms (PgBouncer, HPA, CDC) that semantic search may miss.

3. RRF Fusion (robust rank combination)
   score(doc) = Σ 1/(60 + rank_in_list_i)
   Documents appearing in both FAISS and BM25 results get a compounded boost.
   Parameter-free — avoids score-scale mismatch between cosine and BM25.

4. CrossEncoder Reranker (interaction-aware scoring)
   Unlike bi-encoder cosine similarity (which encodes query and chunk independently),
   the CrossEncoder reads (query, chunk) together. It captures their semantic
   interaction — far more accurate than cosine, but too slow for thousands of
   candidates, so applied only after RRF narrows the pool.
```

---

## Stack

| Layer | Tool | Purpose |
|---|---|---|
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Simulate `textembedding-gecko@003` |
| Vector search | `faiss-cpu IndexFlatIP` | Cosine similarity (inner product on normalized vecs) |
| Keyword search | `rank-bm25 BM25Okapi` | Lexical retrieval (exact terms, acronyms) |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Interaction-aware final reranking |
| Rank fusion | Custom `rrf_fuse()` | Combine FAISS + BM25 without score-scale issues |
| API | `FastAPI` + `uvicorn` | Auto OpenAPI docs at `/docs` |
| Frontend | `React 18` + `Vite` + `Tailwind CSS` | Dark futuristic UI |
| Tests | `pytest` + `unittest.mock` | 56 tests, GCP SDK fully mocked |
| **Cost** | **$0** | **No paid APIs, no GCP credentials required** |

---

## Production Background

The architecture in this assessment is not theoretical — it is a distilled version of patterns I built and operate in a production multi-tenant RAG system (referred to here as **Project Intel Core**, part of the FuldOne platform).

### What Project Intel Core Does

Project Intel Core is a production document intelligence system that ingests enterprise knowledge bases (PDFs, markdown, structured exports) and answers natural-language queries across multiple isolated client projects. It is in active use and handles real workloads.

**Core production stack:**
- **LangGraph StateGraph** with 10+ nodes for multi-turn conversation, conditional routing, iterative context expansion, and final verification
- **5 retrieval strategies** selectable per query: dense-only, sparse-only, hybrid, reranked hybrid, and multi-query ensemble
- **FAISS + BM25Okapi dual store** — the same dual-store pattern used in Strategy B here, but with per-project index isolation
- **CrossEncoder reranking** (`ms-marco-MiniLM-L-6-v2`) applied after RRF fusion — same model and singleton pattern used in this assessment
- **Query expansion** via a real generative model (OpenAI / Vertex AI depending on environment) with follow-up detection and multi-turn context carry-forward
- **Watchdog + incremental indexing** — filesystem monitor rebuilds FAISS indices on document change without full reingest
- **MongoDB session storage** for multi-turn conversation persistence
- **Per-project FAISS isolation** — each client project gets its own index namespace, preventing cross-tenant retrieval bleed

### What This Assessment Adapts

This assessment deliberately takes the retrieval and benchmarking layers of that system — the most relevant slice for the assessment requirements — and makes them self-contained and locally runnable with no paid APIs or GCP credentials.

| Production (Project Intel Core) | Assessment |
|---|---|
| Real Vertex AI `textembedding-gecko@003` | `all-MiniLM-L6-v2` (same interface, local) |
| Real Vertex AI `GenerativeModel` | `MockGenerativeModel` (same interface, deterministic) |
| LangGraph multi-node orchestration | `RAGPipeline` single orchestrator |
| 5 retrieval strategies | 2 strategies (A: dense, B: full hybrid pipeline) |
| Per-project FAISS isolation | Single shared index |
| MongoDB session storage | Stateless HTTP API |
| Streaming incremental indexing | Static 10-doc corpus |

The abstraction boundaries — `EmbeddingProvider` ABC, `FAISSStore`/`BM25Store` composable stores, `rrf_fuse()` as a pure function — are the same ones used in production, which is why the migration path to Vertex AI described in this README is one class swap per layer, not a rewrite.

### Key Lessons Carried Over

**RRF over score fusion:** In production, BM25 scores and cosine scores cannot be averaged — their scales are incompatible and corpus-size dependent. RRF operates on ranks, making it robust to this. This was a production lesson before it was a design decision here.

**CrossEncoder as a final gate, not a first pass:** The CrossEncoder reads (query, chunk) jointly and is 10-50x more accurate than bi-encoder cosine for relevance judgement. But it is too slow for thousands of candidates. The pattern is always: fast retrieval → narrow to 20-50 candidates → CrossEncoder rerank. This is the same flow in both systems.

**Query expansion hurts as often as it helps on narrow queries:** Strategy B benchmark Query 3 ("database scaled for high availability") surfaces a different top chunk than Strategy A because expansion terms like "horizontal scaling, elasticity" shift the embedding toward generic scaling content rather than the PgBouncer/read-replica specifics the user wanted. In production, this is mitigated by running expansion and non-expansion paths in parallel and using RRF to prevent any single path from dominating. The benchmark in this assessment documents this tradeoff honestly.
