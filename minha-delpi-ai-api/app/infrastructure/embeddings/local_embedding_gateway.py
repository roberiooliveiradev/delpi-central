import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.infrastructure.config.settings import Settings


logger = logging.getLogger("minha-delpi-ai-api.embeddings")


class LocalEmbeddingGateway(EmbeddingGatewayPort):
    def __init__(self):
        self.base_url = Settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = Settings.EMBEDDING_MODEL
        self.timeout = Settings.EMBEDDING_TIMEOUT_SECONDS

    def embed(self, text: str) -> list[float]:
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        payload = response.json()
        embedding = payload.get("embedding")

        if not isinstance(embedding, list) or not embedding:
            raise RuntimeError("Invalid embedding response")

        return [float(value) for value in embedding]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if len(texts) == 1:
            return [self.embed(texts[0])]

        workers = max(1, min(Settings.EMBEDDING_BATCH_MAX_WORKERS, len(texts)))
        results: list[list[float] | None] = [None] * len(texts)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self.embed, text): index
                for index, text in enumerate(texts)
            }

            for future in as_completed(futures):
                index = futures[future]
                results[index] = future.result()

        return [embedding for embedding in results if embedding is not None]
