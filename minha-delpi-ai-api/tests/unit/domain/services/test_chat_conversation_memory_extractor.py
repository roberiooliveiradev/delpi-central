from app.domain.services.chat_conversation_memory_extractor import (
    ChatConversationMemoryExtractor,
)


def test_enrich_snapshot_extracts_last_action():
    snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
        {"lastEntities": {}},
        previous_messages=[],
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "path": "/products/10080001/stock"},
            }
        ],
    )

    assert snapshot["lastAction"]["name"] == "stock_lookup"
    assert snapshot["lastAction"]["params"]["productCode"] == "10080001"
