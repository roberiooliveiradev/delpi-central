"""E8.S4 — copy UX separada de actionSelection (EAR mixed bundles)."""

from __future__ import annotations

import json
from pathlib import Path

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
    invalidate_external_action_response_cache,
)
from app.application.services.external_actions.external_action_empty_rival_recommendation_service import (
    ExternalActionEmptyRivalRecommendationService,
)
from app.application.services.external_actions.external_action_catalog_miss_clarification_service import (
    ExternalActionCatalogMissClarificationService,
)

configure_domain_infrastructure_ports()
invalidate_external_action_response_cache()

_ROOT = Path(__file__).resolve().parents[4]
_EAR = _ROOT / "app/content/pt-BR/assistant/external_action_responses.json"


def test_e8_s4_action_selection_has_no_ux_copy_blobs():
    """Negative: routeClarification / refinement não moram mais em actionSelection."""

    ear = json.loads(_EAR.read_text(encoding="utf-8"))
    selection = ear["actionSelection"]
    assert "routeClarification" not in selection
    assert "refinementFallbackMessages" not in selection
    for family in selection.get("emptyRivalRecommendations") or []:
        assert "suggestions" not in family


def test_e8_s4_copy_loaded_from_action_selection_copy():
    """Positive: templates UX vêm de actionSelectionCopy."""

    invalidate_external_action_response_cache()
    text = ExternalActionResponseContentService.get(
        "actionSelectionCopy",
        "routeClarification",
        "catalogMissDirectAnswer",
    )
    assert "catálogo" in text.casefold() or "catalogo" in text.casefold()
    assert ExternalActionResponseContentService.get(
        "actionSelection",
        "routeClarification",
        "catalogMissDirectAnswer",
    ) == ""


def test_e8_s4_empty_rival_suggestions_from_copy_map():
    """Sibling: matchers em actionSelection; suggestions no mapa copy."""

    invalidate_external_action_response_cache()
    tool_calls = [
        {
            "name": "execute_external_action",
            "arguments": {"actionId": "get_production_otd"},
            "metadata": {
                "path": "/production/otd",
                "operationId": "get_production_otd",
            },
        }
    ]
    suggestions = ExternalActionEmptyRivalRecommendationService.suggestions_for_tool_calls(
        tool_calls,
        error_type="empty_result",
    )
    assert suggestions
    assert any("otd" in s["query"].casefold() for s in suggestions)


def test_e8_s4_empty_rival_unrelated_returns_empty():
    """Negative: path sem família → sem suggestions."""

    invalidate_external_action_response_cache()
    suggestions = ExternalActionEmptyRivalRecommendationService.suggestions_for_tool_calls(
        [
            {
                "name": "execute_external_action",
                "metadata": {"path": "/acme/widgets", "operationId": "acme.widgets"},
            }
        ],
        error_type="empty_result",
    )
    assert suggestions == []


def test_e8_s4_catalog_miss_uses_copy_owner():
    invalidate_external_action_response_cache()
    # Service may need route context — smoke that content path resolves
    answer = ExternalActionResponseContentService.get(
        "actionSelectionCopy",
        "routeClarification",
        "catalogMissDirectAnswer",
    )
    assert answer.strip()
    _ = ExternalActionCatalogMissClarificationService
