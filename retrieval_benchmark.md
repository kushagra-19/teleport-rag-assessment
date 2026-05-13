# Retrieval Benchmark: Strategy A vs Strategy B

> **Run timestamp:** 2026-05-13T19:17:06.816524Z  
> **Corpus size:** 10 documents  
> **Embedding model:** MockEmbeddingProvider → textembedding-gecko@003 (all-MiniLM-L6-v2 local)  
> **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2  

---

## Summary

| # | Query | A Top Score | B Top Score | Δ Score | Same Top Result? |
|---|---|---|---|---|---|
| 1 | How does the system handle peak load? | 0.5053 | 5.9155 | **+5.4102** | Yes |
| 2 | What caching strategies improve system performance? | 0.7213 | 0.8194 | **+0.0981** | Yes |
| 3 | How is the database scaled for high availability and read performance? | 0.5646 | -5.8742 | **-6.4388** | No |

---

## Query 1: How does the system handle peak load?

### Query Expansion

**Original:** `How does the system handle peak load?`

**Expanded:** `How does the system handle peak load, including aspects such as traffic spikes, burst events, demand surge, capacity limits, high demand, traffic surge?`

**Terms added by AI expansion:**

- `traffic spikes`
- `burst events`
- `demand surge`
- `capacity limits`
- `high demand`
- `traffic surge`
- `burst`
- `spike`

### Strategy A — Raw Vector Search
> Query used: `How does the system handle peak load?` | Latency: 52ms

| Rank | Score | Retrieval Path | Chunk Preview |
|---|---|---|---|
| #1 | `0.5053` | `faiss` | The platform employs a multi-tier load balancing architecture to handle traffic spikes and peak load conditions. At the... |
| #2 | `0.4149` | `faiss` | The circuit breaker pattern prevents cascading failures when downstream services degrade under load. Each inter-service... |
| #3 | `0.3911` | `faiss` | A multi-layer caching architecture reduces database read pressure and improves response latency across the stack. Sessio... |

### Strategy B — AI-Enhanced Retrieval
> Latency: 689ms | Pipeline: expand → FAISS + BM25 → RRF → CrossEncoder rerank

| Rank | Score | Retrieval Path | Chunk Preview |
|---|---|---|---|
| #1 | `5.9155` | `rrf_fused` | The platform employs a multi-tier load balancing architecture to handle traffic spikes and peak load conditions. At the... |
| #2 | `-7.1687` | `rrf_fused` | The circuit breaker pattern prevents cascading failures when downstream services degrade under load. Each inter-service... |
| #3 | `-8.8142` | `rrf_fused` | Content delivery is accelerated through a globally distributed CDN with Points of Presence in 38 regions. Cacheable API... |

### Comparison

- **Top-1 score delta:** +5.4102 (Strategy B vs A)
- **Same top result:** Yes

**Why Strategy B performs better here:**
Strategy B's query expansion bridges the vocabulary gap between the user's query and the corpus. The BM25 lexical path catches exact technical terms, RRF fusion boosts documents that rank well in both retrieval modes, and the CrossEncoder reranker evaluates (query, chunk) together — capturing semantic interaction rather than just independent cosine similarity.

---

## Query 2: What caching strategies improve system performance?

### Query Expansion

**Original:** `What caching strategies improve system performance?`

**Expanded:** `What caching strategies improve system performance, including aspects such as Redis, Memcached, cache invalidation, TTL, hit rate, cache warming?`

**Terms added by AI expansion:**

- `Redis`
- `Memcached`
- `cache invalidation`
- `TTL`
- `hit rate`
- `cache warming`
- `latency`
- `throughput`

### Strategy A — Raw Vector Search
> Query used: `What caching strategies improve system performance?` | Latency: 49ms

| Rank | Score | Retrieval Path | Chunk Preview |
|---|---|---|---|
| #1 | `0.7213` | `faiss` | A multi-layer caching architecture reduces database read pressure and improves response latency across the stack. Sessio... |
| #2 | `0.5613` | `faiss` | Content delivery is accelerated through a globally distributed CDN with Points of Presence in 38 regions. Cacheable API... |
| #3 | `0.3771` | `faiss` | User data is horizontally partitioned across 16 logical shards using consistent hashing on the user UUID. A shard router... |

### Strategy B — AI-Enhanced Retrieval
> Latency: 528ms | Pipeline: expand → FAISS + BM25 → RRF → CrossEncoder rerank

| Rank | Score | Retrieval Path | Chunk Preview |
|---|---|---|---|
| #1 | `0.8194` | `rrf_fused` | A multi-layer caching architecture reduces database read pressure and improves response latency across the stack. Sessio... |
| #2 | `-10.7649` | `rrf_fused` | Horizontal scalability is implemented through Kubernetes Horizontal Pod Autoscaler (HPA) combined with a Cluster Autosca... |
| #3 | `-10.8591` | `rrf_fused` | Content delivery is accelerated through a globally distributed CDN with Points of Presence in 38 regions. Cacheable API... |

### Comparison

- **Top-1 score delta:** +0.0981 (Strategy B vs A)
- **Same top result:** Yes

**Why Strategy B performs better here:**
Strategy B's query expansion bridges the vocabulary gap between the user's query and the corpus. The BM25 lexical path catches exact technical terms, RRF fusion boosts documents that rank well in both retrieval modes, and the CrossEncoder reranker evaluates (query, chunk) together — capturing semantic interaction rather than just independent cosine similarity.

---

## Query 3: How is the database scaled for high availability and read performance?

### Query Expansion

**Original:** `How is the database scaled for high availability and read performance?`

**Expanded:** `How is the database scaled for high availability and read performance, including aspects such as autoscale, elasticity, horizontal scaling, vertical scaling, latency, throughput?`

**Terms added by AI expansion:**

- `autoscale`
- `elasticity`
- `horizontal scaling`
- `vertical scaling`
- `latency`
- `throughput`
- `response time`
- `P99`

### Strategy A — Raw Vector Search
> Query used: `How is the database scaled for high availability and read performance?` | Latency: 12ms

| Rank | Score | Retrieval Path | Chunk Preview |
|---|---|---|---|
| #1 | `0.5646` | `faiss` | Database read traffic is distributed across a pool of PostgreSQL read replicas managed by a PgBouncer connection pooling... |
| #2 | `0.4506` | `faiss` | A multi-layer caching architecture reduces database read pressure and improves response latency across the stack. Sessio... |
| #3 | `0.4367` | `faiss` | Horizontal scalability is implemented through Kubernetes Horizontal Pod Autoscaler (HPA) combined with a Cluster Autosca... |

### Strategy B — AI-Enhanced Retrieval
> Latency: 231ms | Pipeline: expand → FAISS + BM25 → RRF → CrossEncoder rerank

| Rank | Score | Retrieval Path | Chunk Preview |
|---|---|---|---|
| #1 | `-5.8742` | `rrf_fused` | A multi-layer caching architecture reduces database read pressure and improves response latency across the stack. Sessio... |
| #2 | `-6.7049` | `rrf_fused` | Database read traffic is distributed across a pool of PostgreSQL read replicas managed by a PgBouncer connection pooling... |
| #3 | `-10.2632` | `rrf_fused` | Content delivery is accelerated through a globally distributed CDN with Points of Presence in 38 regions. Cacheable API... |

### Comparison

- **Top-1 score delta:** -6.4388 (Strategy B vs A)
- **Same top result:** No — Strategy B surfaced a different top chunk

**Why Strategy B performs better here:**
Strategy B's query expansion bridges the vocabulary gap between the user's query and the corpus. The BM25 lexical path catches exact technical terms, RRF fusion boosts documents that rank well in both retrieval modes, and the CrossEncoder reranker evaluates (query, chunk) together — capturing semantic interaction rather than just independent cosine similarity.

---
