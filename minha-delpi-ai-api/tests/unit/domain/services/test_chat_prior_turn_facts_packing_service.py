"""E2.S3 — packing dos fatos do turno anterior."""

from __future__ import annotations

from app.domain.services.chat_prior_turn_facts_packing_service import (
    ChatPriorTurnFactsPackingService,
)
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService


def _snapshot() -> dict:
    return {
        "operationalFocus": {
            "productCode": "10080001",
            "branch": "01",
            "period": "last_30_days",
        },
        "lastResultExcerpt": {
            "operationId": "get_product_description",
            "identityFields": {
                "code": "10080001",
                "description": "TERMINAL PINO 6MM LATAO",
            },
        },
        "lastAction": {"name": "product_description", "operationId": "get_product_description"},
        "resultSets": [
            {
                "id": "rs-1",
                "kind": "product",
                "totalCount": 7,
                "items": [
                    {"ordinal": 1, "code": "10080001", "label": "TERMINAL PINO 6MM"},
                    {"ordinal": 2, "code": "10080002", "label": "TERMINAL PINO 8MM"},
                ],
            }
        ],
        "sessionCapabilities": {
            "skills": ["sqlAuthoring", "documentVision"],
            "tools": ["get_product_stock"],
        },
    }


def test_packing_contains_identity_code_and_description():
    facts = ChatPriorTurnFactsPackingService.build(_snapshot())

    assert "10080001" in facts.text
    assert "TERMINAL PINO 6MM LATAO" in facts.text
    assert "identity" in facts.sections
    assert facts.chars == len(facts.text)
    assert facts.truncated is False


def test_packing_includes_focus_result_sets_and_capabilities():
    facts = ChatPriorTurnFactsPackingService.build(_snapshot())

    assert "Período: last_30_days" in facts.text
    assert "10080002" in facts.text
    assert "TERMINAL PINO 8MM" in facts.text
    assert "sqlAuthoring" in facts.text
    assert "get_product_stock" in facts.text
    assert set(facts.sections) >= {
        "identity",
        "focus",
        "resultSets",
        "capabilities",
    }


def test_packing_reports_remaining_items_of_the_list():
    facts = ChatPriorTurnFactsPackingService.build(_snapshot())

    assert "mais 5 item(ns)" in facts.text


def test_packing_is_empty_without_facts():
    facts = ChatPriorTurnFactsPackingService.build({})

    assert facts.is_empty
    assert facts.sections == ()
    assert facts.chars == 0


def test_packing_respects_max_chars():
    facts = ChatPriorTurnFactsPackingService.build(_snapshot(), max_chars=80)

    assert facts.truncated is True
    assert facts.chars <= 80


def test_session_capabilities_shortlist_skips_disabled_skills():
    payload = ChatPriorTurnFactsPackingService.build_session_capabilities(
        skills={"sqlAuthoring": True, "webSearch": False},
        tool_names=["action-1", "action-2"],
    )

    assert payload["skills"] == ["sqlAuthoring"]
    assert payload["tools"] == ["action-1", "action-2"]


def test_working_memory_prompt_block_carries_prior_turn_facts():
    block = ChatWorkingMemoryService.format_prompt_block(_snapshot())

    assert "Fatos do turno anterior:" in block
    assert "TERMINAL PINO 6MM LATAO" in block


def test_packing_does_not_duplicate_product_and_branch_context_items():
    """Produto/filial já são itens de contexto — packing não repete."""
    facts = ChatPriorTurnFactsPackingService.build(
        {"operationalFocus": {"productCode": "10080001", "branch": "01"}}
    )

    assert facts.is_empty
