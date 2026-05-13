# ── Vertex AI simulation ─────────────────────────────────────────────────────
VERTEX_MODEL_NAME: str = "textembedding-gecko@003"
GENERATIVE_MODEL_NAME: str = "gemini-pro"

# ── Local embedding model (simulates textembedding-gecko) ─────────────────────
LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
EMBEDDING_DIM: int = 384
EMBEDDING_BATCH_SIZE: int = 64

# ── FAISS ─────────────────────────────────────────────────────────────────────
FAISS_INDEX_TYPE: str = "IndexFlatIP"  # Inner product = cosine for L2-normalized vectors

# ── Strategy A ────────────────────────────────────────────────────────────────
STRATEGY_A_TOP_K: int = 3

# ── Strategy B ────────────────────────────────────────────────────────────────
STRATEGY_B_FAISS_K: int = 10
STRATEGY_B_BM25_K: int = 10
STRATEGY_B_RERANK_TOP_N: int = 25
STRATEGY_B_FINAL_K: int = 3

# ── Reciprocal Rank Fusion ────────────────────────────────────────────────────
RRF_K: int = 60

# ── CrossEncoder Reranker ─────────────────────────────────────────────────────
RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RERANKER_MAX_LENGTH: int = 512

# ── Benchmark ─────────────────────────────────────────────────────────────────
BENCHMARK_OUTPUT_PATH: str = "retrieval_benchmark.md"
