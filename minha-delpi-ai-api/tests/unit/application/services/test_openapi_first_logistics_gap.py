"""E1.S1 — document the OpenAPI-first gap for a third-party logistics API.

Without the universal planner, registry-first selection cannot bind path params
for an API that never existed in operational_route_registry.json.
"""

from __future__ import annotations

import pytest

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from tests.support.openapi_logistics_fixtures import (
    find_logistics_action,
    import_logistics_actions,
    logistics_allowed_action_ids,
    load_logistics_openapi,
)


class _LogisticsRepository:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        rows = [
            action
            for action in self.actions
            if not allowed or str(action.get("actionId")) in allowed
        ]
        return rows[:limit]

    def list_actions(self, provider_key=None):
        return list(self.actions)

    def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
        return []


def test_logistics_fixture_is_valid_openapi_without_delpi_vocabulary():
    schema = load_logistics_openapi()
    assert schema["openapi"].startswith("3.")
    assert "shipments" in str(schema["paths"]).lower()
    blob = str(schema).lower()
    assert "products/{code}" not in blob
    assert "api-delpi" not in blob
    assert "filial" not in blob


def test_logistics_import_produces_tracking_and_cancel_actions():
    actions = import_logistics_actions(resolve_refs=False)
    operation_ids = {str(item.get("operationId")) for item in actions}
    assert "get_shipment_tracking" in operation_ids
    assert "cancel_shipment" in operation_ids
    assert "get_warehouse_stock" in operation_ids
    tracking = find_logistics_action("get_shipment_tracking", actions)
    assert tracking["method"] == "GET"
    assert "/shipments/{id}/tracking" in str(tracking["path"])


def test_select_action_facade_uses_openapi_first_and_binds_shipment_id(monkeypatch):
    """Fase 9: facade select_action com mode=on não depende do registry."""
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "on",
    )
    actions = import_logistics_actions()
    for action in actions:
        action["enabled"] = True

    service = ExternalActionSelectionService(_LogisticsRepository(actions))
    selected = service.select_action(
        "Onde esta a remessa 45871 e qual a previsao de entrega?",
        allowed_action_ids=logistics_allowed_action_ids(actions),
    )

    assert selected is not None
    assert selected.get("selectionMode") == "openapi_first"
    assert selected["arguments"]["actionId"]
    assert (selected["arguments"].get("parameters") or {}).get("id") == "45871"


def test_openapi_first_acceptance_tracking_with_path_param(monkeypatch):
    """Aceite: planner OpenAPI-first liga tracking + id sem registry."""
    from app.application.services.openapi_first_selection_bridge_service import (
        OpenApiFirstSelectionBridgeService,
    )
    from app.application.services.plan_external_actions_service import (
        PlanExternalActionsService,
    )
    from app.domain.services.openapi_planner_mode_service import OpenApiPlannerModeDecision

    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "on",
    )
    actions = import_logistics_actions()
    repo = _LogisticsRepository(actions)
    bridge = OpenApiFirstSelectionBridgeService(repo, planner=PlanExternalActionsService(llm_planner=None))
    selected_list = bridge.plan_tool_calls(
        "Onde esta a remessa 45871 e qual a previsao de entrega?",
        allowed_action_ids=logistics_allowed_action_ids(actions),
        catalog_actions=actions,
        mode_decision=OpenApiPlannerModeDecision(
            mode="on",
            use_openapi_selection=True,
            run_shadow_compare=False,
            canary_matched=False,
        ),
    )
    assert selected_list
    selected = selected_list[0]
    assert selected is not None
    assert selected["arguments"]["actionId"]
    operation = next(
        item
        for item in actions
        if item["actionId"] == selected["arguments"]["actionId"]
    )
    assert operation["operationId"] == "get_shipment_tracking"
    assert (selected["arguments"].get("parameters") or {}).get("id") == "45871"
