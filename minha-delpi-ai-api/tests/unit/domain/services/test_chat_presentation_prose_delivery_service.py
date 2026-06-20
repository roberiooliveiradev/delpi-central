"""Testes — gate canônico template × LLM × direct."""

import pytest

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_prose_delivery_service import (
    ChatPresentationProseDeliveryService,
    MODE_DIRECT,
    MODE_LLM,
    MODE_TEMPLATE,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService

configure_domain_infrastructure_ports()


def _stack_tool_calls(*, markdown: str = "### Status\n\nTemplate.") -> list[dict]:
    return [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90269001/factory-status",
                "apiDelpiResponseMeta": {"entity": "product_factory_status"},
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


def test_resolve_mode_template_when_response_modes_disabled_and_fallback_allowed(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: False)
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "llm_prose_everywhere",
        lambda: False,
    )
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "deprecate_humanized_linhas_as_prose",
        lambda: False,
    )
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "allow_template_prose_fallback",
        lambda: True,
    )

    mode = ChatPresentationProseDeliveryService.resolve_mode(
        "como esta o status fabril do produto 90269001?",
        _stack_tool_calls(),
    )

    assert mode == MODE_TEMPLATE


def test_resolve_mode_llm_when_response_modes_disabled_and_no_template_fallback(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: False)

    mode = ChatPresentationProseDeliveryService.resolve_mode(
        "como esta o status fabril do produto 90269001?",
        _stack_tool_calls(),
    )

    assert mode == MODE_LLM


def test_template_prose_allowed_false_when_everywhere(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: False)

    assert not ChatPresentationProseDeliveryService.template_prose_allowed()


def test_resolve_mode_llm_when_response_modes_disabled_but_require_flag_false(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: False)
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "require_response_modes_for_llm_prose",
        lambda: False,
    )

    mode = ChatPresentationProseDeliveryService.resolve_mode(
        "como esta o status fabril do produto 90269001?",
        _stack_tool_calls(),
    )

    assert mode == MODE_LLM


def test_should_skip_template_prose_when_modes_disabled_but_require_flag_false(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: False)
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "require_response_modes_for_llm_prose",
        lambda: False,
    )

    assert ChatPresentationProseDeliveryService.should_skip_template_prose_in_pipeline(
        "qual o status do produto 90269002 na fabrica hoje?",
        path="/products/90269002/factory-status",
    )


def test_llm_prose_globally_available_respects_require_flag(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: False)
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "require_response_modes_for_llm_prose",
        lambda: True,
    )
    assert not ChatPresentationProseDeliveryService.llm_prose_globally_available()

    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "require_response_modes_for_llm_prose",
        lambda: False,
    )
    assert ChatPresentationProseDeliveryService.llm_prose_globally_available()


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

    assert mode == MODE_LLM


def test_resolve_mode_direct_when_llm_everywhere_disabled(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "llm_prose_everywhere",
        lambda: False,
    )

    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90269001/stock",
                "apiDelpiResponseMeta": {"entity": "product_stock"},
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


def test_apply_to_tool_context_result_decouples_executed_tools(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    tool_context = {
        "context": "tool output",
        "toolCalls": _stack_tool_calls(),
    }

    mode = ChatPresentationProseDeliveryService.apply_to_tool_context_result(
        tool_context,
        "qual o status do produto 90269002 na fabrica hoje?",
    )

    assert mode == MODE_LLM
    metadata = tool_context["toolCalls"][0]["metadata"]
    assert metadata.get("llmProseDecoupled") is True


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


def test_entity_template_profile_uses_llm_when_everywhere(monkeypatch):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    tool_calls = _stack_tool_calls()
    tool_calls[0]["metadata"]["apiDelpiResponseMeta"] = {
        "entity": "production_consumption_top_items",
    }

    mode = ChatPresentationProseDeliveryService.resolve_mode(
        "como esta o status fabril do produto 90269001?",
        tool_calls,
    )

    assert mode == MODE_LLM


def test_playbook_entity_uses_llm_when_template_fallback_disabled(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "llm_prose_everywhere",
        lambda: False,
    )
    monkeypatch.setattr(
        ChatPresentationProseDeliveryService,
        "_entity_prose_delivery_mode",
        lambda **kwargs: MODE_TEMPLATE,
    )

    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/production/consumption/top-items",
                "apiDelpiResponseMeta": {
                    "entity": "production_consumption_top_items",
                },
                "presentationDecision": {
                    "selected": "table",
                    "layoutMode": "single",
                },
            },
        }
    ]

    mode = ChatPresentationProseDeliveryService.resolve_mode(
        "quais os top itens de consumo na producao?",
        tool_calls,
    )

    assert mode == MODE_LLM


def test_playbook_entity_template_only_with_explicit_offline_fallback(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: False)
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "llm_prose_everywhere",
        lambda: False,
    )
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "deprecate_humanized_linhas_as_prose",
        lambda: False,
    )
    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "allow_template_prose_fallback",
        lambda: True,
    )
    monkeypatch.setattr(
        ChatPresentationProseDeliveryService,
        "_entity_prose_delivery_mode",
        lambda **kwargs: MODE_TEMPLATE,
    )

    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/production/consumption/top-items",
                "apiDelpiResponseMeta": {
                    "entity": "production_consumption_top_items",
                },
                "presentationDecision": {
                    "selected": "table",
                    "layoutMode": "single",
                },
            },
        }
    ]

    mode = ChatPresentationProseDeliveryService.resolve_mode(
        "listagem top consumo",
        tool_calls,
    )

    assert mode == MODE_TEMPLATE


def test_resolve_effective_humanized_summary_uses_archive_when_decoupled():
    metadata = {
        "llmProseDecoupled": True,
        "proseDeliveryMode": "llm",
        "humanizedSummary": {"titulo": "Status fabril", "linhas": []},
        "templateProseArchive": {
            "humanizedSummary": {
                "titulo": "Status fabril",
                "linhas": ["- OP **12345** em andamento."],
            },
        },
    }

    effective = ChatPresentationProseDeliveryService.resolve_effective_humanized_summary(
        metadata,
    )

    assert effective is not None
    assert effective["linhas"] == ["- OP **12345** em andamento."]


def test_should_block_template_prose_metadata_when_data_only():
    metadata = {
        "dataOnlyPresentation": True,
        "humanizedSummary": {"titulo": "KPI", "linhas": ["- legado"]},
    }

    assert ChatPresentationProseDeliveryService.should_block_template_prose_metadata(metadata)
    assert ChatPresentationProseDeliveryService.resolve_humanized_lines_for_display(metadata) == []
    assert ChatPresentationProseDeliveryService.resolve_humanized_detail_lines_for_display(
        metadata,
    ) == []


def test_resolve_humanized_lines_for_facts_uses_archive_when_decoupled():
    metadata = {
        "llmProseDecoupled": True,
        "humanizedSummary": {"titulo": "Status", "linhas": []},
        "templateProseArchive": {
            "humanizedSummary": {"linhas": ["- fato arquivado."]},
        },
    }

    assert ChatPresentationProseDeliveryService.resolve_humanized_lines_for_facts(metadata) == [
        "- fato arquivado.",
    ]
