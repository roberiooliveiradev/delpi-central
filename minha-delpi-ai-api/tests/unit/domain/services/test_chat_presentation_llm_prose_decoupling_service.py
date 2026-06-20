"""Testes — desacoplamento prosa template vs. síntese LLM."""

from app.domain.services.chat_presentation_llm_prose_decoupling_service import (
    ChatPresentationLlmProseDecouplingService,
)
from app.domain.services.chat_presentation_render_plan_service import (
    ChatPresentationRenderPlanService,
)
from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)
from app.domain.services.chat_tool_context_presentation_service import (
    ChatToolContextPresentationService,
)


def _stack_metadata(*, markdown: str) -> dict:
    return {
        "ok": True,
        "path": "/products/90269001/factory-status",
        "textPresentation": {"type": "markdown", "markdown": markdown},
        "humanizedSummary": {
            "titulo": "Status fabril",
            "linhas": ["- OP em andamento.", "- Saldo positivo."],
        },
        "dataAnswer": {
            "profileKey": "factory_status",
            "summary": {"answer": "OP **12** em andamento."},
        },
        "tablePresentations": [
            {
                "type": "table",
                "title": "Ordens",
                "columns": [{"key": "op", "label": "OP"}],
                "rows": [{"op": "12"}],
            }
        ],
        "treePresentation": {
            "type": "tree",
            "title": "Estrutura",
            "root": {"id": "1", "label": "90269001", "children": []},
        },
        "presentationDecision": {
            "layoutMode": "stack",
            "presentationMode": "summary_then_evidence",
            "availableViews": ["text", "table", "tree"],
        },
        "stackPresentationPlan": {
            "presentationMode": "summary_then_evidence",
            "narrativeOrder": ["lead", "operationalTables", "tailVisuals"],
            "tailVisualOrder": ["tree"],
        },
    }


def test_decouple_metadata_clears_template_and_rebuilds_render_plan(monkeypatch):
    monkeypatch.setenv("CHAT_RESPONSE_MODES_ENABLED", "true")

    metadata = _stack_metadata(
        markdown="### Status fabril\n\nTemplate longo com **Destaques**.\n\n- Item A.",
    )

    assert ChatPresentationLlmProseDecouplingService.decouple_metadata(metadata)

    assert metadata["llmProseDecoupled"] is True
    assert metadata["dataOnlyPresentation"] is True
    assert metadata["textPresentation"]["markdown"] == ""
    assert metadata["presentationDecision"]["proseSource"] == "llm"
    assert metadata["templateProseArchive"]["textPresentationMarkdown"].startswith("### Status")

    segments = metadata["renderPlan"]["segments"]
    lead = next(segment for segment in segments if segment.get("slot") == "lead")

    assert lead == {
        "kind": "markdown",
        "slot": "lead",
        "source": "assistantMessage",
    }
    assert any(segment.get("kind") == "tree" for segment in segments)
    assert not any(segment.get("slot") == "highlights" for segment in segments)


def test_should_prefer_authorized_answer_false_when_decoupled():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                **_stack_metadata(markdown="### Template\n\nCorpo."),
                "llmProseDecoupled": True,
            },
        }
    ]

    assert not ChatRichPresentationTextService.should_prefer_authorized_answer_over_llm(
        tool_calls,
    )
    assert not ChatToolContextPresentationService.should_persist_authorized_tool_answer(
        tool_calls,
    )


def test_authorized_body_skips_decoupled_metadata():
    metadata = _stack_metadata(markdown="### Template\n\nCorpo.")
    metadata["llmProseDecoupled"] = True

    assert (
        ChatToolContextPresentationService._authorized_body_from_metadata(metadata) is None
    )


def test_render_plan_keeps_template_source_without_decoupling():
    metadata = _stack_metadata(markdown="### Status\n\nResumo template.")

    ChatPresentationRenderPlanService.build(metadata)

    lead = metadata["renderPlan"]["segments"][0]

    assert lead["source"] == "textPresentation"
