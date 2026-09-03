from app.domain.exceptions.embedding_unavailable_error import EmbeddingUnavailableError
from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort


class DisabledEmbeddingGateway(EmbeddingGatewayPort):
    def embed(self, text: str) -> list[float]:
        raise EmbeddingUnavailableError(
            "Vector embeddings are off; RAG uses keyword search only."
        )

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        raise EmbeddingUnavailableError(
            "Vector embeddings are off; RAG uses keyword search only."
        )
