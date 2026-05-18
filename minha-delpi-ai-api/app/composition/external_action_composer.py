from app.application.services.external_actions.external_action_embedding_service import (
    ExternalActionEmbeddingService,
)
from app.composition.embedding_composer import make_embedding_cache
from app.infrastructure.embeddings.caching_embedding_gateway import CachingEmbeddingGateway
from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway
from app.infrastructure.persistence.postgres_external_action_repository import (
    PostgresExternalActionRepository,
)

_embedding_gateway: CachingEmbeddingGateway | None = None


def make_embedding_gateway() -> CachingEmbeddingGateway:
    global _embedding_gateway

    if _embedding_gateway is None:
        _embedding_gateway = CachingEmbeddingGateway(
            LocalEmbeddingGateway(),
            cache=make_embedding_cache(),
        )

    return _embedding_gateway


def get_embedding_cache_stats() -> dict | None:
    gateway = make_embedding_gateway()
    return gateway.cache_stats()


def make_postgres_external_action_repository() -> PostgresExternalActionRepository:
    return PostgresExternalActionRepository(
        embedding_service=ExternalActionEmbeddingService(
            embedding_gateway=make_embedding_gateway(),
        ),
    )
