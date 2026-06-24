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


def test_should_not_skip_template_prose_when_profile_uses_template_even_if_llm_everywhere(
    monkeypatch,
):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)
    monkeypatch.setattr(
        ChatPresentationProseDeliveryService,
        "_entity_prose_delivery_mode",
        lambda **kwargs: MODE_TEMPLATE,
    )

    assert not ChatPresentationProseDeliveryService.should_skip_template_prose_in_pipeline(
        "quais MPs exclusivas tem o produto 90260882?",
        path="/products/90260882/structure/exclusivity",
    )


def test_resolve_mode_structure_exclusivity_uses_template_even_with_llm_everywhere(
    monkeypatch,
):
    monkeypatch.setattr(ChatResponseModeService, "is_enabled", lambda: True)

    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90260882/structure/exclusivity",
                "apiDelpiResponseMeta": {"entity": "product_structure_exclusivity"},
                "textPresentation": {
                    "type": "markdown",
                    "markdown": (
                        "**Resposta:** Não — nenhuma MP exclusiva; "
                        "as **3** matérias-primas são compartilhadas com outros PAs."
                    ),
                },
                "presentationDecision": {
                    "layoutMode": "stack",
                    "selected": "text",
                },
            },
        }
    ]

    mode = ChatPresentationProseDeliveryService.resolve_mode(
        "quais MPs exclusivas tem o produto 90260882?",
        tool_calls,
    )

    assert mode == MODE_TEMPLATE


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


def test_explicit_template_profile_wins_even_when_playbook_entity(monkeypatch):
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

    assert mode == MODE_TEMPLATE


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
        lambda **kwargs: MODE_LLM,
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


def test_resolve_llm_synthesis_answer_fallback_uses_data_commentary_when_empty():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "llmProseDecoupled": True,
                "dataCommentary": {
                    "highlights": [{"text": "O produto **10080045** está cadastrado como MP."}],
                    "attention": ["Roteiro não retornado."],
                    "nextAction": "Valide roteiro com engenharia.",
                },
            },
        }
    ]

    fallback = ChatPresentationProseDeliveryService.resolve_llm_synthesis_answer_fallback(
        "",
        tool_calls,
    )

    assert "10080045" in fallback
    assert "Roteiro não retornado" in fallback
    assert "engenharia" in fallback.lower()


def test_resolve_llm_synthesis_answer_fallback_keeps_nonempty_llm_answer():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "llmProseDecoupled": True,
                "dataCommentary": {
                    "summary": "Resumo da API que não deve substituir o LLM.",
                },
            },
        }
    ]
    llm_answer = "Resposta sintetizada pelo modelo com contexto operacional suficiente."

    result = ChatPresentationProseDeliveryService.resolve_llm_synthesis_answer_fallback(
        llm_answer,
        tool_calls,
    )

    assert result == llm_answer


def test_ensure_product_code_in_synthesis_prose_prefixes_when_missing():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/10080045/analyser",
                "llmProseDecoupled": True,
            },
        }
    ]

    result = ChatPresentationProseDeliveryService.ensure_product_code_in_synthesis_prose(
        "Produto cadastrado como MP com roteiro vazio.",
        "me fale do produto 10080045",
        tool_calls,
    )

    assert "10080045" in result
    assert result.startswith("O produto **10080045**")


def test_finalize_llm_synthesis_answer_applies_fallback_and_product_code():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/10080045/analyser",
                "llmProseDecoupled": True,
                "dataCommentary": {
                    "highlights": [{"text": "Cadastro MP confirmado nos dados consultados."}],
                },
            },
        }
    ]

    result = ChatPresentationProseDeliveryService.finalize_llm_synthesis_answer(
        "",
        tool_calls,
        message="me fale do produto 10080045",
        response_mode_effect="llm_synthesis_brief",
    )

    assert "10080045" in result
    assert "MP" in result


def test_compact_fallback_skips_verbose_summary_lines():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/10080045/analyser",
                "llmProseDecoupled": True,
                "dataCommentary": {
                    "highlights": [{"text": "Cadastro MP confirmado."}],
                    "summaryLines": [
                        "- **Estrutura**: Nenhum registro (0)",
                        "- **Roteiro**: Nenhum registro (0)",
                    ],
                    "attention": ["Roteiro vazio."],
                },
            },
        }
    ]

    fallback = ChatPresentationProseDeliveryService.resolve_llm_synthesis_answer_fallback(
        "",
        tool_calls,
        compact=True,
    )

    assert "Cadastro MP" in fallback
    assert "Estrutura" not in fallback
    assert "Pontos de atenção" not in fallback
