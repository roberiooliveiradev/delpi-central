from app.application.security.chat_permissions import CHAT_TOOLS_USE_PERMISSION
from app.application.services.assistant_capabilities_registry import (
    AssistantCapabilitiesRegistry,
)
from app.application.services.chat_capabilities_service import ChatCapabilitiesService


def test_list_features_loads_catalog():
    features = AssistantCapabilitiesRegistry.list_features()

    assert len(features) >= 8
    assert AssistantCapabilitiesRegistry.get_feature("web_search") is not None


def test_find_by_help_topic():
    feature = AssistantCapabilitiesRegistry.find_by_help_topic("canvas")

    assert feature is not None
    assert feature.get("id") == "canvas"


def test_search_estoque():
    results = AssistantCapabilitiesRegistry.search("estoque")

    assert results
    assert any(item.get("id") == "stock_lookup" for item in results)


def test_search_comercial_matches_comerciais():
    results = AssistantCapabilitiesRegistry.search("comercial")

    assert any(item.get("id") == "commercial_indicators" for item in results)


def test_resolve_availability_without_agent():
    buckets = AssistantCapabilitiesRegistry.resolve_availability(
        allowed_action_ids=[],
        action_catalog=[],
        web_search_enabled=True,
        user_permissions={CHAT_TOOLS_USE_PERMISSION},
    )

    assert any(item.get("id") == "web_search" for item in buckets["availableNow"])
    assert any(item.get("requiresAgent") for item in buckets["requiresAgent"])


def test_resolve_availability_operational_without_tools_permission():
    buckets = AssistantCapabilitiesRegistry.resolve_availability(
        allowed_action_ids=[],
        action_catalog=[],
        web_search_enabled=True,
        user_permissions=set(),
        can_use_tools=False,
    )

    assert any(item.get("id") == "stock_lookup" for item in buckets["requiresProfilePermission"])
    assert not any(item.get("id") == "stock_lookup" for item in buckets["requiresAgent"])


def test_format_release_notes_answer():
    answer = AssistantCapabilitiesRegistry.format_release_notes_answer()

    assert answer is not None
    assert "novidades" in answer.lower() or "Pesquisa" in answer


def test_release_notes_question_detection():
    assert ChatCapabilitiesService.is_release_notes_question("o que mudou na última versão?")

    answer = ChatCapabilitiesService.resolve_capability_answer(
        message="o que mudou na última versão?",
        workspace_context={},
        allowed_action_ids=[],
        action_catalog=[],
    )

    assert answer
    assert "novidade" in answer.lower() or "Pesquisa" in answer
