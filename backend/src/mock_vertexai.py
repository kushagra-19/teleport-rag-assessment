"""
Mock implementations of Vertex AI SDK classes.

Provides drop-in replacements for:
  - vertexai.language_models.TextEmbeddingModel
  - vertexai.generative_models.GenerativeModel

The interface matches the real Vertex AI SDK exactly. Swapping to production
requires only changing the provider in embeddings.py — no other code changes.
"""

from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── TextEmbeddingModel ────────────────────────────────────────────────────────

class TextEmbeddingResult:
    """Mirrors vertexai.language_models.TextEmbedding."""
    __slots__ = ("values",)

    def __init__(self, values: list[float]) -> None:
        self.values = values


class TextEmbeddingModel:
    """
    Mock of vertexai.language_models.TextEmbeddingModel.

    Uses sentence-transformers/all-MiniLM-L6-v2 locally to simulate
    textembedding-gecko@003 behavior. Interface matches the real SDK:

        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        results = model.get_embeddings(["text one", "text two"])
        vector = results[0].values  # list[float], L2-normalized
    """

    _instance: Optional["TextEmbeddingModel"] = None

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer
        from backend.config.settings import LOCAL_EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE
        self._model_name = model_name
        self._batch_size = EMBEDDING_BATCH_SIZE
        self._encoder = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
        logger.info(
            "TextEmbeddingModel loaded (vertex_name=%s, local=%s)",
            model_name, LOCAL_EMBEDDING_MODEL,
        )

    @classmethod
    def from_pretrained(cls, model_name: str = "textembedding-gecko@003") -> "TextEmbeddingModel":
        """Singleton — avoids reloading the transformer on every call."""
        if cls._instance is None:
            cls._instance = cls(model_name)
        return cls._instance

    def get_embeddings(self, texts: list[str]) -> list[TextEmbeddingResult]:
        """Returns L2-normalized embedding results, matching the Vertex AI SDK signature."""
        results: list[TextEmbeddingResult] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            vectors = self._encoder.encode(batch, normalize_embeddings=True)
            results.extend(TextEmbeddingResult(v.tolist()) for v in vectors)
        return results


# ── GenerativeModel ───────────────────────────────────────────────────────────

class GenerativeModelResponse:
    """Mirrors vertexai.generative_models.GenerationResponse."""
    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        self.text = text


class GenerativeModel:
    """
    Mock of vertexai.generative_models.GenerativeModel.

    Produces semantically enriched query expansions using a curated
    domain-vocabulary map. This is deterministic (testable) and produces
    meaningfully different queries rather than simple synonym replacement.

    In production, replace this class with:
        from vertexai.generative_models import GenerativeModel
    No other code changes are required.
    """

    # Domain-specific semantic enrichment map.
    # Each key phrase triggers addition of production-relevant technical terms.
    _EXPANSION_MAP: dict[str, list[str]] = {
        "peak load":      ["traffic spikes", "burst events", "demand surge", "capacity limits"],
        "peak":           ["high demand", "traffic surge", "burst", "spike"],
        "load":           ["traffic", "request volume", "throughput", "concurrent requests"],
        "handle":         ["manage", "process", "absorb", "distribute", "route"],
        "scale":          ["autoscale", "elasticity", "horizontal scaling", "vertical scaling"],
        "scaling":        ["autoscaling", "horizontal scaling", "elasticity", "node provisioning"],
        "cache":          ["in-memory storage", "TTL", "cache hit rate", "eviction policy"],
        "caching":        ["Redis", "Memcached", "cache invalidation", "TTL", "hit rate", "cache warming"],
        "performance":    ["latency", "throughput", "response time", "P99", "efficiency"],
        "database":       ["data store", "OLTP", "read replicas", "write throughput"],
        "availability":   ["uptime", "redundancy", "failover", "high availability", "SLA"],
        "fail":           ["fault tolerance", "resilience", "circuit breaker", "retry"],
        "failure":        ["cascading failure", "fault tolerance", "resilience", "recovery"],
        "replicas":       ["read replicas", "standby nodes", "replication lag", "consistency"],
        "replica":        ["read replica", "standby", "streaming replication"],
        "distributed":    ["microservices", "cluster", "partitioned", "federated"],
        "monitor":        ["observability", "metrics", "alerting", "tracing"],
        "monitoring":     ["observability", "Prometheus", "Grafana", "distributed tracing", "SLO"],
        "rate limit":     ["token bucket", "throttling", "quota", "429 response"],
        "rate limiting":  ["token bucket algorithm", "throttling", "API quotas", "backpressure"],
        "queue":          ["message queue", "async processing", "event streaming", "backpressure"],
        "concurrent":     ["parallel processing", "thread safety", "connection pooling"],
        "concurrency":    ["parallelism", "thread safety", "async I/O", "connection pooling"],
        "autoscal":       ["elastic scaling", "auto-provisioning", "HPA", "cluster autoscaler"],
        "infrastructure": ["cloud infrastructure", "compute resources", "node pool", "cluster"],
        "resilience":     ["fault tolerance", "circuit breaker", "retry policy", "graceful degradation"],
        "latency":        ["response time", "P99 latency", "tail latency", "network round-trip"],
        "cdn":            ["edge caching", "content delivery", "geographic distribution", "PoP"],
        "shard":          ["data partitioning", "horizontal partitioning", "hash-based routing"],
        "sharding":       ["horizontal partitioning", "consistent hashing", "shard key", "scatter-gather"],
        "high availab":   ["failover", "redundancy", "standby", "replication", "uptime SLA"],
        "read perform":   ["read replicas", "connection pooling", "query optimization", "caching layer"],
    }

    def __init__(self, model_name: str = "gemini-pro") -> None:
        self.model_name = model_name

    def generate_content(self, prompt: str) -> GenerativeModelResponse:
        """
        Extracts the original query from a structured prompt and returns
        a semantically enriched version, bridging the vocabulary gap between
        user language and corpus terminology.
        """
        query = self._extract_query(prompt)
        expanded = self._build_expanded_query(query)
        logger.debug("Query expansion: %r → %r", query, expanded)
        return GenerativeModelResponse(expanded)

    def get_expansion_terms(self, query: str) -> list[str]:
        """Returns only the list of added terms (used for UI explainability chips)."""
        return self._collect_expansion_terms(query.lower())

    # ── private ──────────────────────────────────────────────────────────────

    def _extract_query(self, prompt: str) -> str:
        for marker in ("Query:", "query:", "Question:", "question:"):
            if marker in prompt:
                return prompt.split(marker)[-1].strip().strip('"').strip("'")
        sentences = [s.strip() for s in prompt.strip().split(".") if s.strip()]
        return sentences[-1] if sentences else prompt

    def _collect_expansion_terms(self, query_lower: str) -> list[str]:
        seen: set[str] = set()
        terms: list[str] = []
        for keyword, expansions in self._EXPANSION_MAP.items():
            if keyword in query_lower:
                for term in expansions:
                    if term not in seen:
                        seen.add(term)
                        terms.append(term)
        if not terms:
            terms = ["system architecture", "performance characteristics",
                     "scalability patterns", "operational reliability"]
        return terms[:8]

    def _build_expanded_query(self, query: str) -> str:
        query_lower = query.lower().rstrip("?").rstrip(".")
        terms = self._collect_expansion_terms(query_lower)
        expansion_clause = ", ".join(terms[:6])
        base = query_lower.capitalize()
        return f"{base}, including aspects such as {expansion_clause}?"
