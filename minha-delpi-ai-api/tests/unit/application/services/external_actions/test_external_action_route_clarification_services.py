from app.application.services.external_actions.external_action_score_gap_clarification_service import (
    ExternalActionScoreGapClarificationService,
)
from app.application.services.external_actions.external_action_catalog_miss_clarification_service import (
    ExternalActionCatalogMissClarificationService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_score_gap_clarifies_when_top_two_close():
    ranked = [
        {
            "actionId": "a1",
            "operationId": "get_production_otd",
            "summary": "OTD detalhe",
            "path": "/production/otd",
            "selectionScore": 0.51,
        },
        {
            "actionId": "a2",
            "operationId": "get_production_oee",
            "summary": "OEE detalhe",
            "path": "/production/oee",
            "selectionScore": 0.49,
        },
    ]

    clarification = ExternalActionScoreGapClarificationService.maybe_build(ranked)

    assert clarification is not None
    assert ExternalActionScoreGapClarificationService.is_clarification_tool_call(
        clarification
    )
    assert "OTD" in clarification["arguments"]["directAnswer"]
    assert clarification["arguments"]["scoreGap"] <= 0.05


def test_score_gap_skips_when_gap_large():
    ranked = [
        {
            "actionId": "a1",
            "operationId": "get_a",
            "summary": "A",
            "selectionScore": 0.9,
        },
        {
            "actionId": "a2",
            "operationId": "get_b",
            "summary": "B",
            "selectionScore": 0.4,
        },
    ]

    assert ExternalActionScoreGapClarificationService.maybe_build(ranked) is None


def test_catalog_miss_clarifies_when_requires_tool(monkeypatch):
    class _Route:
        requires_tool = True
        intent = "operational_query"

    monkeypatch.setattr(
        "app.application.services.external_actions.external_action_catalog_miss_clarification_service.ChatIntentRouterService.classify",
        lambda *args, **kwargs: _Route(),
    )

    answer = ExternalActionCatalogMissClarificationService.resolve_direct_answer(
        "indicador inventado xyz",
        allowed_action_ids=["api-delpi.x.y"],
    )

    assert answer
    assert "catálogo" in answer.lower() or "rota" in answer.lower()


def test_catalog_miss_skips_when_not_requires_tool(monkeypatch):
    class _Route:
        requires_tool = False
        intent = "llm_general"

    monkeypatch.setattr(
        "app.application.services.external_actions.external_action_catalog_miss_clarification_service.ChatIntentRouterService.classify",
        lambda *args, **kwargs: _Route(),
    )

    assert (
        ExternalActionCatalogMissClarificationService.resolve_direct_answer(
            "quem e voce",
            allowed_action_ids=["api-delpi.x.y"],
        )
        is None
    )
