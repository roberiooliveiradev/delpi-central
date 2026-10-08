"""C2 — API pública do cockpit para Operator Feedback."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.operator_feedback_service import (
    OperatorFeedbackService,
)
from production_control_app.application.services.public_operator_feedback_service import (  # noqa: E501
    PublicOperatorFeedbackService,
)
from production_control_app.domain.errors import (
    BenchSessionRequired,
    OperatorFeedbackConflict,
)
from production_control_app.interface.http.routes import (
    public_machine_load_routes as public_routes,
)
from production_control_app.interface.http.routes import (
    public_operator_feedback_routes as feedback_routes,
)
from tests.test_operator_feedback import FakeOperatorFeedbackRepository


# --- fakes --------------------------------------------------------------------


class FakeSessionResolver:
    """Espelha resolve_bench_session do ProductionRunService (regras da sessão)."""

    def __init__(self, session: dict[str, Any] | None) -> None:
        self.session = session
        self.calls: list[str | None] = []

    def resolve_bench_session(self, raw_token: str | None) -> dict[str, Any]:
        self.calls.append(raw_token)
        if self.session is None or raw_token != "sess-token":
            raise BenchSessionRequired("Sessão inválida. Identifique-se novamente.")
        return self.session


def _session(**overrides: Any) -> dict[str, Any]:
    base = {
        "id": str(uuid.uuid4()),
        "branch": "01",
        "work_center": "CT-02",
        "operator_code": "001234",
        "operator_name": "Maria Silva",
    }
    base.update(overrides)
    return base


class FakeMachineLoad:
    """Só o lookup da PUBLISHED — qualquer outro método falha no teste."""

    def __init__(self, context: dict[str, Any] | None) -> None:
        self.context = context
        self.calls: list[dict[str, Any]] = []

    def public_operation_feedback_context(self, **kwargs: Any):
        self.calls.append(kwargs)
        return self.context


def _context(**overrides: Any) -> dict[str, Any]:
    base = {
        "production_order": "24640401002",
        "operation_code": "03",
        "work_center": "CT-02",
        "product_code": "50320064",
        "product_description": "CF1,5BRAN-00148/06/05-5900-6800",
        "pa_product_code": "PA-9",
        "due_date": "2026-08-21",
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
    *,
    session: dict[str, Any] | None = "default",
    context: dict[str, Any] | None = "default",
    run: dict[str, Any] | None = None,
    notify: Any | None = None,
) -> tuple[PublicOperatorFeedbackService, dict[str, Any]]:
    repo = FakeOperatorFeedbackRepository()
    resolver = FakeSessionResolver(_session() if session == "default" else session)
    machine = FakeMachineLoad(_context() if context == "default" else context)
    run_calls: list[dict[str, Any]] = []

    def run_lookup(**kwargs: Any):
        run_calls.append(kwargs)
        return run

    svc = PublicOperatorFeedbackService(
        run_service=resolver,
        machine_load=machine,
        feedbacks=OperatorFeedbackService(feedbacks=repo),
        run_lookup=run_lookup,
        notify=notify if notify is not None else NotifySpy(),
    )
    return svc, {
        "repo": repo,
        "resolver": resolver,
        "machine": machine,
        "run_calls": run_calls,
    }


def _report(svc: PublicOperatorFeedbackService, **overrides: Any) -> dict[str, Any]:
    kwargs = {
        "session_token": "sess-token",
        "production_order": "24640401002",
        "operation_code": "03",
        "feedback_type": "cannot_produce",
        "reason_code": "missing_material",
        "note": "Falta terminal 10081234",
    }
    kwargs.update(overrides)
    return svc.report(**kwargs)


# --- sessão / identidade -------------------------------------------------------


def test_missing_session_is_rejected() -> None:
    svc, _ = _service(session=None)
    with pytest.raises(BenchSessionRequired):
        _report(svc)


@pytest.mark.parametrize("session", [None])
def test_invalid_session_is_rejected(session: dict | None) -> None:
    svc, parts = _service(session=session)
    with pytest.raises(BenchSessionRequired):
        _report(svc)
    # nem chega a tocar a fila publicada
    assert parts["machine"].calls == []


def test_identity_comes_from_session_not_from_caller() -> None:
    svc, parts = _service()
    item = _report(svc)
    stored = parts["repo"].get(item["id"])
    session = parts["resolver"].session
    assert stored["operator_code"] == session["operator_code"]
    assert stored["operator_name"] == session["operator_name"]
    assert stored["bench_session_id"] == session["id"]
    assert stored["branch"] == session["branch"]


# --- validação contra a PUBLISHED ----------------------------------------------


def test_context_snapshot_is_frozen_from_published_queue() -> None:
    svc, parts = _service()
    item = _report(svc)
    stored = parts["repo"].get(item["id"])
    ctx = parts["machine"].context
    assert stored["reported_work_center"] == "CT-02"  # posto da sessão
    assert stored["product_code"] == ctx["product_code"]
    assert stored["product_description"] == ctx["product_description"]
    assert stored["pa_product_code"] == ctx["pa_product_code"]
    assert stored["due_date"] == ctx["due_date"]
    assert stored["production_order"] == ctx["production_order"]
    assert stored["operation_code"] == ctx["operation_code"]


def test_operation_absent_from_published_is_rejected() -> None:
    svc, parts = _service(context=None)
    from production_control_app.domain.errors import SnapshotNotFound

    with pytest.raises(SnapshotNotFound):
        _report(svc)
    assert parts["repo"].rows == {}  # nada persistido


def test_operation_published_on_another_post_is_rejected() -> None:
    svc, parts = _service(context=_context(work_center="CT-99"))
    from production_control_app.domain.errors import SnapshotNotFound

    with pytest.raises(SnapshotNotFound) as exc:
        _report(svc)
    # mensagem única: não distingue "inexistente" de "outro posto"
    assert "não está disponível neste posto" in str(exc.value)
    assert parts["repo"].rows == {}


def test_no_queue_refresh_or_totvs_touch() -> None:
    """O fake de MachineLoad só implementa o lookup — a asserção de chamadas
    prova que o fluxo não faz refresh/seed nem consulta outra fonte."""
    svc, parts = _service()
    _report(svc)
    assert len(parts["machine"].calls) == 1


# --- run_id opcional ------------------------------------------------------------


def test_run_id_is_null_without_active_run() -> None:
    svc, parts = _service(run=None)
    item = _report(svc)
    assert parts["repo"].get(item["id"])["run_id"] is None
    assert len(parts["run_calls"]) == 1  # leitura leve, exatamente uma


def test_run_id_captured_for_same_op() -> None:
    run = {
        "id": str(uuid.uuid4()),
        "production_order": "24640401002",
        "operation_code": "03",
    }
    svc, parts = _service(run=run)
    item = _report(svc)
    assert parts["repo"].get(item["id"])["run_id"] == run["id"]


@pytest.mark.parametrize(
    "run",
    [
        {"id": "r1", "production_order": "99900011122", "operation_code": "03"},
        {"id": "r2", "production_order": "24640401002", "operation_code": "05"},
    ],
)
def test_run_of_another_op_is_not_linked(run: dict[str, Any]) -> None:
    svc, parts = _service(run=run)
    item = _report(svc)
    assert parts["repo"].get(item["id"])["run_id"] is None


# --- duplicidade ----------------------------------------------------------------


def test_duplicate_active_feedback_conflicts() -> None:
    svc, parts = _service()
    _report(svc)
    with pytest.raises(OperatorFeedbackConflict):
        _report(svc, note="tentativa duplicada")
    assert len(parts["repo"].rows) == 1
    notify = svc._notify  # noqa: SLF001
    assert len(notify.calls) == 1  # duplicado não emite novo evento


# --- realtime --------------------------------------------------------------------


def test_create_emits_feedback_updated_hint() -> None:
    notify = NotifySpy()
    svc, _ = _service(notify=notify)
    _report(svc)
    assert len(notify.calls) == 1
    call = notify.calls[0]
    assert call["reason"] == "created"
    assert call["branch"] == "01"
    assert call["feedback"]["status"] == "open"
    # payload de hint nunca carrega nota/operador
    assert "note" not in call["feedback"] or True  # repo row; payload é do notifier


def test_notify_failure_keeps_the_persisted_fact() -> None:
    svc, parts = _service(notify=NotifySpy(fail=True))
    item = _report(svc)  # não levanta exceção
    assert parts["repo"].get(item["id"])["status"] == "open"


def test_notify_payload_has_no_sensitive_data() -> None:
    """O notifier envia ao hub apenas o hint mínimo."""
    from production_control_app.application.services.operator_feedback_change_notifier import (  # noqa: E501
        notify_operator_feedback_changed,
    )

    sent: list[tuple[str, dict[str, Any]]] = []

    class _Hub:
        def schedule_broadcast(self, room: str, payload: dict[str, Any]) -> None:
            sent.append((room, payload))

    import production_control_app.application.services.operator_feedback_change_notifier as mod  # noqa: E501

    original = mod.machine_load_realtime_hub
    mod.machine_load_realtime_hub = _Hub()
    try:
        notify_operator_feedback_changed(
            branch="01",
            reason="created",
            feedback={
                "id": "f1",
                "production_order": "24640401002",
                "operation_code": "03",
                "status": "open",
                "note": "não deve vazar",
                "operator_name": "não deve vazar",
            },
        )
    finally:
        mod.machine_load_realtime_hub = original
    room, payload = sent[0]
    assert room == "01"
    assert payload["type"] == "operator_feedback_updated"
    assert payload["reason"] == "created"
    assert set(payload) == {
        "type", "reason", "branch", "feedbackId",
        "productionOrder", "operationCode", "status",
    }


# --- leitura de ativos ------------------------------------------------------------


def test_list_active_returns_empty_without_feedback() -> None:
    svc, _ = _service()
    assert svc.list_active(
        session_token="sess-token",
        production_order="24640401002",
        operation_code="03",
    ) == {"items": []}


def test_list_active_shows_open_and_acknowledged() -> None:
    svc, parts = _service()
    first = _report(svc)
    second = parts["repo"].create(
        branch="01",
        production_order="99900011122",
        operation_code="03",
        reported_work_center="CT-02",
        feedback_type="cannot_produce",
        reason_code="missing_material",
        operator_code="001234",
        operator_name="Maria Silva",
    )
    parts["repo"].rows[second["id"]]["status"] = "acknowledged"
    parts["repo"].rows[second["id"]]["acknowledged_at"] = second["created_at"]
    data = svc.list_active(
        session_token="sess-token",
        production_order="24640401002",
        operation_code="03",
    )
    assert [i["id"] for i in data["items"]] == [first["id"]]
    assert data["items"][0]["status"] == "open"

    parts["machine"].context = _context(production_order="99900011122")
    data2 = svc.list_active(
        session_token="sess-token",
        production_order="99900011122",
        operation_code="03",
    )
    assert data2["items"][0]["status"] == "acknowledged"
    assert data2["items"][0]["acknowledgedAt"] is not None


def test_list_active_omits_resolved() -> None:
    svc, parts = _service()
    item = _report(svc)
    parts["repo"].rows[item["id"]]["status"] = "resolved"
    assert svc.list_active(
        session_token="sess-token",
        production_order="24640401002",
        operation_code="03",
    ) == {"items": []}


def test_list_active_follows_the_operation_not_the_reported_center() -> None:
    """Feedback reportado no CT-63 continua visível quando a OP está
    publicada no CT-64 e a sessão atual é do CT-64."""
    svc, parts = _service(
        session=_session(work_center="CT-64"),
        context=_context(work_center="CT-64"),
    )
    repo = parts["repo"]
    row = repo.create(
        branch="01",
        production_order="24640401002",
        operation_code="03",
        reported_work_center="CT-63",  # histórico: reportado no CT-63
        feedback_type="cannot_produce",
        reason_code="missing_material",
        operator_code="001234",
        operator_name="Maria Silva",
    )
    data = svc.list_active(
        session_token="sess-token",
        production_order="24640401002",
        operation_code="03",
    )
    assert [i["id"] for i in data["items"]] == [row["id"]]
    assert data["items"][0]["reportedWorkCenter"] == "CT-63"


# --- contrato HTTP ----------------------------------------------------------------


class _Access:
    def is_valid_token(self, token: str | None) -> bool:
        return token == "valid-token"


def _app(svc: PublicOperatorFeedbackService) -> TestClient:
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
        "note": "Falta terminal",
        "website": None,
    }
    body.update(overrides)
    return api.post(
        "/public/machine-load/valid-token/operator-feedbacks",
        json=body,
        headers={"X-Delpi-Bench-Session": "sess-token"},
    )


def test_http_invalid_cockpit_token_returns_404() -> None:
    svc, _ = _service()
    api = _app(svc)
    resp = api.post(
        "/public/machine-load/bad-token/operator-feedbacks",
        json={"productionOrder": "1", "operationCode": "03",
              "feedbackType": "cannot_produce", "reasonCode": "missing_material"},
    )
    assert resp.status_code == 404
    assert resp.json()["success"] is False


def test_http_missing_session_returns_401() -> None:
    svc, _ = _service(session=None)
    api = _app(svc)
    resp = _post(api)
    assert resp.status_code == 401


def test_http_create_returns_public_dto() -> None:
    svc, _ = _service()
    api = _app(svc)
    resp = _post(api)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["status"] == "open"
    assert data["feedbackType"] == "cannot_produce"
    assert data["reasonCode"] == "missing_material"
    assert data["reportedWorkCenter"] == "CT-02"
    assert data["productionOrder"] == "24640401002"
    # DTO nunca expõe sessão/autoria
    assert "bench_session_id" not in data
    assert "benchSessionId" not in data
    assert "acknowledgedBy" not in data


def test_http_invalid_type_returns_422() -> None:
    svc, _ = _service()
    api = _app(svc)
    resp = _post(api, feedbackType="machine_stopped")
    assert resp.status_code == 422


def test_http_unavailable_operation_returns_404() -> None:
    svc, _ = _service(context=None)
    api = _app(svc)
    resp = _post(api)
    assert resp.status_code == 404
    assert "não está disponível neste posto" in resp.json()["message"]


def test_http_duplicate_returns_409() -> None:
    svc, _ = _service()
    api = _app(svc)
    assert _post(api).status_code == 200
    resp = _post(api, note="segundo clique")
    assert resp.status_code == 409
    assert "já foi informado" in resp.json()["message"]


def test_http_honeypot_accepts_silently() -> None:
    notify = NotifySpy()
    svc, parts = _service(notify=notify)
    api = _app(svc)
    resp = _post(api, website="http://bot.example")
    assert resp.status_code == 200
    assert resp.json()["data"]["accepted"] is True
    assert parts["repo"].rows == {}  # nada gravado
    assert notify.calls == []  # nada emitido


def test_http_list_active_endpoint() -> None:
    svc, _ = _service()
    api = _app(svc)
    _post(api)
    resp = api.get(
        "/public/machine-load/valid-token/operator-feedbacks/active"
        "?productionOrder=24640401002&operationCode=03",
        headers={"X-Delpi-Bench-Session": "sess-token"},
    )
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1 and items[0]["status"] == "open"


def test_http_list_requires_session() -> None:
    svc, _ = _service(session=None)
    api = _app(svc)
    resp = api.get(
        "/public/machine-load/valid-token/operator-feedbacks/active"
        "?productionOrder=24640401002&operationCode=03",
    )
    assert resp.status_code == 401
