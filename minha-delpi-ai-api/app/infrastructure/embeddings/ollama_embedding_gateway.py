import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.infrastructure.config.embedding_config import resolve_embedding_config


logger = logging.getLogger("minha-delpi-ai-api.embeddings.ollama")


class OllamaEmbeddingGateway(EmbeddingGatewayPort):
    def __init__(self):
        config = resolve_embedding_config()
        self.base_url = config.base_url.rstrip("/")
        self.model = config.model
        self.timeout = config.timeout_seconds

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

        import os

        workers = max(
            1,
            min(
                int(os.getenv("EMBEDDING_BATCH_MAX_WORKERS", "4")),
                len(texts),
            ),
        )
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
