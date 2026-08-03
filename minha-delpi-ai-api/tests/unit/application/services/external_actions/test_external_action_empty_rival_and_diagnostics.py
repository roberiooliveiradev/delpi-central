from app.application.services.external_actions.external_action_empty_rival_recommendation_service import (
    ExternalActionEmptyRivalRecommendationService,
)
from app.application.services.external_actions.external_action_selection_diagnostics_service import (
    ExternalActionSelectionDiagnosticsService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_empty_rival_recommendations_for_otd():
    suggestions = ExternalActionEmptyRivalRecommendationService.suggestions_for_tool_calls(
        [
            {
                "name": "execute_external_action",
                "metadata": {
                    "operationId": "get_production_otd",
                    "path": "/production/otd",
                },
            }
        ],
        error_type="empty_result",
    )

    assert suggestions
    assert any("período" in item["label"].lower() or "status" in item["label"].lower() or "ops" in item["label"].lower() for item in suggestions)
    assert ExternalActionEmptyRivalRecommendationService.should_skip_auto_retry(
        [{"metadata": {"path": "/production/otd"}}],
        error_type="empty_result",
    )


def test_selection_diagnostics_annotate_score_gap():
    tool_call = {
        "name": "execute_external_action",
        "arguments": {"actionId": "a1"},
        "reason": "x",
    }
    ranked = [
        {"actionId": "a1", "operationId": "op1", "selectionScore": 0.8},
        {"actionId": "a2", "operationId": "op2", "selectionScore": 0.7},
    ]
    annotated = ExternalActionSelectionDiagnosticsService.annotate(
        tool_call,
        match_source="semanticFallback",
        ranked=ranked,
        reason_key="genericSemanticFallback",
    )

    assert annotated["selectionDiagnostics"]["matchSource"] == "semanticFallback"
    assert annotated["selectionDiagnostics"]["rivalIds"] == ["a1", "a2"]
    assert annotated["selectionDiagnostics"]["scoreGap"] == 0.1
    assert annotated["arguments"]["selectionDiagnostics"]["reasonKey"] == (
        "genericSemanticFallback"
    )
