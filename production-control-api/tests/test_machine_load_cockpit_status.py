"""GET /machine-load/cockpit-status — estados MES locais do cockpit (Etapa 01).

Fonte oficial de execução para a Carga Máquina: production_runs +
work_center_state_events, nunca HZA/api-delpi nem Production Pulse.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from production_control_app.application.services.machine_load_cockpit_status_service import (
    MachineLoadCockpitStatusService,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    InvalidBranch,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PluginsDatabaseConnectionError,
)
from production_control_app.interface.http.routes import machine_load_routes as routes
from production_control_app.middleware.auth_middleware import (
    _is_internal_integration,
    _is_public_route,
)

FULL_PERMS = (
    "production-control.access",
    "production-control.machine-load.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)

_NOW = datetime(2026, 10, 16, 12, 0, 0, tzinfo=timezone.utc)


def _user(*permissions: str):
    return SimpleNamespace(is_superadmin=False, permissions=list(permissions), id="user-1")


def _row(**overrides: Any) -> dict[str, Any]:
    """Linha do JOIN live (runs + estado aberto) — shape do repositório real."""
    base = {
        "run_id": "11111111-2222-3333-4444-555555555555",
        "branch": "01",
        "work_center": "CT-35",
        "run_status": "running",
        "production_order": "24640401002",
        "operation_code": "03",
        "operator_code": "001234",
        "operator_name": "Maria Silva",
        "run_started_at": datetime(2026, 10, 16, 7, 30, tzinfo=timezone.utc),
        "state_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "operational_state": "producing",
        "state_source": "operator",
    }
    base.update(overrides)
    return base


class FakeMonitoringRepo:
    """Só o que o serviço consome do port — uma consulta em lote por filial."""

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows or []
        self.calls: list[str] = []

    def list_live_work_centers(self, *, branch: str) -> list[dict[str, Any]]:
        self.calls.append(branch)
        return list(self.rows)


def _service(
    rows: list[dict[str, Any]] | None = None,
) -> tuple[MachineLoadCockpitStatusService, FakeMonitoringRepo]:
    repo = FakeMonitoringRepo(rows)
    return (
        MachineLoadCockpitStatusService(
            repository=repo,
            branch_access=BranchAccessService(),
            clock=lambda: _NOW,
        ),
        repo,
    )


def _app(
    service: MachineLoadCockpitStatusService, user: Any | None
) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def _inject_user(request: Request, call_next):
        request.state.user = user
        return await call_next(request)

    app.include_router(routes.router)
    routes.build_machine_load_cockpit_status_service = lambda: service  # type: ignore[assignment]
    return TestClient(app)


# --- estados -----------------------------------------------------------------


def test_branch_isolation_each_call_uses_requested_branch() -> None:
    service, repo = _service([_row()])
    service.cockpit_status(_user(*FULL_PERMS), branch="01")
    service.cockpit_status(_user(*FULL_PERMS), branch="02")
    assert repo.calls == ["01", "02"]


def test_running_producing_is_producing() -> None:
    service, _ = _service([_row()])
    data = service.cockpit_status(_user(*FULL_PERMS), branch="01")
    item = data["items"][0]
    assert item["display_status"] == "producing"
    assert item["integrity_status"] == "complete"
    assert item["run_status"] == "running"
    assert item["operational_state"] == "producing"
    assert data["summary"]["producing"] == 1
    assert data["summary"]["active_runs"] == 1


def test_running_stopped_is_stopped_even_from_automatic_downtime() -> None:
    # Parada automática também gera evento 'stopped' aberto — a origem do
    # evento não muda a projeção.
    service, _ = _service([_row(operational_state="stopped", state_source="auto")])
    item = service.cockpit_status(_user(*FULL_PERMS), branch="01")["items"][0]
    assert item["display_status"] == "stopped"
    assert item["integrity_status"] == "complete"


def test_paused_stopped_is_paused() -> None:
    service, _ = _service([_row(run_status="paused", operational_state="stopped")])
    item = service.cockpit_status(_user(*FULL_PERMS), branch="01")["items"][0]
    assert item["display_status"] == "paused"
    assert item["integrity_status"] == "complete"


def test_closed_run_is_not_returned() -> None:
    service, _ = _service([_row(run_status="completed"), _row(run_status="aborted")])
    data = service.cockpit_status(_user(*FULL_PERMS), branch="01")
    assert data["items"] == []
    assert data["summary"]["active_runs"] == 0


def test_branch_without_open_runs_returns_empty_items_and_zeroed_summary() -> None:
    service, _ = _service([])
    data = service.cockpit_status(_user(*FULL_PERMS), branch="01")
    assert data["branch"] == "01"
    assert data["items"] == []
    assert data["summary"] == {
        "active_runs": 0,
        "producing": 0,
        "stopped": 0,
        "paused": 0,
        "unknown": 0,
    }


def test_open_run_without_mes_state_is_unknown_not_dropped() -> None:
    service, _ = _service([_row(operational_state=None)])
    item = service.cockpit_status(_user(*FULL_PERMS), branch="01")["items"][0]
    assert item["display_status"] == "unknown"
    assert item["integrity_status"] == "inconsistent"


@pytest.mark.parametrize(
    ("run_status", "operational_state"),
    [
        ("paused", "producing"),   # pausado não pode estar produzindo
        ("running", "paused"),     # valor fora do catálogo de estados
        ("running", None),         # running sozinho não prova produção
        ("running", ""),           # estado vazio é ausente
    ],
)
def test_inconsistent_states_never_get_false_classification(
    run_status: str, operational_state: str | None
) -> None:
    service, _ = _service(
        [_row(run_status=run_status, operational_state=operational_state)]
    )
    item = service.cockpit_status(_user(*FULL_PERMS), branch="01")["items"][0]
    assert item["display_status"] == "unknown"
    assert item["integrity_status"] == "inconsistent"
    # dados originais preservados para diagnóstico
    assert item["run_status"] == run_status


def test_duplicated_join_rows_collapse_into_one_item() -> None:
    run_id = "dup-run"
    service, _ = _service([_row(run_id=run_id), _row(run_id=run_id)])
    data = service.cockpit_status(_user(*FULL_PERMS), branch="01")
    assert len(data["items"]) == 1
    assert data["items"][0]["run_id"] == run_id


# --- identidade e contexto ----------------------------------------------------


def test_item_shape_and_timestamps() -> None:
    service, _ = _service([_row()])
    data = service.cockpit_status(_user(*FULL_PERMS), branch="01")
    assert data["branch"] == "01"
    assert data["source"] == "cockpit"
    assert data["as_of"] == _NOW.isoformat()
    item = data["items"][0]
    assert item["run_id"] == "11111111-2222-3333-4444-555555555555"
    assert item["work_center"] == "CT-35"
    assert item["production_order"] == "24640401002"
    assert item["operation_code"] == "03"
    assert item["started_at"] == "2026-10-16T07:30:00+00:00"


def test_payload_never_exposes_operator_identity() -> None:
    service, _ = _service([_row()])
    data = service.cockpit_status(_user(*FULL_PERMS), branch="01")
    for item in data["items"]:
        for key in item:
            assert "operator" not in key


def test_service_signature_has_no_remote_gateway() -> None:
    """Garantia estrutural: a consulta não pode chamar api-delpi nem Pulse."""
    params = set(inspect.signature(MachineLoadCockpitStatusService.__init__).parameters)
    assert params == {"self", "repository", "branch_access", "clock"}


# --- segurança -----------------------------------------------------------------


def test_unauthenticated_user_is_denied() -> None:
    service, _ = _service([_row()])
    with pytest.raises(PermissionError):
        service.cockpit_status(None, branch="01")


def test_missing_machine_load_view_permission() -> None:
    service, _ = _service([_row()])
    with pytest.raises(PermissionError):
        service.cockpit_status(
            _user("production-control.access", "production-control.view.filial-01"),
            branch="01",
        )


def test_user_without_branch_permission_is_denied() -> None:
    service, _ = _service([_row()])
    with pytest.raises(BranchAccessDenied):
        service.cockpit_status(
            _user(
                "production-control.access",
                "production-control.machine-load.view",
                "production-control.view.filial-01",
            ),
            branch="02",
        )


def test_invalid_branch_is_rejected() -> None:
    service, _ = _service([_row()])
    with pytest.raises(InvalidBranch):
        service.cockpit_status(_user(*FULL_PERMS), branch="03")


def test_cockpit_status_path_requires_jwt_middleware() -> None:
    """A rota não pode escapar para a lista pública nem para a faixa S2S."""
    assert _is_public_route("/machine-load/cockpit-status") is False
    assert _is_internal_integration("/machine-load/cockpit-status") is False


# --- contrato HTTP ---------------------------------------------------------------


def test_route_returns_envelope_with_snapshot() -> None:
    service, _ = _service([_row()])
    api = _app(service, _user(*FULL_PERMS))

    resp = api.get("/machine-load/cockpit-status?branch=01")

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["branch"] == "01"
    assert data["source"] == "cockpit"
    assert data["summary"]["producing"] == 1
    assert data["items"][0]["display_status"] == "producing"
    # identidade pessoal fora do contrato HTTP também
    assert not any("operator" in key for key in data["items"][0])


def test_route_branch_02_uses_own_permission_and_branch() -> None:
    service, repo = _service([_row(branch="02")])
    api = _app(service, _user(*FULL_PERMS))

    resp = api.get("/machine-load/cockpit-status?branch=02")

    assert resp.status_code == 200
    assert resp.json()["data"]["branch"] == "02"
    assert repo.calls == ["02"]


def test_route_without_user_is_denied() -> None:
    service, _ = _service([_row()])
    api = _app(service, None)

    resp = api.get("/machine-load/cockpit-status?branch=01")

    assert resp.status_code == 403
    assert resp.json()["success"] is False


def test_route_missing_machine_load_view_is_denied() -> None:
    service, _ = _service([_row()])
    api = _app(
        service,
        _user("production-control.access", "production-control.view.filial-01"),
    )

    resp = api.get("/machine-load/cockpit-status?branch=01")

    assert resp.status_code == 403


def test_route_wrong_branch_permission_is_denied() -> None:
    service, _ = _service([_row()])
    api = _app(
        service,
        _user(
            "production-control.access",
            "production-control.machine-load.view",
            "production-control.view.filial-01",
        ),
    )

    resp = api.get("/machine-load/cockpit-status?branch=02")

    assert resp.status_code == 403


def test_route_invalid_branch_is_422() -> None:
    service, _ = _service([_row()])
    api = _app(service, _user(*FULL_PERMS))

    resp = api.get("/machine-load/cockpit-status?branch=03")

    assert resp.status_code == 422


def test_route_database_down_is_controlled_failure_never_empty_list() -> None:
    class FailingRepo:
        def list_live_work_centers(self, *, branch: str) -> list[dict[str, Any]]:
            raise PluginsDatabaseConnectionError("postgres-plugins fora do ar")

    service = MachineLoadCockpitStatusService(
        repository=FailingRepo(),  # type: ignore[arg-type]
        branch_access=BranchAccessService(),
        clock=lambda: _NOW,
    )
    api = _app(service, _user(*FULL_PERMS))

    resp = api.get("/machine-load/cockpit-status?branch=01")

    assert resp.status_code == 503
    body = resp.json()
    assert body["success"] is False
    assert "items" not in (body.get("data") or {})
