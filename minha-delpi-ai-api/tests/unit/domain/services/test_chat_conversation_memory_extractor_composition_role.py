from app.domain.services.chat_conversation_memory_extractor import (
    ChatConversationMemoryExtractor,
)


def test_extract_last_action_prefers_primary_over_enrichment_sales():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/10090016/stock",
                "compositionRole": "primary",
            },
        },
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/10090016/sales",
                "compositionRole": "enrichment",
            },
        },
    ]

    last = ChatConversationMemoryExtractor._extract_last_action(None, tool_calls)

    assert last is not None
    assert "/stock" in str(last.get("path") or "")
    assert "sales" not in str(last.get("path") or "")
