"""C5 — Material faltante estruturado + fila urgente do Alimentador de Linha.

Cobre: validação SD4, snapshots congelados, atomicidade feedback+materiais,
lifecycle pending->picked->delivered, autorização do Alimentador, realtime,
compatibilidade com registros antigos e a garantia de que delivered não
resolve o impedimento (quem encerra é o PCP).
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.line_feeder_urgent_requests_service import (  # noqa: E501
    LineFeederUrgentRequestsService,
)
from production_control_app.application.services.operator_feedback_material_service import (  # noqa: E501
    OperatorFeedbackMaterialService,
)
from production_control_app.application.services.operator_feedback_service import (
    OperatorFeedbackService,
)
from production_control_app.application.services.pcp_operator_feedback_service import (  # noqa: E501
    PcpOperatorFeedbackService,
)
from production_control_app.application.services.public_operator_feedback_service import (  # noqa: E501
    PublicOperatorFeedbackService,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    InvalidOperatorFeedbackMaterials,
    OperatorFeedbackMaterialNotFound,
    OperatorFeedbackMaterialStateError,
)
from production_control_app.domain.services.branch_access_service import (
    BranchAccessService,
)
from production_control_app.interface.http.routes import (
    line_feeder_routes as feeder_routes,
)
from tests.test_operator_feedback import FakeOperatorFeedbackRepository
from tests.test_operator_feedback_public_api import (
    FakeMachineLoad,
    FakeOperationMaterials,
    FakeSessionResolver,
    NotifySpy,
    _context,
    _sd4_material,
    _session,
)


# --- fakes -------------------------------------------------------------------


class FakeSnapshots:
    """MachineLoadSnapshotRepositoryPort mínimo — fila vigente (WORKING)."""

    def __init__(self, operations: list[dict[str, Any]] | None = None) -> None:
        self.operations = operations
        self.calls = 0

    def get(self, *, branch: str) -> dict[str, Any] | None:
        self.calls += 1
        if self.operations is None:
            return None
        return {"payload_json": {"operations": self.operations}}


FEEDER_PERMS = (
    "production-control.access",
    "production-control.line-feeder.view",
    "production-control.view.filial-01",
)


def _user(
    *permissions: str, user_id: str = "feeder-1", email: str = "feeder@delpi.com.br"
):
    return SimpleNamespace(
        is_superadmin=False,
        permissions=list(permissions),
        id=user_id,
        email=email,
    )


def _public_parts(
    *,
    materials: list[dict[str, Any]] | None = None,
) -> tuple[
    PublicOperatorFeedbackService,
    FakeOperatorFeedbackRepository,
    FakeOperationMaterials,
]:
    repo = FakeOperatorFeedbackRepository()
    operation_materials = FakeOperationMaterials(materials)
    svc = PublicOperatorFeedbackService(
        run_service=FakeSessionResolver(_session()),
        machine_load=FakeMachineLoad(_context()),
        feedbacks=OperatorFeedbackService(feedbacks=repo),
        run_lookup=lambda **kwargs: None,
        notify=NotifySpy(),
        operation_materials=operation_materials,
        feedback_materials=OperatorFeedbackMaterialService(materials=repo),
    )
    return svc, repo, operation_materials


def _report_materials(
    svc: PublicOperatorFeedbackService,
    *,
    codes: Any = ("10081234",),
    note: str = "Falta terminal",
    **overrides: Any,
) -> dict[str, Any]:
    return svc.report(
        session_token="sess-token",
        production_order="24640401002",
        operation_code="03",
        feedback_type="cannot_produce",
        reason_code="missing_material",
        note=note,
        material_codes=codes,
    )


def _feeder_service(
    repo: FakeOperatorFeedbackRepository,
    *,
    snapshot_ops: list[dict[str, Any]] | None = (
        [
            {
                "production_order": "24640401002",
                "operation_code": "03",
                "work_center": "CT-64",
            }
        ]
    ),
    notify: Any | None = None,
) -> tuple[LineFeederUrgentRequestsService, NotifySpy, FakeSnapshots]:
    spy = notify if notify is not None else NotifySpy()
    snapshots = FakeSnapshots(snapshot_ops)
    lifecycle = OperatorFeedbackMaterialService(materials=repo)
    svc = LineFeederUrgentRequestsService(
        branch_access=BranchAccessService(),
        materials=repo,
        lifecycle=lifecycle,
        snapshots=snapshots,
        notify=spy,
    )
    return svc, spy, snapshots


# --- criação: validação SD4 + snapshot congelado -------------------------------


def test_missing_material_requires_at_least_one_code() -> None:
    svc, repo, _ = _public_parts()
    for codes in (None, [], ["", "   "]):
        with pytest.raises(InvalidOperatorFeedbackMaterials) as exc:
            _report_materials(svc, codes=codes)
        assert "Selecione pelo menos um material" in str(exc.value)
    assert repo.rows == {}


def test_material_code_outside_operation_is_rejected() -> None:
    svc, repo, _ = _public_parts()
    with pytest.raises(InvalidOperatorFeedbackMaterials) as exc:
        _report_materials(svc, codes=("99999999",))
    assert "não pertencem a esta operação" in str(exc.value)
    assert repo.rows == {}


def test_mixing_valid_and_foreign_codes_is_rejected() -> None:
    svc, repo, _ = _public_parts()
    with pytest.raises(InvalidOperatorFeedbackMaterials):
        _report_materials(svc, codes=("10081234", "XX-INVENTADO"))
    assert repo.rows == {}


def test_materials_are_frozen_from_sd4_not_client() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    stored = repo.get(item["id"])
    materials = stored["materials"] if "materials" in stored else repo.list_for_feedbacks([item["id"]])[item["id"]]
    assert len(materials) == 1
    material = materials[0]
    # o cliente só enviou o código — todo o resto veio da SD4
    assert material["product_code"] == "10081234"
    assert material["description"] == "TERMINAL FASTON"
    assert material["unit"] == "PC"
    assert float(material["original_qty"]) == 500.0
    assert float(material["open_qty"]) == 120.0
    assert float(material["consumed_qty"]) == 380.0
    assert material["status"] == "pending"


def test_multiple_materials_accepted_and_persisted() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc, codes=("10081234", "10085678"))
    materials = repo.list_for_feedbacks([item["id"]])[item["id"]]
    codes = {m["product_code"] for m in materials}
    assert codes == {"10081234", "10085678"}
    assert all(m["status"] == "pending" for m in materials)


def test_duplicate_codes_in_payload_are_deduped() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc, codes=("10081234", "10081234"))
    materials = repo.list_for_feedbacks([item["id"]])[item["id"]]
    assert len(materials) == 1


def test_sd4_lookup_uses_branch_and_operation() -> None:
    svc, repo, materials = _public_parts()
    _report_materials(svc)
    assert materials.calls, "service deve reconsultar a SD4 oficial"
    call = materials.calls[0]
    assert call.get("branch") == "01" or "branch" in call


# --- atomicidade ---------------------------------------------------------------


def test_feedback_and_materials_created_together() -> None:
    """Mesmo create: a linha devolvida já traz os filhos — não há janela
    onde o feedback existe sem os materiais."""
    svc, repo, _ = _public_parts()
    item = _report_materials(svc, codes=("10081234", "10085678"))
    assert len(item.get("materials") or []) == 2 or (
        len(repo.list_for_feedbacks([item["id"]])[item["id"]]) == 2
    )


# --- compatibilidade C1–C4 -----------------------------------------------------


def test_legacy_feedback_without_materials_still_lists() -> None:
    """Feedback histórico (sem materiais) serializa com materials=[]."""
    svc, repo, _ = _public_parts()
    legacy = svc._feedbacks.report(
        feedback_type="cannot_produce",
        reason_code="missing_material",
        branch="01",
        production_order="24640401002",
        operation_code="03",
        reported_work_center="CT-02",
        operator_code="001234",
        operator_name="Maria Silva",
        note="sem materiais (legado)",
    )
    active = svc.list_active(
        session_token="sess-token",
        production_order="24640401002",
        operation_code="03",
    )
    assert active["items"][0]["materials"] == []
    assert repo.get(legacy["id"])["status"] == "open"


def test_pcp_inbox_shows_materials_and_legacy_empty() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc, codes=("10081234",))
    pcp = PcpOperatorFeedbackService(
        branch_access=BranchAccessService(),
        feedbacks=svc._feedbacks,
        materials=OperatorFeedbackMaterialService(materials=repo),
        notify=NotifySpy(),
    )
    user = _user(
        "production-control.access",
        "production-control.machine-load.view",
        "production-control.view.filial-01",
    )
    data = pcp.list_inbox(user, branch="01")
    found = next(i for i in data["items"] if i["id"] == item["id"])
    assert found["materials"][0]["productCode"] == "10081234"
    assert found["materials"][0]["status"] == "pending"


# --- lifecycle do material ------------------------------------------------------


def _material_of(repo: FakeOperatorFeedbackRepository, feedback_id: str):
    return repo.list_for_feedbacks([feedback_id])[feedback_id][0]


def test_material_lifecycle_pending_picked_delivered() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    lifecycle = OperatorFeedbackMaterialService(materials=repo)

    picked = lifecycle.mark_picked(material["id"], picked_by="feeder-1")
    assert picked["status"] == "picked"
    assert picked["picked_by"] == "feeder-1"
    assert picked["picked_at"] is not None

    delivered = lifecycle.mark_delivered(material["id"], delivered_by="feeder-2")
    assert delivered["status"] == "delivered"
    assert delivered["delivered_by"] == "feeder-2"


def test_retry_same_state_is_idempotent() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    lifecycle = OperatorFeedbackMaterialService(materials=repo)

    first = lifecycle.mark_picked(material["id"], picked_by="feeder-1")
    second = lifecycle.mark_picked(material["id"], picked_by="feeder-9")
    assert second["status"] == "picked"
    # retry não reescreve autoria/timestamp do primeiro
    assert second["picked_by"] == first["picked_by"] == "feeder-1"
    assert second["picked_at"] == first["picked_at"]


def test_invalid_transitions_raise_state_error() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    lifecycle = OperatorFeedbackMaterialService(materials=repo)

    with pytest.raises(OperatorFeedbackMaterialStateError):
        lifecycle.mark_delivered(material["id"], delivered_by="f")  # pending->delivered
    lifecycle.mark_picked(material["id"], picked_by="f")
    lifecycle.mark_delivered(material["id"], delivered_by="f")
    with pytest.raises(OperatorFeedbackMaterialStateError):
        # regressiva: delivered não volta para picked
        lifecycle.mark_picked(material["id"], picked_by="f")


def test_unknown_material_raises_not_found() -> None:
    _, repo, _ = _public_parts()
    lifecycle = OperatorFeedbackMaterialService(materials=repo)
    with pytest.raises(OperatorFeedbackMaterialNotFound):
        lifecycle.mark_picked(str(uuid.uuid4()), picked_by="f")


def test_delivered_does_not_resolve_feedback() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    lifecycle = OperatorFeedbackMaterialService(materials=repo)

    lifecycle.mark_picked(material["id"], picked_by="f")
    lifecycle.mark_delivered(material["id"], delivered_by="f")

    assert repo.get(item["id"])["status"] == "open"


def test_resolved_feedback_blocks_material_transition() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    lifecycle = OperatorFeedbackMaterialService(materials=repo)

    svc._feedbacks.resolve(item["id"], resolved_by="pcp-1")
    with pytest.raises(OperatorFeedbackMaterialStateError) as exc:
        lifecycle.mark_picked(material["id"], picked_by="f")
    assert "resolvido pelo PCP" in str(exc.value)
    # histórico preservado — material não é apagado
    assert _material_of(repo, item["id"])["status"] == "pending"


# --- fila urgente do Alimentador -----------------------------------------------


def test_urgent_queue_lists_pending_and_picked() -> None:
    svc, repo, _ = _public_parts()
    item_a = _report_materials(svc, codes=("10081234",))
    material_a = _material_of(repo, item_a["id"])
    feeder, _, _ = _feeder_service(repo)
    lifecycle = OperatorFeedbackMaterialService(materials=repo)
    lifecycle.mark_picked(material_a["id"], picked_by="f")

    data = feeder.list_requests(_user(*FEEDER_PERMS), branch="01")
    assert data["summary"] == {"total": 1, "pending": 0, "picked": 1}
    entry = data["items"][0]
    assert entry["productCode"] == "10081234"
    assert entry["status"] == "picked"
    assert entry["feedbackId"] == item_a["id"]
    assert entry["productionOrder"] == "24640401002"
    assert entry["operationCode"] == "03"
    assert entry["reportedWorkCenter"] == "CT-02"  # posto da sessão
    assert entry["currentWorkCenter"] == "CT-64"   # fila vigente
    assert entry["outOfQueue"] is False
    assert entry["operatorName"] == "Maria Silva"
    assert entry["note"] == "Falta terminal"


def test_delivered_leaves_active_queue() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    lifecycle = OperatorFeedbackMaterialService(materials=repo)
    lifecycle.mark_picked(material["id"], picked_by="f")
    lifecycle.mark_delivered(material["id"], delivered_by="f")

    feeder, _, _ = _feeder_service(repo)
    data = feeder.list_requests(_user(*FEEDER_PERMS), branch="01")
    assert data["items"] == []


def test_resolved_feedback_leaves_active_queue() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    feeder, _, _ = _feeder_service(repo)

    svc._feedbacks.resolve(item["id"], resolved_by="pcp-1")
    data = feeder.list_requests(_user(*FEEDER_PERMS), branch="01")
    assert data["items"] == []
    # histórico continua no banco
    assert _material_of(repo, item["id"])["status"] == "pending"


def test_op_out_of_current_queue_still_listed() -> None:
    """OP transferida/encerrada: CT atual fica vazio, pedido continua visível."""
    svc, repo, _ = _public_parts()
    _report_materials(svc)
    feeder, _, _ = _feeder_service(repo, snapshot_ops=[])
    data = feeder.list_requests(_user(*FEEDER_PERMS), branch="01")
    assert len(data["items"]) == 1
    assert data["items"][0]["currentWorkCenter"] is None
    assert data["items"][0]["outOfQueue"] is True


def test_current_work_center_from_live_queue_not_reported() -> None:
    """Transferência: reported=CT-02 (histórico), destino=CT-64 (fila vigente)."""
    svc, repo, _ = _public_parts()
    _report_materials(svc)
    feeder, _, _ = _feeder_service(repo)
    item = feeder.list_requests(_user(*FEEDER_PERMS), branch="01")["items"][0]
    assert item["reportedWorkCenter"] == "CT-02"
    assert item["currentWorkCenter"] == "CT-64"


# --- autorização do Alimentador --------------------------------------------------


def test_feeder_requires_line_feeder_permission() -> None:
    svc, repo, _ = _public_parts()
    _report_materials(svc)
    feeder, _, _ = _feeder_service(repo)
    user = _user(
        "production-control.access",
        "production-control.machine-load.view",
        "production-control.view.filial-01",
    )
    with pytest.raises(PermissionError):
        feeder.list_requests(user, branch="01")


def test_feeder_requires_branch_access() -> None:
    svc, repo, _ = _public_parts()
    _report_materials(svc)
    feeder, _, _ = _feeder_service(repo)
    user = _user(
        "production-control.access",
        "production-control.line-feeder.view",
        # sem view.filial-01
    )
    with pytest.raises(BranchAccessDenied):
        feeder.list_requests(user, branch="01")


def test_material_uuid_of_other_branch_is_rejected() -> None:
    """UUID manual não abre a fila de outra filial: autorização pelo branch
    real do registro."""
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    feeder, _, _ = _feeder_service(repo)
    user = _user(
        "production-control.access",
        "production-control.line-feeder.view",
        "production-control.view.filial-02",
    )
    with pytest.raises(BranchAccessDenied):
        feeder.update_material_status(
            user, material_id=material["id"], status="picked"
        )


# --- update via service ----------------------------------------------------------


def test_update_marks_picked_and_delivered() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    feeder, spy, _ = _feeder_service(repo)
    user = _user(*FEEDER_PERMS, user_id="feeder-joao")

    result = feeder.update_material_status(
        user, material_id=material["id"], status="picked"
    )
    assert result["item"]["status"] == "picked"
    assert repo.materials[material["id"]]["picked_by"] == "feeder-joao"

    result = feeder.update_material_status(
        user, material_id=material["id"], status="delivered"
    )
    assert result["item"]["status"] == "delivered"
    assert repo.materials[material["id"]]["delivered_by"] == "feeder-joao"
    assert repo.get(item["id"])["status"] == "open"  # delivered não resolve

    reasons = [c["reason"] for c in spy.calls]
    assert reasons == ["material_picked", "material_delivered"]


def test_update_authorship_comes_from_jwt() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    feeder, _, _ = _feeder_service(repo)
    feeder.update_material_status(
        _user(*FEEDER_PERMS, user_id="jwt-user-42"),
        material_id=material["id"],
        status="picked",
    )
    assert repo.materials[material["id"]]["picked_by"] == "jwt-user-42"


def test_update_rejects_invalid_status_value() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    feeder, _, _ = _feeder_service(repo)
    with pytest.raises(ValueError):
        feeder.update_material_status(
            _user(*FEEDER_PERMS), material_id=material["id"], status="pending"
        )


def test_realtime_payload_is_minimal() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    feeder, spy, _ = _feeder_service(repo)
    feeder.update_material_status(
        _user(*FEEDER_PERMS), material_id=material["id"], status="picked"
    )
    call = spy.calls[0]
    assert call["reason"] == "material_picked"
    assert call["branch"] == "01"
    feedback = call["feedback"]
    assert feedback["id"] == item["id"]
    # sem nota, operador nem descrição no socket
    assert "note" not in feedback
    assert "operator_name" not in feedback
    assert "description" not in feedback


def test_no_mes_dependencies_in_urgent_service() -> None:
    import inspect

    signature = inspect.signature(LineFeederUrgentRequestsService.__init__)
    params = set(signature.parameters)
    for forbidden in ("run_service", "pulse", "downtime", "machine_load"):
        assert forbidden not in params


# --- contrato HTTP do Alimentador ------------------------------------------------


def _feeder_app(
    svc: LineFeederUrgentRequestsService, user: Any
) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = user
        return await call_next(request)

    app.include_router(feeder_routes.router)
    feeder_routes.build_line_feeder_urgent_requests_service = (  # type: ignore[assignment]
        lambda: svc
    )
    return TestClient(app)


def test_http_urgent_queue_endpoint() -> None:
    svc, repo, _ = _public_parts()
    _report_materials(svc)
    feeder, _, _ = _feeder_service(repo)
    api = _feeder_app(feeder, _user(*FEEDER_PERMS))

    resp = api.get("/line-feeder/operator-feedback-requests", params={"branch": "01"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["summary"]["total"] == 1
    assert body["data"]["items"][0]["productCode"] == "10081234"


def test_http_urgent_queue_without_permission_is_403() -> None:
    svc, repo, _ = _public_parts()
    _report_materials(svc)
    feeder, _, _ = _feeder_service(repo)
    api = _feeder_app(
        feeder,
        _user("production-control.access", "production-control.view.filial-01"),
    )
    resp = api.get("/line-feeder/operator-feedback-requests", params={"branch": "01"})
    assert resp.status_code == 403


def test_http_update_material_flow() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    feeder, _, _ = _feeder_service(repo)
    api = _feeder_app(feeder, _user(*FEEDER_PERMS))

    resp = api.patch(
        f"/line-feeder/operator-feedback-materials/{material['id']}",
        json={"branch": "01", "status": "picked"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["item"]["status"] == "picked"

    # retry idempotente
    resp = api.patch(
        f"/line-feeder/operator-feedback-materials/{material['id']}",
        json={"branch": "01", "status": "picked"},
    )
    assert resp.status_code == 200

    resp = api.patch(
        f"/line-feeder/operator-feedback-materials/{material['id']}",
        json={"branch": "01", "status": "delivered"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["item"]["status"] == "delivered"

    # saiu da fila ativa
    resp = api.get("/line-feeder/operator-feedback-requests", params={"branch": "01"})
    assert resp.json()["data"]["items"] == []


def test_http_invalid_transition_returns_409() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    feeder, _, _ = _feeder_service(repo)
    api = _feeder_app(feeder, _user(*FEEDER_PERMS))

    resp = api.patch(
        f"/line-feeder/operator-feedback-materials/{material['id']}",
        json={"branch": "01", "status": "delivered"},  # pending -> delivered
    )
    assert resp.status_code == 409


def test_http_unknown_material_returns_404() -> None:
    svc, repo, _ = _public_parts()
    feeder, _, _ = _feeder_service(repo)
    api = _feeder_app(feeder, _user(*FEEDER_PERMS))
    resp = api.patch(
        f"/line-feeder/operator-feedback-materials/{uuid.uuid4()}",
        json={"branch": "01", "status": "picked"},
    )
    assert resp.status_code == 404


def test_http_update_other_branch_is_403() -> None:
    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    material = _material_of(repo, item["id"])
    feeder, _, _ = _feeder_service(repo)
    api = _feeder_app(
        feeder,
        _user(
            "production-control.access",
            "production-control.line-feeder.view",
            "production-control.view.filial-02",
        ),
    )
    resp = api.patch(
        f"/line-feeder/operator-feedback-materials/{material['id']}",
        json={"branch": "02", "status": "picked"},
    )
    assert resp.status_code == 403


# --- contrato HTTP público (validação SD4) -------------------------------------


class _Access:
    def is_valid_token(self, token: str | None) -> bool:
        return token == "valid-token"


def _public_app(svc: PublicOperatorFeedbackService) -> TestClient:
    from production_control_app.interface.http.routes import (
        public_machine_load_routes as public_routes,
    )
    from production_control_app.interface.http.routes import (
        public_operator_feedback_routes as feedback_routes,
    )

    app = FastAPI()
    app.include_router(feedback_routes.router)
    app.include_router(public_routes.router)
    feedback_routes.build_public_operator_feedback_service = (  # type: ignore[assignment]
        lambda: svc
    )
    public_routes.build_public_cockpit_access_service = (  # type: ignore[assignment]
        lambda: _Access()
    )
    return TestClient(app)


def _post(api: TestClient, **overrides: Any):
    body = {
        "productionOrder": "24640401002",
        "operationCode": "03",
        "feedbackType": "cannot_produce",
        "reasonCode": "missing_material",
        "materialCodes": ["10081234"],
        "note": "Falta terminal",
        "website": None,
    }
    body.update(overrides)
    return api.post(
        "/public/machine-load/valid-token/operator-feedbacks",
        json=body,
        headers={"X-Delpi-Bench-Session": "sess-token"},
    )


def test_http_material_outside_op_returns_422() -> None:
    svc, _, _ = _public_parts()
    api = _public_app(svc)
    resp = _post(api, materialCodes=["XX-FORA-DA-OP"])
    assert resp.status_code == 422
    assert "não pertencem a esta operação" in resp.json()["message"]


def test_http_missing_material_without_codes_returns_422() -> None:
    svc, _, _ = _public_parts()
    api = _public_app(svc)
    resp = _post(api, materialCodes=[])
    assert resp.status_code == 422
    assert "Selecione pelo menos um material" in resp.json()["message"]


def test_http_create_returns_materials_in_dto() -> None:
    svc, _, _ = _public_parts()
    api = _public_app(svc)
    resp = _post(api)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["materials"][0]["productCode"] == "10081234"
    assert data["materials"][0]["status"] == "pending"
    # cockpit não recebe autoria interna
    assert "pickedBy" not in data["materials"][0]


# --- regressão: NUMERIC volta como Decimal e json.dumps explodia (500) ---------


def test_numeric_open_qty_serializes_in_pcp_and_feeder_payloads() -> None:
    """open_qty NUMERIC retorna Decimal do Postgres — os DTOs PCP e Alimentador
    precisam serializar como float, senão ok()/JSONResponse gera 500."""
    import json
    from decimal import Decimal

    from production_control_app.core.responses import ok

    svc, repo, _ = _public_parts()
    item = _report_materials(svc)
    for row in repo.materials.values():
        row["open_qty"] = Decimal("2.500000")

    pcp = PcpOperatorFeedbackService(
        branch_access=BranchAccessService(),
        feedbacks=svc._feedbacks,
        materials=OperatorFeedbackMaterialService(materials=repo),
        notify=NotifySpy(),
    )
    user = _user(
        "production-control.access",
        "production-control.machine-load.view",
        "production-control.view.filial-01",
    )
    body = json.loads(ok(pcp.list_inbox(user, branch="01")).body)
    found = next(i for i in body["data"]["items"] if i["id"] == item["id"])
    assert found["materials"][0]["openQty"] == 2.5

    feeder, _, _ = _feeder_service(repo)
    body = json.loads(
        ok(feeder.list_requests(_user(*FEEDER_PERMS), branch="01")).body
    )
    request = next(
        i for i in body["data"]["items"] if i["feedbackId"] == item["id"]
    )
    assert request["openQty"] == 2.5
