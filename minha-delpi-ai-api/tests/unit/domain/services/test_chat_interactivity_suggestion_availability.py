from app.domain.services.chat_interactivity_content_service import (
    ChatInteractivityContentService,
)
from app.domain.services.chat_interactivity_suggestion_availability_service import (
    ChatInteractivitySuggestionAvailabilityService,
)


def test_hide_unavailable_suggestions_defaults_true():
    assert ChatInteractivityContentService.hide_unavailable_suggestions() is True


def test_operational_label_disabled_without_agent():
    reason = ChatInteractivitySuggestionAvailabilityService.resolve_disabled_reason(
        "Consultar produto",
        workspace_context={"userActivatedAgent": False, "actionsEnabled": False},
    )

    assert reason
    assert "agente" in reason.lower()


def test_sql_label_disabled_without_actions():
    reason = ChatInteractivitySuggestionAvailabilityService.resolve_disabled_reason(
        "Gerar gráfico",
        workspace_context={"userActivatedAgent": True, "actionsEnabled": False},
    )

    assert reason
    assert "sql" in reason.lower() or "schema" in reason.lower()


def test_omit_unavailable_removes_disabled_items():
    items = [
        {"label": "Ver estoque", "query": "estoque", "disabledReason": "indisponível"},
        {"label": "Pesquisar na web", "query": "pesquise na web"},
    ]

    visible = ChatInteractivitySuggestionAvailabilityService.omit_unavailable(
        items,
        workspace_context={"userActivatedAgent": False},
    )

    labels = [item["label"] for item in visible]

    assert "Ver estoque" not in labels
    assert "Pesquisar na web" in labels
