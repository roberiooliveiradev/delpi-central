"""C4 — Inbox e tratativa do Operator Feedback no Portal PCP."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.operator_feedback_service import (
    OperatorFeedbackService,
)
from production_control_app.application.services.pcp_operator_feedback_service import (  # noqa: E501
    PcpOperatorFeedbackService,
)
from production_control_app.domain.errors import (
    BranchAccessDenied,
    OperatorFeedbackNotFound,
    OperatorFeedbackStateError,
)
from production_control_app.domain.services.branch_access_service import (
    BranchAccessService,
)
from production_control_app.interface.http.routes import (
    operator_feedback_routes as feedback_routes,
)
from tests.test_operator_feedback import FakeOperatorFeedbackRepository

FULL_PERMS = (
    "production-control.access",
    "production-control.machine-load.view",
    "production-control.view.filial-01",
    "production-control.view.filial-02",
)


def _user(*permissions: str, user_id: str = "pcp-1", email: str = "pcp@delpi.com.br"):
    return SimpleNamespace(
        is_superadmin=False,
        permissions=list(permissions),
        id=user_id,
        email=email,
    )


def _pcp(**overrides: Any) -> Any:
    base = {
        "feedback_type": "cannot_produce",
        "reason_code": "missing_material",
        "branch": "01",
        "production_order": "24640401002",
        "operation_code": "03",
        "reported_work_center": "CT-63",
        "operator_code": "001234",
        "operator_name": "Maria Silva",
        "note": "Falta terminal 10081234",
        "product_code": "TR-1234",
        "product_description": "Transformador 15kVA",
        "pa_product_code": "PA-5678",
        "due_date": "2026-10-08",
    }
    base.update(overrides)
    return base


class NotifySpy:
    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[dict[str, Any]] = []
        self._fail = fail

    def __call__(self, **kwargs: Any) -> None:
        if self._fail:
            raise RuntimeError("socket down")
        self.calls.append(kwargs)


def _service(
    *, notify: Any | None = None
) -> tuple[PcpOperatorFeedbackService, dict[str, Any]]:
    repo = FakeOperatorFeedbackRepository()
    domain = OperatorFeedbackService(feedbacks=repo)
    svc = PcpOperatorFeedbackService(
        branch_access=BranchAccessService(),
        feedbacks=domain,
        notify=notify if notify is not None else NotifySpy(),
    )
    return svc, {"repo": repo, "domain": domain}


def _report(domain: OperatorFeedbackService, **overrides: Any) -> dict[str, Any]:
    return domain.report(**_pcp(**overrides))


# --- listagem da inbox ----------------------------------------------------------


def test_inbox_lists_only_active_feedback() -> None:
    svc, ctx = _service()
    domain = ctx["domain"]
    open_row = _report(domain, production_order="111", operation_code="01")
    ack_row = _report(domain, production_order="222", operation_code="02")
    resolved = _report(domain, production_order="333", operation_code="05")
    domain.acknowledge(ack_row["id"], acknowledged_by="pcp-0")
    domain.resolve(resolved["id"], resolved_by="pcp-0")

    data = svc.list_inbox(_user(*FULL_PERMS), branch="01")

    ids = [item["id"] for item in data["items"]]
    assert open_row["id"] in ids
    assert ack_row["id"] in ids
    assert resolved["id"] not in ids
    assert data["summary"] == {"total": 2, "open": 1, "acknowledged": 1}


def test_inbox_orders_open_first_oldest_first() -> None:
    svc, ctx = _service()
    domain = ctx["domain"]
    old_ack = _report(domain, production_order="111", operation_code="01")
    old_open = _report(domain, production_order="333", operation_code="05")
    new_open = _report(domain, production_order="222", operation_code="02")
    domain.acknowledge(old_ack["id"], acknowledged_by="pcp-0")

    data = svc.list_inbox(_user(*FULL_PERMS), branch="01")

    statuses = [item["status"] for item in data["items"]]
    assert statuses[0] == "open"
    assert statuses[-1] == "acknowledged"
    # dentro de open, o mais antigo primeiro
    open_ids = [
        item["id"] for item in data["items"] if item["status"] == "open"
    ]
    assert open_ids == [old_open["id"], new_open["id"]]


def test_inbox_is_not_limited_by_reported_work_center() -> None:
    """Transferência de CT: feedback criado no CT-63 continua na inbox da filial."""
    svc, ctx = _service()
    row = _report(ctx["domain"], reported_work_center="CT-63")

    data = svc.list_inbox(_user(*FULL_PERMS), branch="01")

    assert data["items"][0]["id"] == row["id"]
    assert data["items"][0]["reportedWorkCenter"] == "CT-63"


def test_inbox_rejects_user_without_branch_access() -> None:
    svc, _ = _service()
    user = _user(
        "production-control.access",
        "production-control.machine-load.view",
        "production-control.view.filial-02",  # sem filial-01
    )
    with pytest.raises(BranchAccessDenied):
        svc.list_inbox(user, branch="01")


def test_inbox_rejects_user_without_machine_load_view() -> None:
    svc, _ = _service()
    user = _user(
        "production-control.access",
        "production-control.view.filial-01",
    )
    with pytest.raises(PermissionError):
        svc.list_inbox(user, branch="01")


def test_inbox_dto_carries_pcp_context() -> None:
    svc, ctx = _service()
    row = _report(ctx["domain"])
    item = svc.list_inbox(_user(*FULL_PERMS), branch="01")["items"][0]

    assert item["id"] == row["id"]
    assert item["branch"] == "01"
    assert item["productionOrder"] == "24640401002"
    assert item["operationCode"] == "03"
    assert item["operatorCode"] == "001234"
    assert item["operatorName"] == "Maria Silva"
    assert item["productCode"] == "TR-1234"
    assert item["paProductCode"] == "PA-5678"
    assert item["dueDate"] == "2026-10-08"
    # nada interno vaza
    assert "bench_session_id" not in item
    assert "benchSessionId" not in item


# --- acknowledge ----------------------------------------------------------------


def test_acknowledge_open_feedback() -> None:
    svc, ctx = _service()
    row = _report(ctx["domain"])

    item = svc.acknowledge(_user(*FULL_PERMS, user_id="ana.pcp"), feedback_id=row["id"])

    assert item["status"] == "acknowledged"
    assert item["acknowledgedBy"] == "ana.pcp"
    assert item["acknowledgedAt"]


def test_acknowledge_authorship_comes_from_jwt() -> None:
    """Não existe parâmetro de autoria: só o usuário autenticado decide."""
    svc, ctx = _service()
    row = _report(ctx["domain"])

    svc.acknowledge(_user(*FULL_PERMS, user_id="jwt-user"), feedback_id=row["id"])
    stored = ctx["repo"].get(row["id"])
    assert stored["acknowledged_by"] == "jwt-user"


def test_acknowledge_is_idempotent_and_keeps_first_author() -> None:
    """Analista B repete acknowledge — a autoria do A não é sobrescrita."""
    svc, ctx = _service()
    row = _report(ctx["domain"])
    svc.acknowledge(_user(*FULL_PERMS, user_id="ana"), feedback_id=row["id"])

    again = svc.acknowledge(
        _user(*FULL_PERMS, user_id="beatriz"), feedback_id=row["id"]
    )

    assert again["status"] == "acknowledged"
    assert again["acknowledgedBy"] == "ana"


def test_acknowledge_requires_branch_of_the_record() -> None:
    """Sem acesso à filial 02, o UUID correto não abre a tratativa."""
    svc, ctx = _service()
    row = _report(ctx["domain"], branch="02")
    user = _user(
        "production-control.access",
        "production-control.machine-load.view",
        "production-control.view.filial-01",  # sem filial-02
    )
    with pytest.raises(BranchAccessDenied):
        svc.acknowledge(user, feedback_id=row["id"])
    assert ctx["repo"].get(row["id"])["status"] == "open"


def test_acknowledge_unknown_id_raises_not_found() -> None:
    svc, _ = _service()
    with pytest.raises(OperatorFeedbackNotFound):
        svc.acknowledge(_user(*FULL_PERMS), feedback_id=str(uuid.uuid4()))


def test_acknowledge_resolved_is_state_conflict() -> None:
    svc, ctx = _service()
    row = _report(ctx["domain"])
    svc.resolve(_user(*FULL_PERMS), feedback_id=row["id"])

    with pytest.raises(OperatorFeedbackStateError):
        svc.acknowledge(_user(*FULL_PERMS), feedback_id=row["id"])


# --- resolve --------------------------------------------------------------------


def test_resolve_open_feedback() -> None:
    svc, ctx = _service()
    row = _report(ctx["domain"])

    item = svc.resolve(
        _user(*FULL_PERMS, user_id="ana.pcp"),
        feedback_id=row["id"],
        resolution_note="Material disponibilizado.",
    )

    assert item["status"] == "resolved"
    assert item["resolvedBy"] == "ana.pcp"
    assert item["resolutionNote"] == "Material disponibilizado."
    assert item["resolvedAt"]


def test_resolve_acknowledged_feedback() -> None:
    svc, ctx = _service()
    row = _report(ctx["domain"])
    svc.acknowledge(_user(*FULL_PERMS), feedback_id=row["id"])

    item = svc.resolve(_user(*FULL_PERMS), feedback_id=row["id"])

    assert item["status"] == "resolved"
    assert item["acknowledgedBy"]  # autoria do acknowledge preservada


def test_resolve_removes_from_active_inbox() -> None:
    svc, ctx = _service()
    row = _report(ctx["domain"])
    svc.resolve(_user(*FULL_PERMS), feedback_id=row["id"])

    data = svc.list_inbox(_user(*FULL_PERMS), branch="01")
    assert data["summary"]["total"] == 0


def test_resolve_note_is_optional_and_limited() -> None:
    svc, ctx = _service()
    row = _report(ctx["domain"])
    item = svc.resolve(_user(*FULL_PERMS), feedback_id=row["id"])
    assert item["resolutionNote"] is None

    row2 = _report(ctx["domain"], production_order="999", operation_code="07")
    with pytest.raises(ValueError):
        svc.resolve(
            _user(*FULL_PERMS), feedback_id=row2["id"], resolution_note="x" * 501
        )


def test_resolve_authorship_comes_from_jwt() -> None:
    svc, ctx = _service()
    row = _report(ctx["domain"])
    svc.resolve(_user(*FULL_PERMS, user_id="jwt-resolver"), feedback_id=row["id"])
    assert ctx["repo"].get(row["id"])["resolved_by"] == "jwt-resolver"


def test_resolve_requires_branch_of_the_record() -> None:
    svc, ctx = _service()
    row = _report(ctx["domain"], branch="02")
    user = _user(
        "production-control.access",
        "production-control.machine-load.view",
        "production-control.view.filial-01",
    )
    with pytest.raises(BranchAccessDenied):
        svc.resolve(user, feedback_id=row["id"])
    assert ctx["repo"].get(row["id"])["status"] == "open"


# --- realtime -------------------------------------------------------------------


def test_acknowledge_emits_realtime_hint() -> None:
    spy = NotifySpy()
    svc, ctx = _service(notify=spy)
    row = _report(ctx["domain"])
    svc.acknowledge(_user(*FULL_PERMS), feedback_id=row["id"])

    assert len(spy.calls) == 1
    call = spy.calls[0]
    assert call["reason"] == "acknowledged"
    assert call["branch"] == "01"
    assert call["feedback"]["status"] == "acknowledged"


def test_resolve_emits_realtime_hint() -> None:
    spy = NotifySpy()
    svc, ctx = _service(notify=spy)
    row = _report(ctx["domain"])
    svc.resolve(_user(*FULL_PERMS), feedback_id=row["id"])

    assert spy.calls[0]["reason"] == "resolved"
    assert spy.calls[0]["feedback"]["status"] == "resolved"


def test_realtime_failure_does_not_rollback_persistence() -> None:
    svc, ctx = _service(notify=NotifySpy(fail=True))
    row = _report(ctx["domain"])

    item = svc.acknowledge(_user(*FULL_PERMS), feedback_id=row["id"])

    assert item["status"] == "acknowledged"
    assert ctx["repo"].get(row["id"])["status"] == "acknowledged"


def test_resolve_realtime_failure_keeps_resolution() -> None:
    svc, ctx = _service(notify=NotifySpy(fail=True))
    row = _report(ctx["domain"])
    svc.resolve(_user(*FULL_PERMS), feedback_id=row["id"])
    assert ctx["repo"].get(row["id"])["status"] == "resolved"


# --- nenhum acoplamento MES -------------------------------------------------------


def test_service_has_no_mes_dependencies() -> None:
    """O orquestrador PCP não recebe run service, Pulse, downtime ou fila —
    não há como ele pausar, parar ou classificar apontamento."""
    svc, _ = _service()
    assert not hasattr(svc, "_run_service")
    assert not hasattr(svc, "_machine_load")
    import inspect

    signature = inspect.signature(PcpOperatorFeedbackService.__init__)
    assert set(signature.parameters) == {
        "self", "branch_access", "feedbacks", "notify"
    }


# --- contrato HTTP ---------------------------------------------------------------


def _app(
    svc: PcpOperatorFeedbackService, user: Any
) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = user
        return await call_next(request)

    app.include_router(feedback_routes.router)
    feedback_routes.build_pcp_operator_feedback_service = (  # type: ignore[assignment]
        lambda: svc
    )
    return TestClient(app)


def _seed(svc_ctx: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    return _report(svc_ctx["domain"], **overrides)


def test_http_inbox_returns_envelope_and_summary() -> None:
    svc, ctx = _service()
    _seed(ctx)
    api = _app(svc, _user(*FULL_PERMS))

    resp = api.get("/operator-feedbacks", params={"branch": "01"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["summary"]["open"] == 1
    assert body["data"]["items"][0]["productionOrder"] == "24640401002"


def test_http_inbox_without_machine_load_view_is_403() -> None:
    svc, _ = _service()
    api = _app(
        svc,
        _user("production-control.access", "production-control.view.filial-01"),
    )
    resp = api.get("/operator-feedbacks", params={"branch": "01"})
    assert resp.status_code == 403


def test_http_inbox_invalid_branch_is_422() -> None:
    svc, _ = _service()
    api = _app(svc, _user(*FULL_PERMS))
    resp = api.get("/operator-feedbacks", params={"branch": "99"})
    assert resp.status_code == 422


def test_http_acknowledge_flow() -> None:
    svc, ctx = _service()
    row = _seed(ctx)
    api = _app(svc, _user(*FULL_PERMS, user_id="ana.pcp"))

    resp = api.post(f"/operator-feedbacks/{row['id']}/acknowledge")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "acknowledged"
    assert data["acknowledgedBy"] == "ana.pcp"


def test_http_resolve_with_note() -> None:
    svc, ctx = _service()
    row = _seed(ctx)
    api = _app(svc, _user(*FULL_PERMS))

    resp = api.post(
        f"/operator-feedbacks/{row['id']}/resolve",
        json={"resolutionNote": "Programação ajustada."},
    )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "resolved"
    assert data["resolutionNote"] == "Programação ajustada."


def test_http_resolve_without_body_is_ok() -> None:
    svc, ctx = _service()
    row = _seed(ctx)
    api = _app(svc, _user(*FULL_PERMS))
    resp = api.post(f"/operator-feedbacks/{row['id']}/resolve")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "resolved"


def test_http_acknowledge_other_branch_is_403() -> None:
    svc, ctx = _service()
    row = _seed(ctx, branch="02")
    api = _app(
        svc,
        _user(
            "production-control.access",
            "production-control.machine-load.view",
            "production-control.view.filial-01",
        ),
    )
    resp = api.post(f"/operator-feedbacks/{row['id']}/acknowledge")
    assert resp.status_code == 403


def test_http_unknown_feedback_is_404() -> None:
    svc, _ = _service()
    api = _app(svc, _user(*FULL_PERMS))
    resp = api.post(f"/operator-feedbacks/{uuid.uuid4()}/acknowledge")
    assert resp.status_code == 404


def test_http_acknowledge_resolved_conflict_is_409() -> None:
    svc, ctx = _service()
    row = _seed(ctx)
    api = _app(svc, _user(*FULL_PERMS))
    api.post(f"/operator-feedbacks/{row['id']}/resolve")

    resp = api.post(f"/operator-feedbacks/{row['id']}/acknowledge")
    assert resp.status_code == 409
    assert resp.json()["success"] is False


def test_http_resolution_note_over_limit_is_422() -> None:
    svc, ctx = _service()
    row = _seed(ctx)
    api = _app(svc, _user(*FULL_PERMS))
    resp = api.post(
        f"/operator-feedbacks/{row['id']}/resolve",
        json={"resolutionNote": "x" * 501},
    )
    assert resp.status_code == 422
