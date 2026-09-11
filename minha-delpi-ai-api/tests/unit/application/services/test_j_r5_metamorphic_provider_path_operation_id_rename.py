"""J-R5 — metamorphic rename verdadeiro (provider + path + operationId).

Não mede sinônimo linguístico. Renomeia superfície técnica preservando
summary/description/tags/schema e prova seleção/execução/outcome equivalentes
sem matcher específico para a V2 no core.
"""

from __future__ import annotations

import json
from pathlib import Path
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
from app.infrastructure.external_actions.openapi_action_importer import (
    OpenApiActionImporter,
)
from tests.support.local_openapi_http_server import LocalOpenApiHttpServer
from tests.support.openapi_logistics_fixtures import normalize_imported_action

_FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "openapi"
_MSG = "Onde esta a remessa 45871 e qual a previsao de entrega?"
_OUTCOME = {
    "id": "45871",
    "status": "in_transit",
    "location": "Santos Hub",
    "estimatedDelivery": "2026-09-15",
}


class _Repo:
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
                "responseSchema": action.get("responseSchema"),
            },
        }


class _Audit:
    def log(self, **kwargs):
        return None


def _import_version(filename: str, provider_key: str) -> list[dict]:
    schema = json.loads((_FIXTURES / filename).read_text(encoding="utf-8"))
    raw = OpenApiActionImporter().import_actions(provider_key, schema)
    return [normalize_imported_action(item, provider_key=provider_key) for item in raw]


def _run_chain(actions: list[dict], *, provider_key: str, http_path: str) -> dict:
    with LocalOpenApiHttpServer(routes={http_path: _OUTCOME}) as server:
        repo = _Repo(actions, base_url=server.base_url, provider_key=provider_key)
        allowed = [str(a["actionId"]) for a in actions]
        candidates = RetrieveActionCandidatesService(repo).retrieve(
            _MSG,
            allowed_action_ids=allowed,
            catalog_actions=actions,
        )
        assert candidates, f"no candidates for {provider_key}"
        plan = PlanExternalActionsService().plan(_MSG, candidates)
        assert plan.steps, f"no plan for {provider_key}"
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
            action_id=str(step.action_id),
            arguments=dict(step.arguments),
        )
        top = candidates[0].descriptor
        return {
            "providerKey": provider_key,
            "path": top.path,
            "operationId": top.operation_id,
            "ok": result.get("ok"),
            "data": result.get("data"),
            "hits": list(server.hits),
        }


def test_j_r5_metamorphic_provider_path_operation_id_rename():
    v1_provider = "metamorphic-tracking-a"
    v2_provider = "metamorphic-tracking-z"
    v1 = _import_version("metamorphic_tracking_v1.json", v1_provider)
    v2 = _import_version("metamorphic_tracking_v2.json", v2_provider)

    assert len(v1) == 1 and len(v2) == 1
    assert v1[0]["summary"] == v2[0]["summary"]
    assert v1[0]["description"] == v2[0]["description"]
    assert v1[0]["tags"] == v2[0]["tags"]
    assert v1[0]["path"] != v2[0]["path"]
    assert v1[0]["operationId"] != v2[0]["operationId"]
    assert v1_provider != v2_provider

    r1 = _run_chain(v1, provider_key=v1_provider, http_path="/shipments/45871/tracking")
    r2 = _run_chain(v2, provider_key=v2_provider, http_path="/cargo/45871/position")

    assert r1["ok"] is True and r2["ok"] is True
    assert r1["data"] == r2["data"] == _OUTCOME
    assert r1["operationId"] == "get_shipment_tracking"
    assert r2["operationId"] == "locateCargo"
    assert r1["path"] == "/shipments/{id}/tracking"
    assert r2["path"] == "/cargo/{id}/position"
    assert "/shipments/45871/tracking" in r1["hits"]
    assert "/cargo/45871/position" in r2["hits"]


def test_j_r5_negative_not_mere_linguistic_synonym():
    """Garante que V1/V2 diferem tecnicamente (não é só paráfrase de frase)."""
    v1 = _import_version("metamorphic_tracking_v1.json", "metamorphic-tracking-a")
    v2 = _import_version("metamorphic_tracking_v2.json", "metamorphic-tracking-z")
    technical_delta = {
        "provider": v1[0]["providerKey"] != v2[0]["providerKey"],
        "path": v1[0]["path"] != v2[0]["path"],
        "operationId": v1[0]["operationId"] != v2[0]["operationId"],
    }
    assert all(technical_delta.values()), technical_delta
