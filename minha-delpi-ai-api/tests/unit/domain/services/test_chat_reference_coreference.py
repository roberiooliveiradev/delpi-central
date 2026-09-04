"""E3.S2 — correferência (esse/ele/anterior/segundo) apoiada em resultSets."""

from __future__ import annotations

from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)


def _result_set(items: list[tuple[str, str]]) -> list[dict]:
    return [
        {
            "id": "rs-1",
            "kind": "product",
            "totalCount": len(items),
            "items": [
                {"ordinal": index, "code": code, "label": label}
                for index, (code, label) in enumerate(items, start=1)
            ],
        }
    ]


def _resolve(message: str, snapshot: dict):
    return ChatReferenceResolutionService.resolve_from_snapshot(message, snapshot)


def _values(resolved: list[dict], resolved_to: str) -> list[str]:
    return [item["value"] for item in resolved if item["resolvedTo"] == resolved_to]


def test_pronoun_resolves_to_single_item_of_previous_list():
    resolved, used = _resolve(
        "qual o estoque dele?",
        {"resultSets": _result_set([("10080001", "TERMINAL PINO 6MM")])},
    )

    assert _values(resolved, "resultSetItem") == ["10080001"]
    assert "resultSets" in used


def test_list_scope_reference_resolves_single_item():
    resolved, _ = _resolve(
        "me mostra os dados da lista",
        {"resultSets": _result_set([("10080001", "TERMINAL PINO 6MM")])},
    )

    assert _values(resolved, "resultSetItem") == ["10080001"]


def test_pronoun_falls_back_to_operational_focus_product():
    resolved, used = _resolve(
        "quais fornecedores dele?",
        {"operationalFocus": {"productCode": "10080001"}},
    )

    assert "10080001" in _values(resolved, "productCode")
    assert "productCode" in used


def test_pronoun_with_multi_item_list_does_not_guess_an_item():
    resolved, _ = _resolve(
        "qual o estoque dele?",
        {
            "resultSets": _result_set(
                [("10080001", "TERMINAL PINO"), ("10080002", "TERMINAL OLHAL")]
            )
        },
    )

    assert _values(resolved, "resultSetItem") == []


def test_previous_item_reference_resolves_penultimate_code():
    resolved, _ = _resolve(
        "volta para o item anterior",
        {
            "resultSets": _result_set(
                [
                    ("10080001", "TERMINAL PINO"),
                    ("10080002", "TERMINAL OLHAL"),
                    ("10080003", "TERMINAL FEMEA"),
                ]
            )
        },
    )

    assert _values(resolved, "resultSetItem") == ["10080002"]


def test_ordinal_reference_still_wins_over_pronoun_coreference():
    resolved, _ = _resolve(
        "estoque do segundo",
        {
            "resultSets": _result_set(
                [("10080001", "TERMINAL PINO"), ("10080002", "TERMINAL OLHAL")]
            )
        },
    )

    assert _values(resolved, "resultSetItem") == ["10080002"]


def test_explicit_code_in_message_disables_coreference():
    resolved, _ = _resolve(
        "qual o estoque dele 10080009?",
        {"operationalFocus": {"productCode": "10080001"}},
    )

    assert "10080001" not in _values(resolved, "productCode")


def test_message_without_coreference_marker_resolves_nothing_extra():
    resolved, _ = _resolve(
        "bom dia",
        {"resultSets": _result_set([("10080001", "TERMINAL PINO")])},
    )

    assert _values(resolved, "resultSetItem") == []
