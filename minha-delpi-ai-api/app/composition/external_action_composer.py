from app.application.services.external_actions.external_action_embedding_service import (
    ExternalActionEmbeddingService,
)
from app.infrastructure.embeddings.caching_embedding_gateway import CachingEmbeddingGateway
from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway


def make_embedding_gateway() -> CachingEmbeddingGateway:
    return CachingEmbeddingGateway(LocalEmbeddingGateway())
from app.infrastructure.persistence.postgres_external_action_repository import (
    PostgresExternalActionRepository,
)


def make_postgres_external_action_repository() -> PostgresExternalActionRepository:
    return PostgresExternalActionRepository(
        embedding_service=ExternalActionEmbeddingService(
            embedding_gateway=make_embedding_gateway(),
        ),
    )
