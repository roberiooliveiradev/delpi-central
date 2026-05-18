from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)


class FakeSettingsRepository:
    def __init__(self):
        self.payload = None

    def get_chat_intelligence_settings(self):
        return self.payload

    def save_chat_intelligence_settings(self, payload):
        self.payload = payload


def test_resolve_uses_runtime_over_env_defaults():
    repository = FakeSettingsRepository()
    repository.payload = {
        "ragContextMinScore": 0.5,
        "externalActionSemanticMinScore": 0.55,
        "externalActionSemanticRankEnabled": False,
        "chatToolRouterEnabled": False,
        "chatHistorySummaryEnabled": False,
    }

    service = ChatIntelligenceSettingsService(settings_repository=repository)
    resolved = service.resolve()

    assert resolved.rag_context_min_score == 0.5
    assert resolved.external_action_semantic_min_score == 0.55
    assert resolved.external_action_semantic_rank_enabled is False


def test_save_persists_merged_settings():
    repository = FakeSettingsRepository()
    service = ChatIntelligenceSettingsService(settings_repository=repository)

    result = service.save({"ragContextMinScore": 0.4})

    assert repository.payload["ragContextMinScore"] == 0.4
    assert result["ragContextMinScore"] == 0.4
