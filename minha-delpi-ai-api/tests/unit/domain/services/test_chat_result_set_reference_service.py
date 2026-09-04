"""E2.S2 — resultSets na memória de trabalho e resolução de ordinais."""

from __future__ import annotations

import json

from app.domain.services.chat_conversation_memory_extractor import (
    ChatConversationMemoryExtractor,
)
from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)
from app.domain.services.chat_result_set_reference_service import (
    ChatResultSetReferenceService,
)


def _search_tool_call() -> dict:
    return {
        "name": "execute_external_action",
        "arguments": {"parameters": {"description": "terminal pino"}},
        "metadata": {
            "ok": True,
            "operationId": "search_products",
            "path": "/products/search",
            "tablePresentations": [
                {
                    "title": "Produtos encontrados",
                    "rows": [
                        {"product_code": "10080001", "description": "TERMINAL PINO 6MM"},
                        {"product_code": "10080002", "description": "TERMINAL PINO 8MM"},
                        {"product_code": "10080003", "description": "TERMINAL PINO 10MM"},
                        {"product_code": "10080004", "description": "TERMINAL PINO 12MM"},
                    ],
                }
            ],
        },
    }


def _generic_tool_call() -> dict:
    return {
        "name": "execute_external_action",
        "arguments": {"parameters": {}},
        "metadata": {
            "ok": True,
            "operationId": "list_branches",
            "path": "/branches",
            "responsePreview": json.dumps(
                {
                    "data": {
                        "items": [
                            {"code": "01", "name": "Matriz"},
                            {"code": "02", "name": "Filial ES"},
                        ]
                    }
                }
            ),
        },
    }


def test_build_result_sets_from_table_rows_keeps_code_and_label():
    sets = ChatResultSetReferenceService.build_result_sets(
        tool_calls=[_search_tool_call()],
        message_id="msg-1",
    )

    assert len(sets) == 1
    result_set = sets[0]
    assert result_set["kind"] == "product"
    assert result_set["totalCount"] == 4
    assert result_set["items"][1] == {
        "ordinal": 2,
        "code": "10080002",
        "label": "TERMINAL PINO 8MM",
    }
    assert result_set["messageId"] == "msg-1"


def test_build_result_sets_marks_non_product_payload_as_generic():
    sets = ChatResultSetReferenceService.build_result_sets(
        tool_calls=[_generic_tool_call()],
    )

    assert len(sets) == 1
    assert sets[0]["kind"] == "generic"
    assert [item["code"] for item in sets[0]["items"]] == ["01", "02"]


def test_snapshot_enrichment_persists_result_sets():
    snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
        {"operationalFocus": {}},
        previous_messages=[],
        tool_calls=[_search_tool_call()],
    )

    assert snapshot["resultSets"]
    assert snapshot["resultSets"][0]["items"][0]["code"] == "10080001"


def test_result_sets_survive_turn_without_new_listing():
    first = ChatConversationMemoryExtractor.enrich_snapshot(
        {"operationalFocus": {}},
        previous_messages=[],
        tool_calls=[_search_tool_call()],
    )
    second = ChatConversationMemoryExtractor.enrich_snapshot(
        first,
        previous_messages=[],
        tool_calls=[],
    )

    assert second["resultSets"] == first["resultSets"]


def test_ordinal_reference_resolves_second_item_code():
    snapshot = {
        "operationalFocus": {},
        "resultSets": ChatResultSetReferenceService.build_result_sets(
            tool_calls=[_search_tool_call()],
        ),
    }

    resolved, used = ChatReferenceResolutionService.resolve_from_snapshot(
        "estoque do segundo",
        snapshot,
    )

    entry = next(item for item in resolved if item["resolvedTo"] == "resultSetItem")
    assert entry["value"] == "10080002"
    assert entry["label"] == "TERMINAL PINO 8MM"
    assert "resultSets" in used


def test_range_reference_resolves_three_first_codes():
    snapshot = {
        "resultSets": ChatResultSetReferenceService.build_result_sets(
            tool_calls=[_search_tool_call()],
        ),
    }

    codes = ChatResultSetReferenceService.resolve_codes(
        "me mostra o estoque dos tres primeiros",
        snapshot,
    )

    assert codes == ["10080001", "10080002", "10080003"]


def test_last_item_reference_resolves_last_code():
    snapshot = {
        "resultSets": ChatResultSetReferenceService.build_result_sets(
            tool_calls=[_search_tool_call()],
        ),
    }

    assert ChatResultSetReferenceService.resolve_codes(
        "e o ultimo?",
        snapshot,
    ) == ["10080004"]


def test_item_number_reference_resolves_by_position():
    snapshot = {
        "resultSets": ChatResultSetReferenceService.build_result_sets(
            tool_calls=[_search_tool_call()],
        ),
    }

    assert ChatResultSetReferenceService.resolve_codes(
        "detalha o item 3",
        snapshot,
    ) == ["10080003"]


def test_ordinal_without_result_sets_resolves_nothing():
    resolved, used = ChatReferenceResolutionService.resolve_from_snapshot(
        "estoque do segundo",
        {"operationalFocus": {}},
    )

    assert not [item for item in resolved if item["resolvedTo"] == "resultSetItem"]
    assert "resultSets" not in used


def test_message_without_ordinal_does_not_resolve_result_set():
    snapshot = {
        "resultSets": ChatResultSetReferenceService.build_result_sets(
            tool_calls=[_search_tool_call()],
        ),
    }

    assert ChatResultSetReferenceService.resolve_codes(
        "qual o estoque do 10080001?",
        snapshot,
    ) == []
