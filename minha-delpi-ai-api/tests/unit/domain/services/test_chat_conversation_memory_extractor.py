from app.domain.services.chat_conversation_memory_extractor import (
    ChatConversationMemoryExtractor,
)


def test_enrich_snapshot_extracts_recent_metric_snapshots_from_prose():
    snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
        {"operationalFocus": {}},
        previous_messages=[
            {
                "role": "assistant",
                "content": "**ROL:** R$ 4.229.441,28",
            },
            {
                "role": "assistant",
                "content": "Consulta filtrada pela filial 01.\n\n**ROL:** R$ 676.062,44",
                "metadata": {
                    "toolCalls": [
                        {
                            "name": "execute_external_action",
                            "arguments": {"parameters": {"branch": "01"}},
                            "metadata": {"ok": True, "path": "/financial/rol"},
                        }
                    ]
                },
            },
        ],
    )
    snaps = snapshot.get("recentMetricSnapshots") or []
    assert len(snaps) >= 2
    assert any(abs(float(s["value"]) - 4229441.28) < 0.01 for s in snaps)
    assert any(
        abs(float(s["value"]) - 676062.44) < 0.01 and s.get("branch") == "01"
        for s in snaps
    )
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


def test_enrich_snapshot_keeps_prior_last_action_when_current_tool_fails():
    prior_messages = [
        {
            "role": "assistant",
            "id": "m0",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/financial/rol",
                            "actionId": "api_delpi.financial.get_financial_rol",
                            "apiDelpiResponseMeta": {"operationId": "get_financial_rol"},
                            "requestParameters": {
                                "start_date": "01-08-2026",
                                "end_date": "31-08-2026",
                            },
                        },
                    }
                ]
            },
        }
    ]
    snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
        {"operationalFocus": {}},
        previous_messages=prior_messages,
        tool_calls=[
            {
                "name": "execute_external_action",
                "arguments": {"parameters": {"branch": "01", "limit": 10}},
                "metadata": {
                    "ok": False,
                    "path": "/financial/rol",
                    "error": "Unknown parameter: limit",
                },
            }
        ],
    )

    last_action = snapshot["lastAction"]
    assert last_action["path"] == "/financial/rol"
    assert last_action["params"]["start_date"] == "01-08-2026"
    assert "limit" not in last_action["params"]


def test_enrich_snapshot_operation_id_from_api_delpi_response_meta():
    snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
        {"operationalFocus": {}},
        previous_messages=[],
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/financial/rol",
                    "actionId": "api_delpi.financeiro.get_financial_rol",
                    "apiDelpiResponseMeta": {"operationId": "get_financial_rol"},
                },
            }
        ],
    )

    last_action = snapshot["lastAction"]
    assert last_action["operationId"] == "get_financial_rol"
    assert last_action["actionId"] == "api_delpi.financeiro.get_financial_rol"


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
