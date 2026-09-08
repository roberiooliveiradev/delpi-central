"""Fase 9 — facades não caem no registry com mode=on."""

from __future__ import annotations

from app.application.services.external_actions.external_action_selection_dispatch_service import (
    ExternalActionSelectionDispatchService,
)
from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from tests.support.openapi_logistics_fixtures import (
    import_logistics_actions,
    logistics_allowed_action_ids,
)


class _Repo:
    def __init__(self, actions: list[dict]):
        self.actions = actions

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        return [
            action
            for action in self.actions
            if not allowed or str(action.get("actionId")) in allowed
        ][:limit]

    def list_actions(self, provider_key=None):
        return list(self.actions)

    def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
        return []


def test_dispatch_returns_none_when_openapi_mode_on(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "on",
    )
    actions = import_logistics_actions()
    for action in actions:
        action["enabled"] = True
    service = ExternalActionSelectionService(_Repo(actions))
    assert (
        service._dispatch.dispatch(
            "Onde esta a remessa 45871?",
            allowed_action_ids=logistics_allowed_action_ids(actions),
        )
        is None
    )


def test_select_action_fail_closed_does_not_use_dispatch(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "on",
    )
    actions = import_logistics_actions()
    for action in actions:
        action["enabled"] = True

    class BoomDispatch(ExternalActionSelectionDispatchService):
        def dispatch(self, *args, **kwargs):
            raise AssertionError("registry dispatch must not run with mode=on")

    service = ExternalActionSelectionService(_Repo(actions))
    service._dispatch = BoomDispatch(service._route_selection, service._support)
    selected = service.select_action(
        "Onde esta a remessa 45871 e qual a previsao de entrega?",
        allowed_action_ids=logistics_allowed_action_ids(actions),
    )
    assert selected is not None
    assert selected.get("selectionMode") == "openapi_first"
    assert (selected.get("arguments") or {}).get("parameters", {}).get("id") == "45871"


def test_select_action_for_product_uses_openapi(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.config.settings.Settings.CHAT_OPENAPI_PLANNER_MODE",
        "on",
    )
    actions = [
        {
            "actionId": "stock-action",
            "providerKey": "acme",
            "method": "GET",
            "path": "/products/{code}/stock",
            "operationId": "get_product_stock",
            "summary": "estoque do produto",
            "description": "consulta estoque saldo",
            "enabled": True,
            "parametersSchema": [
                {
                    "name": "code",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            ],
            "sensitivity": "read",
        }
    ]
    service = ExternalActionSelectionService(_Repo(actions))
    selected = service.select_action_for_product(
        "estoque",
        product_code="10080022",
        allowed_action_ids=["stock-action"],
    )
    assert selected is not None
    assert selected["arguments"]["actionId"] == "stock-action"
    assert selected["arguments"]["parameters"]["code"] == "10080022"
