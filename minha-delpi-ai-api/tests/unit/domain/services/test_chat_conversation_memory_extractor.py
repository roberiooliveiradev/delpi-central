from app.domain.services.chat_conversation_memory_extractor import (
    ChatConversationMemoryExtractor,
)


def test_enrich_snapshot_extracts_last_action():
    snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
        {"operationalFocus": {}},
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


def test_enrich_snapshot_extracts_last_result_excerpt():
    snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
        {"operationalFocus": {}},
        previous_messages=[],
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/products/90260149/structure",
                    "presentation": {
                        "type": "tree",
                        "title": "Estrutura do produto 90260149",
                    },
                    "responsePreview": (
                        '{"items":[{"code":"10380044"},{"code":"10380045"}]}'
                    ),
                },
            }
        ],
    )

    excerpt = snapshot.get("lastResultExcerpt") or {}

    assert excerpt.get("presentationType") == "tree"
    assert excerpt.get("topKeys")
