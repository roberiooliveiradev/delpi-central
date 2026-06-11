from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.infrastructure.config.settings import Settings


class FakeSettingsRepository:
    def __init__(self):
        self.payload = None

    def get_chat_intelligence_settings(self):
        return self.payload

    def save_chat_intelligence_settings(self, payload):
        self.payload = payload


def test_resolve_uses_admin_over_environment_defaults(monkeypatch):
    monkeypatch.setattr(Settings, "RAG_CONTEXT_MIN_SCORE", 0.35)
    monkeypatch.setattr(Settings, "CHAT_AGENTIC_LOOP_ENABLED", False)

    repository = FakeSettingsRepository()
    repository.payload = {
        "ragContextMinScore": 0.5,
        "agenticLoopEnabled": True,
    }

    service = ChatIntelligenceSettingsService(settings_repository=repository)
    resolved = service.resolve()

    assert resolved.rag_context_min_score == 0.5
    assert resolved.agentic_loop_enabled is True


def test_ensure_defaults_seeded_persists_only_when_empty(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_AGENTIC_LOOP_ENABLED", False)
    monkeypatch.setattr(Settings, "CHAT_TOOL_ROUTER_ENABLED", False)

    repository = FakeSettingsRepository()
    service = ChatIntelligenceSettingsService(settings_repository=repository)

    result = service.ensure_defaults_seeded()

    assert repository.payload["agenticLoopEnabled"] is False
    assert repository.payload["chatToolRouterEnabled"] is False
    assert result["source"] == "admin"

    repository.payload["agenticLoopEnabled"] = True
    monkeypatch.setattr(Settings, "CHAT_AGENTIC_LOOP_ENABLED", False)

    second = service.ensure_defaults_seeded()

    assert repository.payload["agenticLoopEnabled"] is True
    assert second["agenticLoopEnabled"] is True


def test_save_persists_and_returns_admin_values(monkeypatch):
    monkeypatch.setattr(Settings, "RAG_CONTEXT_MIN_SCORE", 0.35)

    repository = FakeSettingsRepository()
    service = ChatIntelligenceSettingsService(settings_repository=repository)

    result = service.save({"ragContextMinScore": 0.4})

    assert repository.payload["ragContextMinScore"] == 0.4
    assert result["ragContextMinScore"] == 0.4
    assert result["source"] == "admin"
