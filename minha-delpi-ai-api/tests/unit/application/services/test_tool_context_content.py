from app.application.services.chat_tool_context_content_service import (
    ChatToolContextContentService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def test_tool_context_router_messages_exist():
    assert ChatToolContextContentService.get("router", "toolSuggested")
    assert ChatToolContextContentService.get("router", "actionSuggested")


def test_tool_context_pagination_reasons_exist():
    assert ChatToolContextContentService.get("pagination", "formatRefinement")


def test_tool_context_drawing_missing_action_supports_product_code():
    text = ChatToolContextContentService.format(
        "drawing",
        "missingAuthorizedAnalyserAction",
        product_code="90260140",
    )

    assert "90260140" in text
    assert "/products/{code}/analyser" in text


def test_presenter_stock_text_detail_header_exists():
    header = ChatAssistantContentService.get(
        "presenter_content",
        "generic",
        "stockTextDetailHeader",
    )

    assert "filial" in header.lower()
