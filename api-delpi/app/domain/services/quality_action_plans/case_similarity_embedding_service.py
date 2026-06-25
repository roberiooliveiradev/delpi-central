"""Embeddings de search_text para busca semântica PAC (Onda 6)."""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger("api-pac-quality.similarity_embeddings")

DEFAULT_EMBEDDING_DIMENSIONS = 1024


class CaseSimilarityEmbeddingPort(Protocol):
    def is_enabled(self) -> bool: ...

    def embed(self, text: str) -> list[float] | None: ...


class CaseSimilarityEmbeddingService:
    @staticmethod
    def fit_dimensions(
        values: list[float],
        *,
        dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
    ) -> list[float]:
        if len(values) == dimensions:
            return values
        if len(values) > dimensions:
            return values[:dimensions]
        return [*values, *([0.0] * (dimensions - len(values)))]

    @staticmethod
    def format_pgvector_literal(values: list[float]) -> str:
        return "[" + ",".join(f"{value:.8f}" for value in values) + "]"

    @classmethod
    def embed_search_text(
        cls,
        gateway: CaseSimilarityEmbeddingPort,
        text: str,
        *,
        dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
    ) -> list[float] | None:
        if not gateway.is_enabled():
            return None

        normalized = " ".join(str(text or "").split())
        if not normalized:
            return None

        try:
            embedding = gateway.embed(normalized)
        except Exception:
            logger.warning("Falha ao gerar embedding PAC", exc_info=True)
            return None

        if not embedding:
            return None

        return cls.fit_dimensions(embedding, dimensions=dimensions)
