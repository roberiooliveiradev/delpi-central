"""E11.S6 — semantic ownership: KPI/production sem pathMarkers/pathTokens authority."""

from __future__ import annotations

from app.application.services.external_actions.operational_route_selection.operational_route_domain_selection_service import (
    OperationalRouteDomainSelectionService,
)
from app.domain.models.operational_api_route_spec import OperationalApiRouteSpec
from app.domain.services.chat_department_kpi_intent_service import DepartmentKpiMatch
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
    ProductionOperationalIntentKind,
)
from app.domain.services.turn_understanding_product_intent_mapper_service import (
    TurnUnderstandingProductIntentMapperService,
)


def test_virtual_kpi_route_has_no_lateral_path_markers():
    match = DepartmentKpiMatch(
        path_token="closing-rate",
        domain_prefix="/commercial/",
        reason="taxa",
        operation_hint="closing",
    )
    spec = OperationalApiRouteSpec.from_department_kpi(match)
    route = OperationalRouteDomainSelectionService._virtual_department_kpi_route(spec)
    route_spec = route.get("route") or {}
    assert not (route_spec.get("pathMarkers") or [])
    assert not (route_spec.get("operationIdMarkers") or [])
    assert route.get("domain") == "department_kpi"
    assert route.get("intentBinding")
    assert route.get("continuityFacets")


def test_production_path_token_for_is_empty():
    for kind in ProductionOperationalIntentKind:
        assert ChatProductionOperationalIntentService.path_token_for(kind) == ""


def test_product_mapper_keeps_facet_vocabulary_not_http_path():
    intent = TurnUnderstandingProductIntentMapperService.from_goal_prose(
        "estoque do produto"
    )
    assert intent == "stock"
    assert "/" not in intent


def test_production_bundle_has_no_path_tokens_key():
    from pathlib import Path
    import json

    payload = json.loads(
        (
            Path(__file__).resolve().parents[4]
            / "app/content/pt-BR/assistant/production_operational_intent.json"
        ).read_text(encoding="utf-8")
    )
    assert "pathTokens" not in payload
    assert payload.get("cleanupMeta", {}).get("pathTokensDeletedAt") == "E11.S6"
