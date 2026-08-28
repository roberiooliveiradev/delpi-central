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


def test_enrich_snapshot_merges_request_parameters_from_metadata():
    snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
        {"operationalFocus": {}},
        previous_messages=[],
        tool_calls=[
            {
                "name": "execute_external_action",
                "arguments": {
                    "parameters": {"branch": "all"},
                },
                "metadata": {
                    "ok": True,
                    "path": "/financial/rol",
                    "apiRouteDomain": "financial_kpi",
                    "parameterStrategy": "date_branch",
                    "requestParameters": {
                        "branch": "all",
                        "start_date": "01-08-2026",
                        "end_date": "28-08-2026",
                    },
                },
            }
        ],
    )

    last_action = snapshot["lastAction"]
    assert last_action["params"]["branch"] == "all"
    assert last_action["params"]["start_date"] == "01-08-2026"
    assert last_action["params"]["end_date"] == "28-08-2026"
    assert last_action["apiRouteDomain"] == "financial_kpi"
    assert last_action["parameterStrategy"] == "date_branch"


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
