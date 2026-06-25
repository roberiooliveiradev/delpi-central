from __future__ import annotations


class NullCaseSimilarityEmbeddingGateway:
    def is_enabled(self) -> bool:
        return False

    def embed(self, text: str) -> list[float] | None:
        return None
