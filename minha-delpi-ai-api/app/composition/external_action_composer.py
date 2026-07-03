from app.application.services.external_actions.external_action_embedding_service import (
    ExternalActionEmbeddingService,
)
from app.composition.embedding_composer import get_embedding_cache_stats, make_embedding_gateway
from app.infrastructure.persistence.postgres_external_action_repository import (
    PostgresExternalActionRepository,
)


def make_postgres_external_action_repository() -> PostgresExternalActionRepository:
    return PostgresExternalActionRepository(
        embedding_service=ExternalActionEmbeddingService(
            embedding_gateway=make_embedding_gateway(),
        ),
    )


__all__ = [
    "get_embedding_cache_stats",
    "make_embedding_gateway",
    "make_postgres_external_action_repository",
]
