from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def test_selection_reasons_keys_exist():
    keys = (
        "saleOrdersList",
        "transformaMais",
        "systemMetadata",
        "productSearchByGroup",
        "productSearchByDescription",
        "paginationRefinementDefault",
        "genericSemanticFallback",
        "lmpQuery",
        "kpiCpv",
        "kpiStockValue",
    )

    for key in keys:
        value = ExternalActionResponseContentService.get("selectionReasons", key)
        assert value, f"missing selectionReasons.{key}"


def test_rag_activity_stream_keys_exist():
    assert ChatAssistantContentService.get(
        "stream",
        "activity",
        "rag",
        "searching",
        "message",
    )
    assert ChatAssistantContentService.format(
        "stream",
        "activity",
        "rag",
        "foundSources",
        "messageTemplate",
        count=3,
    )
