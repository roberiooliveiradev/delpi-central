from uuid import uuid4

from app.application.services.chat_assistant_catalog_service import (
    ChatAssistantCatalogService,
)


class _StubAgentRepository:
    def get_enabled_by_id(self, agent_id, user_id=None):
        return None

    def list_enabled_action_ids(self, agent_id, user_id=None):
        return []


def test_build_response_without_query():
    service = ChatAssistantCatalogService(agent_repository=_StubAgentRepository())
    payload = service.build_response(user_id=uuid4())

    assert payload["version"]
    assert len(payload["features"]) >= 8
    assert payload["quickPrompts"]
    assert "availableNow" in payload["availability"]
    assert payload["categories"]


def test_build_response_search_estoque():
    service = ChatAssistantCatalogService(agent_repository=_StubAgentRepository())
    payload = service.build_response(user_id=uuid4(), query="estoque", limit=8)

    assert payload["query"] == "estoque"
    assert any(item.get("id") == "stock_lookup" for item in payload["features"])
