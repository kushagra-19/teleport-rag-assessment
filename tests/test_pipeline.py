"""
Pytest suite for the RAG pipeline.

Tests every layer individually and as an integrated system.
GCP SDK classes (TextEmbeddingModel, GenerativeModel) are mocked
via unittest.mock.patch to verify the pipeline works without real
Vertex AI credentials.
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pytest
from unittest.mock import patch, MagicMock, call

from backend.src.mock_vertexai import (
    TextEmbeddingModel, TextEmbeddingResult,
    GenerativeModel, GenerativeModelResponse,
)
from backend.src.embeddings import MockEmbeddingProvider
from backend.src.storage import Chunk, FAISSStore, BM25Store, DualVectorStore
from backend.src.retrieval import StrategyA, StrategyB, rrf_fuse, CrossEncoderReranker
from backend.src.pipeline import RAGPipeline
from backend.data.corpus import CORPUS, BENCHMARK_QUERIES
from backend.config.settings import EMBEDDING_DIM, RRF_K


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def embedder() -> MockEmbeddingProvider:
    return MockEmbeddingProvider()


@pytest.fixture(scope="module")
def pipeline() -> RAGPipeline:
    p = RAGPipeline()
    p.ingest(CORPUS)
    return p


@pytest.fixture(scope="module")
def store(embedder) -> DualVectorStore:
    s = DualVectorStore(dim=EMBEDDING_DIM)
    texts = CORPUS[:5]
    embeddings = embedder.embed(texts)
    chunks = [Chunk(id=i, text=t, source=f"test[{i}]", token_count=len(t.split())) for i, t in enumerate(texts)]
    s.add(chunks, embeddings)
    return s


# ── Mock Vertex AI ────────────────────────────────────────────────────────────

class TestMockTextEmbeddingModel:
    def test_from_pretrained_returns_instance(self):
        model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
        assert isinstance(model, TextEmbeddingModel)

    def test_from_pretrained_is_singleton(self):
        m1 = TextEmbeddingModel.from_pretrained()
        m2 = TextEmbeddingModel.from_pretrained()
        assert m1 is m2

    def test_get_embeddings_returns_correct_count(self):
        model = TextEmbeddingModel.from_pretrained()
        texts = ["hello world", "distributed systems", "load balancing"]
        results = model.get_embeddings(texts)
        assert len(results) == 3

    def test_get_embeddings_values_are_floats(self):
        model = TextEmbeddingModel.from_pretrained()
        result = model.get_embeddings(["test"])[0]
        assert isinstance(result, TextEmbeddingResult)
        assert all(isinstance(v, float) for v in result.values)

    def test_get_embeddings_correct_dimension(self):
        model = TextEmbeddingModel.from_pretrained()
        result = model.get_embeddings(["dimension check"])[0]
        assert len(result.values) == EMBEDDING_DIM

    def test_embeddings_are_normalized(self):
        model = TextEmbeddingModel.from_pretrained()
        result = model.get_embeddings(["normalization test"])[0]
        norm = np.linalg.norm(result.values)
        assert abs(norm - 1.0) < 1e-4


class TestMockGenerativeModel:
    def test_generate_content_returns_response(self):
        model = GenerativeModel()
        response = model.generate_content("Query: How does the system handle peak load?")
        assert isinstance(response, GenerativeModelResponse)
        assert isinstance(response.text, str)
        assert len(response.text) > 0

    def test_expansion_is_richer_than_original(self):
        model = GenerativeModel()
        original = "How does the system handle peak load?"
        response = model.generate_content(f"Query: {original}")
        assert len(response.text) > len(original)

    def test_expansion_contains_domain_terms(self):
        model = GenerativeModel()
        response = model.generate_content("Query: How does the system handle peak load?")
        expanded_lower = response.text.lower()
        domain_terms = ["traffic", "autoscal", "burst", "surge", "capacity", "concurrent"]
        assert any(term in expanded_lower for term in domain_terms)

    def test_get_expansion_terms_returns_list(self):
        model = GenerativeModel()
        terms = model.get_expansion_terms("peak load handling")
        assert isinstance(terms, list)
        assert len(terms) > 0

    def test_expansion_terms_are_strings(self):
        model = GenerativeModel()
        terms = model.get_expansion_terms("caching performance")
        assert all(isinstance(t, str) for t in terms)

    def test_unknown_query_gets_generic_expansion(self):
        model = GenerativeModel()
        terms = model.get_expansion_terms("completely unrelated xyz query")
        assert len(terms) > 0  # Falls back to generic terms


# ── Embeddings ────────────────────────────────────────────────────────────────

class TestMockEmbeddingProvider:
    def test_embed_shape(self, embedder):
        texts = ["hello", "world", "test"]
        result = embedder.embed(texts)
        assert result.shape == (3, EMBEDDING_DIM)

    def test_embed_dtype_float32(self, embedder):
        result = embedder.embed(["dtype check"])
        assert result.dtype == np.float32

    def test_embeddings_are_unit_normalized(self, embedder):
        result = embedder.embed(["normalization", "check", "multiple"])
        norms = np.linalg.norm(result, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-4)

    def test_embedding_dim_property(self, embedder):
        assert embedder.embedding_dim == EMBEDDING_DIM

    def test_model_name_is_string(self, embedder):
        assert isinstance(embedder.model_name, str)
        assert len(embedder.model_name) > 0

    def test_single_text_embedding(self, embedder):
        result = embedder.embed(["single text"])
        assert result.shape == (1, EMBEDDING_DIM)

    @patch("backend.src.mock_vertexai.TextEmbeddingModel.get_embeddings")
    def test_embed_calls_vertex_model(self, mock_get_embeddings):
        dim = EMBEDDING_DIM
        mock_get_embeddings.return_value = [
            TextEmbeddingResult([0.1] * dim)
        ]
        provider = MockEmbeddingProvider()
        provider.embed(["mock test"])
        mock_get_embeddings.assert_called_once()


# ── Storage ───────────────────────────────────────────────────────────────────

class TestFAISSStore:
    def test_add_increases_size(self, embedder):
        store = FAISSStore(dim=EMBEDDING_DIM)
        chunks = [Chunk(id=0, text="test doc", source="test", token_count=2)]
        emb = embedder.embed(["test doc"])
        store.add(chunks, emb)
        assert store.size == 1

    def test_search_returns_k_results(self, embedder):
        store = FAISSStore(dim=EMBEDDING_DIM)
        texts = ["load balancing traffic", "cache memory redis", "database replica"]
        chunks = [Chunk(id=i, text=t, source="test", token_count=3) for i, t in enumerate(texts)]
        emb = embedder.embed(texts)
        store.add(chunks, emb)
        q_emb = embedder.embed(["load balancing"])[0]
        results = store.search(q_emb, k=2)
        assert len(results) == 2

    def test_search_scores_are_descending(self, store, embedder):
        q_emb = embedder.embed(["caching strategy Redis"])[0]
        results = store.faiss.search(q_emb, k=5)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_returns_chunks_and_scores(self, store, embedder):
        q_emb = embedder.embed(["autoscaling kubernetes"])[0]
        results = store.faiss.search(q_emb, k=1)
        chunk, score = results[0]
        assert isinstance(chunk, Chunk)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.1  # cosine similarity ≤ 1


class TestBM25Store:
    def _corpus_store(self) -> BM25Store:
        """BM25 needs a realistic corpus for IDF to produce non-zero scores."""
        store = BM25Store()
        chunks = [
            Chunk(id=i, text=t, source="test", token_count=len(t.split()))
            for i, t in enumerate(CORPUS)
        ]
        store.add(chunks)
        return store

    def test_add_and_search(self):
        store = self._corpus_store()
        results = store.search("load balancing traffic", k=3)
        assert len(results) >= 1
        top_ids = [r[0].id for r in results]
        assert 0 in top_ids  # chunk 0 is the load balancing paragraph

    def test_search_empty_store_returns_empty(self):
        store = BM25Store()
        results = store.search("anything", k=3)
        assert results == []

    def test_bm25_finds_exact_keyword(self):
        store = self._corpus_store()
        results = store.search("PgBouncer", k=3)
        assert len(results) >= 1
        top_ids = [r[0].id for r in results]
        assert 4 in top_ids  # chunk 4 is the PostgreSQL/PgBouncer paragraph


class TestDualVectorStore:
    def test_add_populates_both_stores(self, embedder):
        ds = DualVectorStore(dim=EMBEDDING_DIM)
        texts = ["test doc one", "test doc two"]
        chunks = [Chunk(id=i, text=t, source="test", token_count=3) for i, t in enumerate(texts)]
        emb = embedder.embed(texts)
        ds.add(chunks, emb)
        assert ds.faiss.size == 2
        assert ds.bm25.size == 2

    def test_size_property(self, store):
        assert store.size == 5


# ── Retrieval ─────────────────────────────────────────────────────────────────

class TestRRFFusion:
    def _make_chunks(self, n: int) -> list[Chunk]:
        return [Chunk(id=i, text=f"chunk {i}", source="test", token_count=2) for i in range(n)]

    def test_rrf_combines_both_lists(self):
        chunks = self._make_chunks(4)
        list_a = [(chunks[0], 0.9), (chunks[1], 0.8)]
        list_b = [(chunks[2], 0.95), (chunks[0], 0.7)]
        result = rrf_fuse(list_a, list_b, k=RRF_K)
        ids = [c.id for c, _ in result]
        assert 0 in ids  # chunk[0] appears in both lists → boosted

    def test_rrf_scores_are_positive(self):
        chunks = self._make_chunks(3)
        list_a = [(chunks[0], 0.9), (chunks[1], 0.5)]
        list_b = [(chunks[1], 0.8), (chunks[2], 0.6)]
        result = rrf_fuse(list_a, list_b, k=RRF_K)
        assert all(score > 0 for _, score in result)

    def test_rrf_ordering_is_descending(self):
        chunks = self._make_chunks(4)
        list_a = [(chunks[i], float(4 - i)) for i in range(4)]
        list_b = [(chunks[i], float(4 - i)) for i in range(4)]
        result = rrf_fuse(list_a, list_b, k=RRF_K)
        scores = [s for _, s in result]
        assert scores == sorted(scores, reverse=True)

    def test_rrf_deduplicates(self):
        chunks = self._make_chunks(2)
        list_a = [(chunks[0], 0.9), (chunks[1], 0.8)]
        list_b = [(chunks[0], 0.85)]
        result = rrf_fuse(list_a, list_b, k=RRF_K)
        ids = [c.id for c, _ in result]
        assert len(ids) == len(set(ids))


class TestStrategyA:
    def test_returns_k_results(self, pipeline):
        results = pipeline.query("peak load handling", strategy="A", k=3)
        assert len(results.strategy_a) == 3

    def test_results_have_correct_strategy_label(self, pipeline):
        results = pipeline.query("load balancing", strategy="A", k=2)
        assert all(r.strategy == "A" for r in results.strategy_a)

    def test_scores_are_descending(self, pipeline):
        results = pipeline.query("cache performance Redis", strategy="A", k=3)
        scores = [r.score for r in results.strategy_a]
        assert scores == sorted(scores, reverse=True)

    def test_retrieval_path_is_faiss(self, pipeline):
        results = pipeline.query("database replica", strategy="A", k=3)
        assert all(r.retrieval_path == "faiss" for r in results.strategy_a)

    def test_expanded_query_is_none(self, pipeline):
        results = pipeline.query("scaling microservices", strategy="A", k=2)
        assert all(r.expanded_query is None for r in results.strategy_a)

    def test_relevant_chunk_in_top_results(self, pipeline):
        results = pipeline.query("peak load traffic burst autoscaling", strategy="A", k=3)
        top_texts = " ".join(r.chunk.text.lower() for r in results.strategy_a)
        assert any(kw in top_texts for kw in ["load", "traffic", "scale", "autoscal", "burst"])


class TestStrategyB:
    def test_returns_k_results(self, pipeline):
        results = pipeline.query("peak load handling", strategy="B", k=3)
        assert len(results.strategy_b) == 3

    def test_results_have_correct_strategy_label(self, pipeline):
        results = pipeline.query("caching strategy", strategy="B", k=2)
        assert all(r.strategy == "B" for r in results.strategy_b)

    def test_expanded_query_is_present(self, pipeline):
        results = pipeline.query("database scaling", strategy="B", k=3)
        assert results.expanded_query is not None
        assert len(results.expanded_query) > 0

    def test_expanded_query_is_longer_than_original(self, pipeline):
        query = "How does the system handle peak load?"
        results = pipeline.query(query, strategy="B", k=3)
        assert len(results.expanded_query) > len(query)

    def test_expansion_terms_are_populated(self, pipeline):
        results = pipeline.query("caching strategy", strategy="B", k=3)
        assert len(results.expansion_terms) > 0

    def test_retrieval_path_is_rrf_fused(self, pipeline):
        results = pipeline.query("database scaling high availability", strategy="B", k=3)
        assert all(r.retrieval_path == "rrf_fused" for r in results.strategy_b)

    @patch("backend.src.retrieval.CrossEncoderReranker.rerank")
    def test_cross_encoder_is_called(self, mock_rerank, pipeline):
        chunks = pipeline.get_chunks()[:3]
        mock_rerank.return_value = [(c, 0.9 - i * 0.1) for i, c in enumerate(chunks)]
        pipeline.query("peak load", strategy="B", k=3)
        mock_rerank.assert_called()

    @patch("backend.src.mock_vertexai.GenerativeModel.generate_content")
    def test_generative_model_is_called(self, mock_gen, pipeline):
        mock_gen.return_value = GenerativeModelResponse(
            "expanded query about load balancing traffic spikes autoscaling"
        )
        pipeline.query("peak load", strategy="B", k=3)
        mock_gen.assert_called()


# ── Full Pipeline ─────────────────────────────────────────────────────────────

class TestRAGPipeline:
    def test_ingest_returns_correct_count(self):
        p = RAGPipeline()
        report = p.ingest(CORPUS)
        assert report.doc_count == len(CORPUS)
        assert report.chunk_count == len(CORPUS)

    def test_pipeline_length_after_ingest(self):
        p = RAGPipeline()
        p.ingest(CORPUS)
        assert len(p) == len(CORPUS)

    def test_query_both_returns_both_strategies(self, pipeline):
        response = pipeline.query("peak load", strategy="both", k=3)
        assert response.strategy_a is not None
        assert response.strategy_b is not None

    def test_query_a_only(self, pipeline):
        response = pipeline.query("peak load", strategy="A", k=3)
        assert response.strategy_a is not None
        assert response.strategy_b is None

    def test_query_b_only(self, pipeline):
        response = pipeline.query("peak load", strategy="B", k=3)
        assert response.strategy_a is None
        assert response.strategy_b is not None

    def test_retrieval_time_tracked(self, pipeline):
        response = pipeline.query("load balancing", strategy="both", k=3)
        assert "A" in response.retrieval_time_ms
        assert "B" in response.retrieval_time_ms
        assert response.retrieval_time_ms["A"] >= 0
        assert response.retrieval_time_ms["B"] >= 0

    def test_system_info_fields(self, pipeline):
        info = pipeline.system_info()
        assert info.doc_count == len(CORPUS)
        assert info.embedding_dim == EMBEDDING_DIM
        assert info.bm25_enabled is True
        assert isinstance(info.embedding_model, str)
        assert isinstance(info.reranker_model, str)

    def test_get_chunks_returns_all_corpus(self, pipeline):
        chunks = pipeline.get_chunks()
        assert len(chunks) == len(CORPUS)

    def test_benchmark_queries_return_results(self, pipeline):
        for query in BENCHMARK_QUERIES:
            response = pipeline.query(query, strategy="both", k=3)
            assert response.strategy_a is not None
            assert response.strategy_b is not None
            assert len(response.strategy_a) == 3
            assert len(response.strategy_b) == 3

    @patch("backend.src.mock_vertexai.TextEmbeddingModel.get_embeddings")
    def test_vertex_embedding_model_is_mockable(self, mock_get):
        """Verifies the GCP SDK class can be patched at the import level."""
        dim = EMBEDDING_DIM
        mock_get.return_value = [TextEmbeddingResult([0.0] * dim)]
        p = RAGPipeline()
        p.ingest(["test document"])
        mock_get.assert_called()
