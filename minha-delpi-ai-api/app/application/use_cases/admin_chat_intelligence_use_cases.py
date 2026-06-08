from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.domain.ports.external_action_repository_port import ExternalActionRepositoryPort


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
    def __init__(self, repository: ExternalActionRepositoryPort):
        self.repository = repository

    def execute(self, *, provider_key: str | None = None) -> dict:
        return self.repository.backfill_action_embeddings(provider_key=provider_key)
