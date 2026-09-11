"""J-R4 — unknown external OpenAPI full chain (HTTP local controlado).

Cobre: import → catalog → retrieve → plan → validate/policy → executor HTTP
→ payload → presentation → outcome. Sem edição de core/registry por endpoint.
"""

from __future__ import annotations

from typing import Any

from app.application.services.plan_external_actions_service import PlanExternalActionsService
from app.application.services.retrieve_action_candidates_service import (
    RetrieveActionCandidatesService,
)
from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)
from app.infrastructure.external_actions.http_external_action_gateway import (
    HttpExternalActionGateway,
)
from tests.support.local_openapi_http_server import (
    LocalOpenApiHttpServer,
    make_never_seen_provider_key,
)
from tests.support.openapi_logistics_fixtures import (
    find_logistics_action,
    import_logistics_actions,
    logistics_allowed_action_ids,
)


class _CatalogRepo:
    def __init__(self, actions: list[dict], *, base_url: str, provider_key: str):
        self.actions = actions
        self.base_url = base_url
        self.provider_key = provider_key

    def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
        allowed = {str(item) for item in (allowed_action_ids or [])}
        rows = [
            a
            for a in self.actions
            if not allowed or str(a.get("actionId")) in allowed
        ]
        return rows[:limit]

    def list_actions(self, provider_key=None):
        return list(self.actions)

    def search_similar_actions(self, embedding, *, allowed_action_ids=None, limit=20):
        return []

    def get_action_for_execution(self, action_id: str) -> dict[str, Any] | None:
        action = next((a for a in self.actions if str(a.get("actionId")) == str(action_id)), None)
        if not action:
            return None
        return {
            "provider": {
                "enabled": True,
                "providerKey": self.provider_key,
                "baseUrl": self.base_url,
                "authMode": "none",
                "timeoutSeconds": 10,
            },
            "action": {
                "enabled": True,
                "method": action.get("method"),
                "path": action.get("path"),
                "actionId": action.get("actionId"),
                "operationId": action.get("operationId"),
                "sensitivity": action.get("sensitivity") or "read",
                "parametersSchema": action.get("parametersSchema") or [],
                "requestBodySchema": action.get("requestBodySchema"),
                "responseSchema": action.get("responseSchema"),
            },
        }


class _Audit:
    def log(self, **kwargs):
        return None


TRACKING_PAYLOAD = {
    "shipmentId": "45871",
    "status": "in_transit",
    "location": "Santos Hub",
    "estimatedDelivery": "2026-09-15",
}


def _import_never_seen_actions(provider_key: str) -> list[dict]:
    actions = import_logistics_actions(provider_key=provider_key)
    for row in actions:
        row["providerKey"] = provider_key
        row["providerName"] = "Acme Harbor JR4 Never Seen API"
    return actions


def test_j_r4_unknown_external_full_chain_positive():
    provider_key = make_never_seen_provider_key()
    actions = _import_never_seen_actions(provider_key)
    tracking = find_logistics_action("get_shipment_tracking", actions)
    assert "pathMarkers" not in tracking
    assert provider_key not in {"api_delpi", "logistics-example"} or provider_key == make_never_seen_provider_key()

    with LocalOpenApiHttpServer(
        routes={"/shipments/45871/tracking": TRACKING_PAYLOAD}
    ) as server:
        repo = _CatalogRepo(actions, base_url=server.base_url, provider_key=provider_key)
        msg = "Onde esta a remessa 45871 e qual a previsao de entrega?"
        candidates = RetrieveActionCandidatesService(repo).retrieve(
            msg,
            allowed_action_ids=logistics_allowed_action_ids(actions),
            catalog_actions=actions,
        )
        assert candidates
        assert candidates[0].descriptor.operation_id == "get_shipment_tracking"

        plan = PlanExternalActionsService().plan(msg, candidates)
        assert plan.steps
        step = plan.steps[0]
        assert step.arguments["parameters"]["id"] == "45871"

        use_case = ExecuteExternalActionUseCase(
            repository=repo,
            gateway=HttpExternalActionGateway(),
            policy=ExternalActionExecutionPolicy(),
            audit_repository=_Audit(),
        )
        result = use_case.execute(
            user_id="00000000-0000-0000-0000-000000000001",
            access_token="",
            action_id=str(step.action_id or tracking["actionId"]),
            arguments=dict(step.arguments),
        )

        assert result["ok"] is True
        assert result.get("statusCode") == 200
        data = result.get("data") or {}
        assert data.get("shipmentId") == "45871"
        assert data.get("status") == "in_transit"
        assert data.get("estimatedDelivery") == "2026-09-15"
        assert "/shipments/45871/tracking" in server.hits

        metadata = result.get("metadata") or {}
        # Presentation schema-driven (não presenter tipado por endpoint no core).
        assert (
            metadata.get("presentationDecision")
            or metadata.get("tablePresentation")
            or metadata.get("textPresentation")
            or metadata.get("kpiPresentation")
            or metadata.get("presentation")
        )


def test_j_r4_sibling_warehouse_stock_full_chain():
    provider_key = make_never_seen_provider_key()
    actions = _import_never_seen_actions(provider_key)
    stock = find_logistics_action("get_warehouse_stock", actions)
    payload = {"warehouseId": "W1", "items": [{"sku": "10080022", "qty": 12}]}

    with LocalOpenApiHttpServer(routes={"/warehouses/W1/stock": payload}) as server:
        repo = _CatalogRepo(actions, base_url=server.base_url, provider_key=provider_key)
        use_case = ExecuteExternalActionUseCase(
            repository=repo,
            gateway=HttpExternalActionGateway(),
            policy=ExternalActionExecutionPolicy(),
            audit_repository=_Audit(),
        )
        result = use_case.execute(
            user_id="00000000-0000-0000-0000-000000000001",
            access_token="",
            action_id=str(stock["actionId"]),
            arguments={"parameters": {"id": "W1"}},
        )
        assert result["ok"] is True
        assert (result.get("data") or {}).get("warehouseId") == "W1"
        assert "/warehouses/W1/stock" in server.hits


def test_j_r4_negative_unknown_action_never_executed():
    provider_key = make_never_seen_provider_key()
    actions = _import_never_seen_actions(provider_key)
    with LocalOpenApiHttpServer(routes={"/shipments/1/tracking": TRACKING_PAYLOAD}) as server:
        repo = _CatalogRepo(actions, base_url=server.base_url, provider_key=provider_key)
        use_case = ExecuteExternalActionUseCase(
            repository=repo,
            gateway=HttpExternalActionGateway(),
            policy=ExternalActionExecutionPolicy(),
            audit_repository=_Audit(),
        )
        try:
            use_case.execute(
                user_id="00000000-0000-0000-0000-000000000001",
                access_token="",
                action_id="totally.unknown.action",
                arguments={"parameters": {"id": "1"}},
            )
            raised = False
        except ValueError as exc:
            raised = True
            assert "not found" in str(exc).lower()
        assert raised
        assert server.hits == []
