"""Cadastros — Etapa 2: superfície administrativa humana do catálogo."""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from delpi_mes_app.application.services.mes_downtime_reason_admin_service import (
    MesDowntimeReasonAdminService,
)
from delpi_mes_app.domain.errors import (
    HumanPrincipalRequired,
    MesSourceConflict,
    MesSourceNotFound,
    MesSourceValidationError,
)
from delpi_mes_app.interface.http.routes import mes_routes
from delpi_mes_app.main import app as production_app


def user(*permissions, superadmin=False, principal_type="user"):
    return SimpleNamespace(
        permissions=list(permissions), is_superadmin=superadmin,
        principal_type=principal_type, rbac_unavailable=False,
    )


FULL = ("delpi-mes.access", "delpi-mes.downtime-reasons.manage")


def reason(code, **overrides):
    data = {
        "code": code, "label": f"Motivo {code}", "category": "other",
        "requiresNote": False, "active": True, "sortOrder": 10,
        "createdAt": "2026-01-01T00:00:00+00:00",
        "updatedAt": "2026-01-02T00:00:00+00:00",
    }
    data.update(overrides)
    return data


class FakeGateway:
    def __init__(self):
        self.items = [
            reason("raw_material"),
            reason("obsolete", active=False, sortOrder=999),
        ]
        self.calls = []

    def list_downtime_reasons(self):
        return {"items": list(self.items)}

    def create_downtime_reason(self, payload):
        self.calls.append(("create", payload))
        return reason(payload["code"], requiresNote=payload["requiresNote"])

    def update_downtime_reason(self, code, payload):
        self.calls.append(("update", code, payload))
        return reason(code, **{k: v for k, v in payload.items() if k != "code"})

    def set_downtime_reason_active(self, code, *, active):
        self.calls.append(("active", code, active))
        return reason(code, active=active)


# ---------------------------------------------------------------------------
# Service: autorização global + allowlist DTO
# ---------------------------------------------------------------------------

class TestAdminServiceAuth:
    @pytest.mark.parametrize("principal", [
        user(superadmin=True, principal_type="service"),
        user(*FULL, principal_type="service"),
        None,
    ])
    def test_service_principal_and_anonymous_rejected(self, principal):
        with pytest.raises(HumanPrincipalRequired):
            MesDowntimeReasonAdminService(FakeGateway()).list_reasons(principal)

    @pytest.mark.parametrize("principal", [
        user(),
        user("delpi-mes.access"),
        user("delpi-mes.downtime-reasons.manage"),
        user("delpi-mes.access", "delpi-mes.downtimes.view"),
    ])
    def test_missing_access_or_manage_rejected(self, principal):
        service = MesDowntimeReasonAdminService(FakeGateway())
        with pytest.raises(PermissionError):
            service.list_reasons(principal)
        with pytest.raises(PermissionError):
            service.set_reason_active(principal, "raw_material", active=False)

    def test_authorized_and_superadmin_allowed(self):
        service = MesDowntimeReasonAdminService(FakeGateway())
        assert service.list_reasons(user(*FULL))["items"]
        assert service.list_reasons(user(superadmin=True))["items"]


class TestAdminServiceDto:
    def test_list_preserves_order_and_allowlist(self):
        gateway = FakeGateway()
        gateway.items[0]["defaultPlanned"] = True
        gateway.items[0]["defaultCountsAsAvailabilityLoss"] = False
        gateway.items[0]["internal"] = "drop"
        data = MesDowntimeReasonAdminService(gateway).list_reasons(user(*FULL))
        assert [i["code"] for i in data["items"]] == ["raw_material", "obsolete"]
        assert data["items"][1]["active"] is False
        item = data["items"][0]
        assert set(item) == {
            "code", "label", "category", "requiresNote",
            "active", "sortOrder", "createdAt", "updatedAt",
        }

    def test_list_empty(self):
        gateway = FakeGateway()
        gateway.items = []
        assert MesDowntimeReasonAdminService(gateway).list_reasons(
            user(*FULL)
        ) == {"items": []}

    def test_create_forwards_camelcase_payload(self):
        gateway = FakeGateway()
        service = MesDowntimeReasonAdminService(gateway)
        item = service.create_reason(
            user(*FULL), code="operator_training", label="Treinamento",
            category="people", requires_note=False, sort_order=120,
        )
        assert gateway.calls == [(
            "create",
            {"code": "operator_training", "label": "Treinamento",
             "category": "people", "requiresNote": False, "sortOrder": 120},
        )]
        assert item["code"] == "operator_training"

    def test_update_sends_code_in_path_not_body(self):
        gateway = FakeGateway()
        MesDowntimeReasonAdminService(gateway).update_reason(
            user(*FULL), "raw_material", label="Novo", category="material",
            requires_note=True, sort_order=41,
        )
        _, code, payload = gateway.calls[0]
        assert code == "raw_material"
        assert "code" not in payload and "active" not in payload
        assert payload == {"label": "Novo", "category": "material",
                           "requiresNote": True, "sortOrder": 41}

    def test_set_active_forwards_flag(self):
        gateway = FakeGateway()
        service = MesDowntimeReasonAdminService(gateway)
        assert service.set_reason_active(user(*FULL), "x", active=False)["active"] is False
        assert gateway.calls[-1] == ("active", "x", False)
        assert service.set_reason_active(user(*FULL), "x", active=True)["active"] is True

    @pytest.mark.parametrize("error", [
        MesSourceNotFound("não encontrado"),
        MesSourceConflict("protegido"),
        MesSourceValidationError("inválido"),
    ])
    def test_upstream_errors_propagate(self, error):
        gateway = FakeGateway()
        gateway.update_downtime_reason = lambda *a, **kw: (_ for _ in ()).throw(error)
        with pytest.raises(type(error)):
            MesDowntimeReasonAdminService(gateway).update_reason(
                user(*FULL), "x", label="l", category="c",
                requires_note=False, sort_order=0,
            )


# ---------------------------------------------------------------------------
# HTTP: RBAC nas rotas humanas
# ---------------------------------------------------------------------------

def route_client(monkeypatch, principal, gateway=None):
    app = FastAPI()

    @app.middleware("http")
    async def inject(request, call_next):
        request.state.user = principal
        return await call_next(request)

    app.include_router(mes_routes.router)
    service = MesDowntimeReasonAdminService(gateway or FakeGateway())
    monkeypatch.setattr(
        mes_routes, "build_mes_downtime_reason_admin_service", lambda: service
    )
    return TestClient(app)


def test_admin_routes_require_jwt_in_production_app():
    client = TestClient(production_app)
    assert client.get("/registrations/downtime-reasons").status_code == 401
    assert client.get(
        "/registrations/downtime-reasons",
        headers={"Authorization": "Bearer invalid"},
    ).status_code == 401


@pytest.mark.parametrize("principal", [
    user(superadmin=True, principal_type="service"),
    user(),
    user("delpi-mes.access"),
    user("delpi-mes.access", "delpi-mes.downtimes.view", "delpi-mes.view.filial-01"),
])
def test_admin_routes_forbidden_without_manage(monkeypatch, principal):
    api = route_client(monkeypatch, principal)
    create_body = {"code": "x", "label": "l", "category": "c", "requiresNote": False}
    update_body = {"label": "l", "category": "c", "requiresNote": False}
    for response in [
        api.get("/registrations/downtime-reasons"),
        api.post("/registrations/downtime-reasons", json=create_body),
        api.put("/registrations/downtime-reasons/x", json=update_body),
        api.patch("/registrations/downtime-reasons/x/active", json={"active": True}),
    ]:
        assert response.status_code == 403


class TestAdminHttpFlow:
    def test_crud_flow_and_error_mapping(self, monkeypatch):
        gateway = FakeGateway()
        api = route_client(monkeypatch, user(*FULL), gateway)

        listing = api.get("/registrations/downtime-reasons")
        assert listing.status_code == 200
        codes = [i["code"] for i in listing.json()["data"]["items"]]
        assert codes == ["raw_material", "obsolete"]
        assert "defaultPlanned" not in listing.text

        created = api.post(
            "/registrations/downtime-reasons",
            json={"code": "operator_training", "label": "Treinamento",
                  "category": "people", "requiresNote": False, "sortOrder": 120},
        )
        assert created.status_code == 201
        assert created.json()["data"]["code"] == "operator_training"

        updated = api.put(
            "/registrations/downtime-reasons/operator_training",
            json={"label": "Novo", "category": "people",
                  "requiresNote": True, "sortOrder": 121},
        )
        assert updated.status_code == 200
        assert updated.json()["data"]["requiresNote"] is True

        assert api.patch(
            "/registrations/downtime-reasons/operator_training/active",
            json={"active": False},
        ).json()["data"]["active"] is False
        assert api.patch(
            "/registrations/downtime-reasons/operator_training/active",
            json={"active": True},
        ).json()["data"]["active"] is True

    def test_upstream_status_preserved(self, monkeypatch):
        gateway = FakeGateway()
        gateway.create_downtime_reason = (
            lambda payload: (_ for _ in ()).throw(MesSourceConflict("Já existe."))
        )
        gateway.update_downtime_reason = (
            lambda code, payload: (_ for _ in ()).throw(
                MesSourceNotFound("Motivo não existe.")
            )
        )
        gateway.set_downtime_reason_active = (
            lambda code, *, active: (_ for _ in ()).throw(
                MesSourceConflict("O motivo 'setup' é protegido.")
            )
        )
        api = route_client(monkeypatch, user(*FULL), gateway)

        duplicate = api.post(
            "/registrations/downtime-reasons",
            json={"code": "x", "label": "l", "category": "c", "requiresNote": False},
        )
        assert duplicate.status_code == 409
        assert "Já existe" in duplicate.json()["message"]

        missing = api.put(
            "/registrations/downtime-reasons/ghost",
            json={"label": "l", "category": "c", "requiresNote": False},
        )
        assert missing.status_code == 404

        setup_guard = api.patch(
            "/registrations/downtime-reasons/setup/active", json={"active": False}
        )
        assert setup_guard.status_code == 409
        assert "protegido" in setup_guard.json()["message"]

    @pytest.mark.parametrize("body", [
        {"code": "x", "label": "l", "category": "c", "requiresNote": False,
         "defaultPlanned": True},
        {"code": "x", "label": "l", "category": "c"},
        {"label": "l", "category": "c", "requiresNote": False},
    ])
    def test_post_rejects_extra_or_missing_fields(self, monkeypatch, body):
        api = route_client(monkeypatch, user(*FULL))
        assert api.post("/registrations/downtime-reasons", json=body).status_code == 422

    @pytest.mark.parametrize("body", [
        {"label": "l", "category": "c", "requiresNote": False, "code": "renamed"},
        {"label": "l", "category": "c", "requiresNote": False, "active": True},
        {"label": "l", "requiresNote": False},
    ])
    def test_put_rejects_code_active_or_missing(self, monkeypatch, body):
        api = route_client(monkeypatch, user(*FULL))
        assert api.put(
            "/registrations/downtime-reasons/raw_material", json=body
        ).status_code == 422

    def test_patch_requires_boolean(self, monkeypatch):
        api = route_client(monkeypatch, user(*FULL))
        assert api.patch(
            "/registrations/downtime-reasons/x/active", json={"active": "maybe"}
        ).status_code == 422
        assert api.patch(
            "/registrations/downtime-reasons/x/active", json={}
        ).status_code == 422

    def test_no_secret_or_upstream_in_response(self, monkeypatch):
        api = route_client(monkeypatch, user(*FULL))
        response = api.get("/registrations/downtime-reasons")
        assert "service" not in response.text.lower()
        assert "token" not in response.text.lower()
