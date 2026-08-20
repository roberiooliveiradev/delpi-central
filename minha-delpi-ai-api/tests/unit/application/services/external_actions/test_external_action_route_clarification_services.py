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
            "selectionLexicalMatched": True,
        },
        {
            "actionId": "a2",
            "operationId": "get_production_oee",
            "summary": "OEE detalhe",
            "path": "/production/oee",
            "selectionScore": 0.49,
            "selectionLexicalMatched": True,
        },
    ]

    clarification = ExternalActionScoreGapClarificationService.maybe_build(ranked)

    assert clarification is not None
    assert ExternalActionScoreGapClarificationService.is_clarification_tool_call(
        clarification
    )
    assert "OTD" in clarification["arguments"]["directAnswer"]
    assert clarification["arguments"]["scoreGap"] <= 0.05


def test_score_gap_skips_semantic_tie_without_lexical_like_kimi_ok():
    """Empate semântico sem overlap lexical real → não abrir «rotas próximas»."""
    ranked = [
        {
            "actionId": "a1",
            "operationId": "get_production_orders_finished_without_consumption",
            "summary": "OPs finalizadas sem consumo de componentes",
            "selectionScore": 0.47,
        },
        {
            "actionId": "a2",
            "operationId": "get_refugos_health",
            "summary": "Indicador — Refugos health",
            "selectionScore": 0.44,
        },
    ]

    assert ExternalActionScoreGapClarificationService.maybe_build(ranked) is None


def test_lexical_ok_token_does_not_match_playbook_shape():
    """Regressão: «ok» de KIMI_OK não pode casar substring em playbook_report."""
    from app.application.services.external_actions.external_action_selection_support_service import (
        ExternalActionSelectionSupportService,
    )

    action = {
        "method": "GET",
        "path": "/production/orders/finished-without-consumption",
        "summary": "OPs finalizadas sem consumo de componentes",
        "operationId": "get_production_orders_finished_without_consumption",
        "delpiMetadata": {"entity": "production_orders", "shape": "playbook_report"},
        "parametersSchema": [
            {
                "name": "branch",
                "description": "Branch scope: all (no branch filter)",
                "schema": {"enum": ["all", "01", "02"]},
            }
        ],
    }

    score = ExternalActionSelectionSupportService.lexical_overlap_score(
        "Responda apenas: KIMI_OK",
        action,
    )
    assert score == 0.0


def test_lexical_overlap_matches_otd_whole_token():
    from app.application.services.external_actions.external_action_selection_support_service import (
        ExternalActionSelectionSupportService,
    )

    action = {
        "method": "GET",
        "path": "/production/otd",
        "summary": "OTD produção",
        "operationId": "get_production_otd",
        "delpiMetadata": {"shape": "playbook_report"},
    }

    score = ExternalActionSelectionSupportService.lexical_overlap_score(
        "mostrar otd de produção",
        action,
    )
    assert score > 0



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


def test_score_gap_skips_zero_scores_like_kimi_ok_smoke():
    """Mensagem sem overlap lexical → scores 0; não abrir «rotas próximas»."""
    ranked = [
        {
            "actionId": "console-alerts",
            "operationId": "get_console_alerts",
            "summary": "Avaliar alertas do console",
            "selectionScore": 0.0,
        },
        {
            "actionId": "nc-list",
            "operationId": "list_non_conformities",
            "summary": "Não conformidades — listagem",
            "selectionScore": 0.0,
        },
    ]

    assert ExternalActionScoreGapClarificationService.maybe_build(ranked) is None


def test_score_gap_skips_weak_semantic_tie():
    ranked = [
        {
            "actionId": "a1",
            "operationId": "get_a",
            "summary": "A",
            "selectionScore": 0.22,
        },
        {
            "actionId": "a2",
            "operationId": "get_b",
            "summary": "B",
            "selectionScore": 0.21,
        },
    ]

    assert ExternalActionScoreGapClarificationService.maybe_build(ranked) is None


def test_lexical_ranking_drops_zero_overlap():
    from app.application.services.external_actions.external_action_selection_support_service import (
        ExternalActionSelectionSupportService,
    )

    ranked = ExternalActionSelectionSupportService.ensure_lexical_ranking(
        "Responda apenas: KIMI_OK",
        [
            {
                "actionId": "console-alerts",
                "operationId": "get_console_alerts",
                "summary": "Avaliar alertas do console",
                "path": "/console/alerts",
                "method": "GET",
            },
            {
                "actionId": "nc-list",
                "operationId": "list_non_conformities",
                "summary": "Não conformidades — listagem",
                "path": "/quality/non-conformities",
                "method": "GET",
            },
        ],
    )

    assert ranked == []


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
