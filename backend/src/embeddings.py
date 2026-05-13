"""
Embedding provider abstraction layer.

Defines EmbeddingProvider as an abstract interface so the concrete
implementation can be swapped (mock → real Vertex AI) without touching
any retrieval or pipeline code.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """
    Abstract interface for embedding providers.

    Production swap: replace MockEmbeddingProvider with a VertexEmbeddingProvider
    that wraps the real vertexai.language_models.TextEmbeddingModel.
    """

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """
        Returns a float32 numpy array of shape (len(texts), embedding_dim).
        All vectors are L2-normalized (unit norm), ready for cosine similarity
        via inner product (FAISS IndexFlatIP).
        """
        ...

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """Dimensionality of output vectors."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier for observability."""
        ...


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider backed by MockTextEmbeddingModel.

    Internally uses sentence-transformers/all-MiniLM-L6-v2 to produce
    384-dimensional L2-normalized embeddings, simulating the behavior of
    Vertex AI's textembedding-gecko@003.
    """

    def __init__(self) -> None:
        from backend.src.mock_vertexai import TextEmbeddingModel
        from backend.config.settings import VERTEX_MODEL_NAME, EMBEDDING_DIM

        self._model = TextEmbeddingModel.from_pretrained(VERTEX_MODEL_NAME)
        self._dim = EMBEDDING_DIM
        self._vertex_name = VERTEX_MODEL_NAME
        logger.info("MockEmbeddingProvider ready (dim=%d)", self._dim)

    def embed(self, texts: list[str]) -> np.ndarray:
        results = self._model.get_embeddings(texts)
        vectors = np.array([r.values for r in results], dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Guard against zero-norm edge case
        vectors = vectors / np.where(norms > 1e-8, norms, 1.0)
        return vectors

    @property
    def embedding_dim(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return f"MockEmbeddingProvider → {self._vertex_name} (all-MiniLM-L6-v2 local)"
