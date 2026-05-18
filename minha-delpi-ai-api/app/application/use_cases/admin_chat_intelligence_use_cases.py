from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.infrastructure.persistence.postgres_external_action_repository import (
    PostgresExternalActionRepository,
)


class GetAdminChatIntelligenceSettingsUseCase:
    def __init__(self, service: ChatIntelligenceSettingsService | None = None):
        self.service = service or ChatIntelligenceSettingsService()

    def execute(self) -> dict:
        return self.service.to_dict()


class SaveAdminChatIntelligenceSettingsUseCase:
    def __init__(self, service: ChatIntelligenceSettingsService | None = None):
        self.service = service or ChatIntelligenceSettingsService()

    def execute(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")

        return self.service.save(payload)


class ReindexExternalActionEmbeddingsUseCase:
    def __init__(self, repository: PostgresExternalActionRepository | None = None):
        if repository is None:
            from app.composition.external_action_composer import (
                make_postgres_external_action_repository,
            )

            repository = make_postgres_external_action_repository()

        self.repository = repository

    def execute(self, *, provider_key: str | None = None) -> dict:
        return self.repository.backfill_action_embeddings(provider_key=provider_key)
