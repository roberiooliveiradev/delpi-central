import logging

import requests

from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.infrastructure.config.embedding_config import resolve_embedding_config


logger = logging.getLogger("minha-delpi-ai-api.embeddings.openai-compatible")


class OpenAiCompatibleEmbeddingGateway(EmbeddingGatewayPort):
    def __init__(self):
        config = resolve_embedding_config()
        self.base_url = config.base_url.rstrip("/")
        self.model = config.model
        self.api_key = config.api_key
        self.timeout = config.timeout_seconds

    def embed(self, text: str) -> list[float]:
        response = requests.post(
            f"{self.base_url}/embeddings",
            json={
                "model": self.model,
                "input": text,
            },
            headers=self._headers(),
            timeout=self.timeout,
        )

        response.raise_for_status()

        payload = response.json()
        data = payload.get("data") or []

        if not data:
            raise RuntimeError("Invalid OpenAI-compatible embedding response")

        embedding = data[0].get("embedding")

        if not isinstance(embedding, list) or not embedding:
            raise RuntimeError("Invalid embedding vector")

        return [float(value) for value in embedding]

    def _headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers
