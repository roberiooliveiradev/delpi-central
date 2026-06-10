from app.domain.services.chat_presentation_evidence_first_layout_service import (
    ChatPresentationEvidenceFirstLayoutService,
)
from app.domain.services.chat_presentation_stack_order_service import (
    ChatPresentationStackOrderService,
)


def test_activate_sets_presentation_mode_when_data_answer_has_answer():
    metadata = {
        "dataAnswer": {
            "summary": {"answer": "Situação fabril consolidada.", "riskLevel": "ok"},
        },
    }

    assert ChatPresentationEvidenceFirstLayoutService.activate(metadata) is True
    assert (
        metadata["presentationDecision"]["presentationMode"] == "summary_then_evidence"
    )


def test_stack_plan_uses_summary_then_evidence_profile_when_mode_active():
    metadata = {
        "path": "/products/90262404/factory-status",
        "presentationDecision": {"presentationMode": "summary_then_evidence"},
        "dataAnswer": {
            "summary": {"answer": "Produção em andamento.", "riskLevel": "attention"},
        },
        "textPresentation": {
            "markdown": "### Status fabril\n\n<!-- section:scope -->\n\nEscopo.",
        },
        "tablePresentations": [
            {
                "type": "table",
                "title": "Produção",
                "rows": [{"production_order": "001"}],
            }
        ],
        "chartPresentation": {"type": "chart", "title": "Saldo MP", "series": []},
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan.get("presentationMode") == "summary_then_evidence"
    assert plan["sectionVisibility"]["highlights"] is False
    assert plan["sectionVisibility"]["profile"] is False
    assert "profileTables" not in plan["narrativeOrder"]
    assert "highlights" not in plan["narrativeOrder"]
    assert "operationalTables" in plan["narrativeOrder"]


def test_compose_keeps_natural_chat_narrative_without_story_card():
    metadata = {
        "presentationDecision": {
            "presentationMode": "summary_then_evidence",
            "layoutMode": "stack",
        },
        "dataAnswer": {
            "profileKey": "factory_status",
            "summary": {
                "answer": "Situação fabril consolidada.",
                "riskLevel": "ok",
            },
        },
        "stackPresentationPlan": {
            "presentationMode": "summary_then_evidence",
        },
        "textPresentation": {
            "title": "Status completo na fábrica — 90262404",
            "markdown": (
                "### Status completo na fábrica — 90262404\n\n"
                "Visão integrada na fábrica do produto **90262404**.\n\n"
                "Situação consolidada: **PA PRODUZIDO**\n\n"
                "**Resumo**\n\n"
                "Leitura repetida.\n\n"
                "**Destaques**\n\n"
                "- Produção em andamento."
            ),
        },
    }

    ChatPresentationEvidenceFirstLayoutService.compose(metadata)

    markdown = metadata["textPresentation"]["markdown"]

    assert "storyPresentation" not in metadata
    assert "Visão integrada na fábrica" in markdown
    assert "PA PRODUZIDO" in markdown
    assert "**Resumo**" not in markdown
    assert "**Destaques**" not in markdown
