from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger("api-delpi.similarity_embeddings")


class OllamaCaseSimilarityEmbeddingGateway:
    def __init__(self) -> None:
        self._base_url = (settings.OLLAMA_BASE_URL or "").rstrip("/")
        self._model = settings.EMBEDDING_MODEL
        self._timeout = settings.EMBEDDING_TIMEOUT_SECONDS

    def is_enabled(self) -> bool:
        return bool(settings.PAC_SIMILARITY_EMBEDDINGS_ENABLED and self._base_url and self._model)

    def embed(self, text: str) -> list[float] | None:
        if not self.is_enabled():
            return None

        response = httpx.post(
            f"{self._base_url}/api/embeddings",
            json={"model": self._model, "prompt": text},
            timeout=self._timeout,
        )
        response.raise_for_status()

        payload = response.json()
        embedding = payload.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise RuntimeError("Resposta de embedding inválida")

        return [float(value) for value in embedding]
