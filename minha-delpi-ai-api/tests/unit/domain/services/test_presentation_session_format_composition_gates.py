from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_llm_composition_service import (
    ChatPresentationLlmCompositionService,
)
from app.domain.services.chat_presentation_user_format_preference_service import (
    ChatPresentationUserFormatPreferenceService,
)

configure_domain_infrastructure_ports()


def test_explicit_table_forces_api_only_composition():
    metadata = {
        "path": "/products/90260149/structure",
        "ok": True,
        "explicitSessionFormat": "table",
        "treePresentation": {"type": "tree", "title": "Estrutura", "root": {"id": "1"}},
        "tablePresentation": {
            "type": "table",
            "title": "Itens",
            "rows": [{"code": "1"}],
        },
    }

    cleaned = ChatPresentationLlmCompositionService.apply(
        metadata,
        "Lead.\n\n[[tree]]\n\n[[table]]",
        explicit_format="table",
    )

    assert metadata["presentationDecision"]["proseCompositionAllowed"] is False
    assert metadata["presentationDecision"]["proseCompositionPolicy"] == "api_only"
    assert metadata["presentationDecision"]["allowedMarkerKinds"] == []
    assert "[[" not in cleaned
    assert metadata.get("proseCompositionSource") != "llm"


def test_behavior_instructions_response_format_table_gates_composition():
    metadata = {
        "path": "/products/90260149/stock",
        "ok": True,
        "tablePresentation": {"type": "table", "title": "Estoque", "rows": []},
        "behaviorInstructions": {"responseFormat": "table"},
    }

    policy = ChatPresentationUserFormatPreferenceService.resolve_prose_composition_policy(
        metadata,
    )

    assert policy == "api_only"


def test_automatic_format_allows_llm_markers_stack():
    policy = ChatPresentationUserFormatPreferenceService.resolve_prose_composition_policy(
        {"path": "/products/90260149/structure"},
        explicit_format="automatic",
    )

    assert policy == "llm_markers_stack"


def test_compose_with_explicit_table_strips_markers_keeps_lead():
    metadata = {
        "path": "/products/10080109/stock",
        "ok": True,
        "explicitSessionFormat": "table",
        "tablePresentation": {
            "type": "table",
            "title": "Estoque",
            "rows": [{"code": "10080109", "qty": 10}],
        },
        "treePresentation": {"type": "tree", "title": "Árvore", "root": {"id": "x"}},
    }

    cleaned = ChatPresentationLlmCompositionService.apply(
        metadata,
        "Saldo disponível.\n\n[[table]]\n\n[[tree]]",
        response_mode="normal",
    )

    assert cleaned == "Saldo disponível."
    assert "renderPlan" not in metadata or metadata.get("proseCompositionSource") != "llm"
