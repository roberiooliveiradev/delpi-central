"""Problema de Processo pelo Portal PCP — criação autenticada (fila WORKING).

Cobre:
* autorização: production-control.machine-load + branch view +
  my-requests.process-issue.create, e access_token do principal;
* contexto: identidade completa (filial + CT + OP + operação) revalidada na
  fila WORKING vigente — retirada/transferência viram conflito, ausência 404;
* payload: source=pcp_portal, requester.name, contexto da operação,
  materiais SD4 best-effort;
* criação autenticada: Bearer do próprio analista, SEM service token —
  created_by = usuário real no Requests API;
* idempotência ponta a ponta e falha fechada quando o Requests API está fora.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.machine_load_service import (
    MachineLoadService,
)
from production_control_app.application.services.pcp_process_issue_service import (
    PcpProcessIssueService,
)
from production_control_app.domain.errors import (
    MachineLoadOperationNotFound,
    MachineLoadSequenceConflict,
    RequestsGatewayRejected,
    RequestsGatewayUnavailable,
)
from production_control_app.domain.services.branch_access_service import (
    BranchAccessService,
)
from production_control_app.interface.http.routes import machine_load_routes
from tests.test_machine_load import (
    FakeGateway,
    FakePublicationRepo,
    FakeSnapshotRepo,
    _OPERATION,
    _WORK_CENTERS,
)

PCP_PERMS = (
    "production-control.access",
    "production-control.machine-load.view",
    "production-control.view.filial-01",
    "my-requests.process-issue.create",
)


def _user(*permissions: str, access_token: str | None = "jwt-analyst"):
    return SimpleNamespace(
        id="u-pcp-1",
        name="Analista PCP",
        is_superadmin=False,
        permissions=list(permissions),
        access_token=access_token,
    )


def _context(**overrides: Any) -> dict[str, Any]:
    base = {
        "production_order": "24640401002",
        "operation_code": "03",
        "operation_description": "MONTAGEM",
        "work_center": "CT-63",
        "work_center_name": "Montagem 03",
        "product_code": "10045678",
        "product_description": "Componente",
        "pa_product_code": "90264238",
        "pa_product_description": "Produto acabado X",
        "tool": "F99999",
        "resource": "RES-01",
    }
    base.update(overrides)
    return base


class FakeMachineLoad:
    """Só o lookup do contexto WORKING."""

    def __init__(self, context: dict[str, Any] | None = None) -> None:
        self.context = context
        self.calls: list[dict[str, Any]] = []

    def pcp_operation_process_issue_context(self, user, **kwargs: Any):
        self.calls.append({"user": user, **kwargs})
        return self.context


class FakeMaterials:
    def __init__(self, items: list[dict[str, Any]] | None = None, *, fail: bool = False) -> None:
        self.items = items if items is not None else [
            {
                "product_code": "10081234",
                "description": "TERMINAL FASTON",
                "unit": "PC",
                "original_qty": 500.0,
                "open_qty": 120.0,
                "consumed_qty": 380.0,
            }
        ]
        self._fail = fail
        self.calls: list[dict[str, Any]] = []

    def list_for_feedback(self, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append(kwargs)
        if self._fail:
            raise RuntimeError("SD4 indisponível")
        return [dict(item) for item in self.items]


class FakeRequestsGateway:
    """Espelha RequestsApiGateway.create_request_as_user."""

    def __init__(self, result: dict[str, Any] | None = None, error: Exception | None = None) -> None:
        self.result = result or {
            "id": "req-1",
            "request_number": "REQ-2026-000001",
            "status": "submitted",
        }
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def create_request_as_user(self, *, access_token: str, body: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        self.calls.append(
            {"access_token": access_token, "body": body, "idempotency_key": idempotency_key}
        )
        if self.error is not None:
            raise self.error
        return dict(self.result)


def _service(
    machine_load: Any | None = None,
    gateway: FakeRequestsGateway | None = None,
    materials: FakeMaterials | None = None,
) -> PcpProcessIssueService:
    return PcpProcessIssueService(
        machine_load=machine_load or FakeMachineLoad(_context()),
        requests_gateway=gateway or FakeRequestsGateway(),
        operation_materials=materials if materials is not None else FakeMaterials(),
    )


def _report(service: PcpProcessIssueService, user=None, **overrides: Any):
    params = {
        "branch": "01",
        "work_center": "CT-63",
        "production_order": "24640401002",
        "operation_code": "03",
        "issue_code": "tool_not_linked",
        "tool_code": "F12345",
        "idempotency_key": "idem-1",
    }
    params.update(overrides)
    return service.report(user or _user(*PCP_PERMS), **params)


# --- autorização -------------------------------------------------------------


def test_report_requires_process_issue_create_permission():
    gateway = FakeRequestsGateway()
    service = _service(gateway=gateway)
    user = _user(
        "production-control.access",
        "production-control.machine-load.view",
        "production-control.view.filial-01",
    )
    with pytest.raises(PermissionError):
        _report(service, user=user)
    assert gateway.calls == []


def test_report_requires_user_access_token():
    gateway = FakeRequestsGateway()
    service = _service(gateway=gateway)
    with pytest.raises(PermissionError):
        _report(service, user=_user(*PCP_PERMS, access_token=None))
    assert gateway.calls == []


def test_report_rejects_service_principal():
    gateway = FakeRequestsGateway()
    service = _service(gateway=gateway)
    svc = _user(*PCP_PERMS)
    svc.principal_type = "service"
    with pytest.raises(PermissionError):
        _report(service, user=svc)
    assert gateway.calls == []


# --- payload e criação autenticada --------------------------------------------


def test_report_creates_with_real_user_bearer_and_pcp_source():
    machine_load = FakeMachineLoad(_context())
    gateway = FakeRequestsGateway()
    result = _report(_service(machine_load=machine_load, gateway=gateway), note="Falta tempo padrão")

    call = gateway.calls[0]
    assert call["access_token"] == "jwt-analyst"
    assert call["idempotency_key"] == "idem-1"
    headers_body = call["body"]
    assert headers_body["sourceApp"] == "production-control"
    assert headers_body["typeCode"] == "process-issue"
    assert headers_body["branch"] == "01"

    payload = headers_body["payload"]
    assert payload["source"] == "pcp_portal"
    assert payload["requester"] == {"name": "Analista PCP"}
    assert "operator" not in payload
    assert payload["issue"]["code"] == "tool_not_linked"
    assert payload["issue"]["reportedToolCode"] == "F12345"
    assert payload["issue"]["note"] == "Falta tempo padrão"
    assert payload["operation"]["productionOrder"] == "24640401002"
    assert payload["operation"]["reportedWorkCenter"] == "CT-63"
    assert payload["materialsSnapshotAvailable"] is True
    assert len(payload["materials"]) == 1

    assert result["requestNumber"] == "REQ-2026-000001"
    assert result["status"] == "submitted"

    ctx_call = machine_load.calls[0]
    assert ctx_call["branch"] == "01"
    assert ctx_call["work_center"] == "CT-63"
    assert ctx_call["production_order"] == "24640401002"
    assert ctx_call["operation_code"] == "03"


def test_materials_failure_degrades_without_blocking():
    gateway = FakeRequestsGateway()
    service = _service(gateway=gateway, materials=FakeMaterials(fail=True))
    _report(service)
    payload = gateway.calls[0]["body"]["payload"]
    assert payload["materialsSnapshotAvailable"] is False
    assert payload["materials"] == []


def test_requests_api_down_fails_closed():
    service = _service(
        gateway=FakeRequestsGateway(
            error=RequestsGatewayUnavailable("Serviço de solicitações indisponível.")
        )
    )
    with pytest.raises(RequestsGatewayUnavailable):
        _report(service)


def test_upstream_rejection_propagates_message():
    service = _service(
        gateway=FakeRequestsGateway(
            error=RequestsGatewayRejected("Motivo de problema de processo desconhecido.")
        )
    )
    with pytest.raises(RequestsGatewayRejected):
        _report(service)


# --- contexto na fila WORKING (MachineLoadService real) -----------------------


def _machine_load(snapshots: FakeSnapshotRepo) -> MachineLoadService:
    return MachineLoadService(
        FakeGateway(),
        snapshots=snapshots,
        publications=FakePublicationRepo(snapshots.published),
        branch_access=BranchAccessService(),
        open_run_items=lambda **kwargs: [],
    )


def _seed(snapshots: FakeSnapshotRepo, **op_overrides: Any) -> None:
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 8, 19),
        end_date=date(2026, 9, 2),
        payload={
            "work_centers": _WORK_CENTERS,
            "operations": [{**_OPERATION, **op_overrides}],
            "summary": {},
        },
        refreshed_by="pcp",
    )


def test_context_resolves_working_operation_without_publication():
    """AC-05: operação na WORKING ainda não publicada é elegível."""
    snapshots = FakeSnapshotRepo()
    _seed(snapshots)
    assert snapshots.published == {}

    context = _machine_load(snapshots).pcp_operation_process_issue_context(
        _user(*PCP_PERMS),
        branch="01",
        work_center="CT-02",
        production_order="24640401002",
        operation_code="03",
    )
    assert context["work_center"] == "CT-02"
    assert context["production_order"] == "24640401002"
    assert context["tool"] == "23-B31"


def test_context_not_found_raises_404_error():
    snapshots = FakeSnapshotRepo()
    _seed(snapshots)
    with pytest.raises(MachineLoadOperationNotFound):
        _machine_load(snapshots).pcp_operation_process_issue_context(
            _user(*PCP_PERMS),
            branch="01",
            work_center="CT-02",
            production_order="99999999999",
            operation_code="03",
        )


def test_context_wrong_work_center_is_conflict():
    snapshots = FakeSnapshotRepo()
    _seed(snapshots)
    with pytest.raises(MachineLoadSequenceConflict):
        _machine_load(snapshots).pcp_operation_process_issue_context(
            _user(*PCP_PERMS),
            branch="01",
            work_center="CT-01A",
            production_order="24640401002",
            operation_code="03",
        )


def test_context_withdrawn_operation_is_conflict():
    snapshots = FakeSnapshotRepo()
    _seed(snapshots)
    service = _machine_load(snapshots)
    service.withdraw_operations(
        _user(*PCP_PERMS),
        branch="01",
        operations=[
            {
                "work_center": "CT-02",
                "production_order": "24640401002",
                "operation_code": "03",
            }
        ],
        expected_keys=[
            {"production_order": "24640401002", "operation_code": "03"}
        ],
    )
    with pytest.raises(MachineLoadSequenceConflict):
        service.pcp_operation_process_issue_context(
            _user(*PCP_PERMS),
            branch="01",
            work_center="CT-02",
            production_order="24640401002",
            operation_code="03",
        )


def test_context_transferred_operation_resolves_in_new_center():
    snapshots = FakeSnapshotRepo()
    _seed(snapshots)
    service = _machine_load(snapshots)
    service.transfer_operation(
        _user(*PCP_PERMS),
        branch="01",
        production_order="24640401002",
        operation_code="03",
        target_work_center="CT-01A",
        work_center="CT-02",
    )
    context = service.pcp_operation_process_issue_context(
        _user(*PCP_PERMS),
        branch="01",
        work_center="CT-01A",
        production_order="24640401002",
        operation_code="03",
    )
    assert context["work_center"] == "CT-01A"
    with pytest.raises(MachineLoadSequenceConflict):
        service.pcp_operation_process_issue_context(
            _user(*PCP_PERMS),
            branch="01",
            work_center="CT-02",
            production_order="24640401002",
            operation_code="03",
        )


def test_context_requires_machine_load_view():
    snapshots = FakeSnapshotRepo()
    _seed(snapshots)
    user = _user("production-control.access", "production-control.view.filial-01")
    with pytest.raises(PermissionError):
        _machine_load(snapshots).pcp_operation_process_issue_context(
            user,
            branch="01",
            work_center="CT-02",
            production_order="24640401002",
            operation_code="03",
        )


# --- rota autenticada ----------------------------------------------------------


class FakePcpService:
    def __init__(self, result=None, error=None) -> None:
        self.result = result or {
            "requestId": "req-1",
            "requestNumber": "REQ-2026-000001",
            "status": "submitted",
            "message": "Solicitação enviada para Processos com sucesso.",
        }
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def report(self, user, **kwargs: Any):
        self.calls.append({"user": user, **kwargs})
        if self.error is not None:
            raise self.error
        return self.result


def _client(service: FakePcpService) -> TestClient:
    machine_load_routes.build_pcp_process_issue_service = lambda: service  # type: ignore[assignment]
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = _user(*PCP_PERMS)
        return await call_next(request)

    app.include_router(machine_load_routes.router)
    return TestClient(app)


@pytest.fixture
def restore_builder():
    original = machine_load_routes.build_pcp_process_issue_service
    yield
    machine_load_routes.build_pcp_process_issue_service = original  # type: ignore[assignment]


def _post(client: TestClient, **body_overrides):
    body = {
        "work_center": "CT-02",
        "production_order": "24640401002",
        "operation_code": "03",
        "issue_code": "tool_not_linked",
    }
    body.update(body_overrides)
    return client.post(
        "/machine-load/process-issues",
        params={"branch": "01"},
        json=body,
        headers={"Idempotency-Key": "idem-route-1"},
    )


def test_route_happy_path_returns_created_request(restore_builder):
    service = FakePcpService()
    response = _post(_client(service))
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["requestNumber"] == "REQ-2026-000001"
    assert service.calls[0]["idempotency_key"] == "idem-route-1"


def test_route_requires_idempotency_key(restore_builder):
    response = _client(FakePcpService()).post(
        "/machine-load/process-issues",
        params={"branch": "01"},
        json={
            "work_center": "CT-02",
            "production_order": "1",
            "operation_code": "03",
            "issue_code": "other",
        },
    )
    assert response.status_code == 422


def test_route_maps_not_found_and_conflict(restore_builder):
    response = _post(
        _client(FakePcpService(error=MachineLoadOperationNotFound("não achou")))
    )
    assert response.status_code == 404
    response = _post(
        _client(FakePcpService(error=MachineLoadSequenceConflict("mudou")))
    )
    assert response.status_code == 409


def test_route_maps_permission_and_gateway_errors(restore_builder):
    response = _post(_client(FakePcpService(error=PermissionError("sem perm"))))
    assert response.status_code == 403
    response = _post(
        _client(FakePcpService(error=RequestsGatewayUnavailable("fora")))
    )
    assert response.status_code == 502
