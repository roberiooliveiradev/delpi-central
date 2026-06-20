"""Testes — gate canônico template × LLM × direct."""

import pytest

from app.domain.services.chat_presentation_prose_delivery_service import (
    ChatPresentationProseDeliveryService,
    MODE_DIRECT,
    MODE_LLM,
    MODE_TEMPLATE,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService


def _stack_tool_calls(*, markdown: str = "### Status\n\nTemplate.") -> list[dict]:
    return [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90269001/factory-status",
                "textPresentation": {"type": "markdown", "markdown": markdown},
                "humanizedSummary": {"titulo": "Status", "linhas": ["- OP 12."]},
                "dataAnswer": {
                    "profileKey": "factory_status",
                    "summary": {"answer": "OP em andamento."},
                },
                "presentationDecision": {
                    "layoutMode": "stack",
                    "presentationMode": "summary_then_evidence",
                },
                "stackPresentationPlan": {
                    "presentationMode": "summary_then_evidence",
                    "narrativeOrder": ["lead", "tailVisuals"],
                    "tailVisualOrder": ["tree"],
                },
                "treePresentation": {
                    "type": "tree",
                    "title": "Estrutura",
                    "root": {"id": "1", "label": "90269001", "children": []},
                },
            },
        }
    ]


@pytest.mark.parametrize(
    ("message", "tool_calls", "expected"),
    [
        (
            "como esta o status fabril do produto 90269001?",
            _stack_tool_calls(),
            MODE_LLM,
        ),
    ],
)
def test_resolve_mode_narrative_vs_llm(monkeypatch, message, tool_calls, expected):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    mode = ChatPresentationProseDeliveryService.resolve_mode(message, tool_calls)

    assert mode == expected


def test_resolve_mode_template_when_response_modes_disabled(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: False)

    mode = ChatPresentationProseDeliveryService.resolve_mode(
        "como esta o status fabril do produto 90269001?",
        _stack_tool_calls(),
    )

    assert mode == MODE_TEMPLATE


def test_resolve_mode_direct_for_playbook_single_table():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90269001/stock",
                "apiDelpiResponseMeta": {"entity": "product_stock"},
                "humanizedSummary": {
                    "titulo": "Estoque",
                    "linhas": ["Saldo 150 un."],
                },
                "presentation": {
                    "type": "table",
                    "title": "Estoque",
                    "columns": [],
                    "rows": [],
                },
                "presentationDecision": {
                    "selected": "table",
                    "layoutMode": "single",
                },
            },
        }
    ]

    mode = ChatPresentationProseDeliveryService.resolve_mode(
        "qual o saldo na filial 01?",
        tool_calls,
    )

    assert mode == MODE_DIRECT


def test_apply_turn_decouples_and_stamps_delivery_mode(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    tool_calls = _stack_tool_calls()
    mode = ChatPresentationProseDeliveryService.apply_turn(
        "como esta o status fabril do produto 90269001?",
        tool_calls,
    )

    metadata = tool_calls[0]["metadata"]

    assert mode == MODE_LLM
    assert metadata["llmProseDecoupled"] is True
    assert metadata["proseDeliveryMode"] == MODE_LLM
    assert metadata["textPresentation"]["markdown"] == ""
    assert metadata["humanizedSummary"]["linhas"] == []


def test_is_llm_decoupled_metadata_reads_prose_source():
    assert ChatPresentationProseDeliveryService.is_llm_decoupled_metadata(
        {"presentationDecision": {"proseSource": "llm"}},
    )
