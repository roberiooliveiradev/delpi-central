"""E1 — Troca guiada de OP (handoff) no Production Control.

Cobre:
* resolver puro (CT, ordem publicada, saldos conhecido/zero/desconhecido);
* previa sem mutacao com razoes de bloqueio estruturadas;
* confirmacao atomica: run anterior completed + segmento handoff, novo run
  com ancora na mesma amostra Pulse, fatos MES na mesma fronteira,
  auditoria e registro idempotente;
* idempotencia: replay devolve resposta original; mesmo requestId com
  payload diferente e conflito;
* concorrencia: poller entre pre-leitura e lock, run ja encerrado;
* rollback integral em falhas de count event, estado MES, auditoria,
  insert do novo run e insert idempotente;
* negativos: sem proxima, saiu da fila, saldo desconhecido, fila mudou,
  device trocado/indisponivel, epoch divergente, sessao errada.
"""

from __future__ import annotations

import copy
import uuid
from contextlib import contextmanager
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.domain.errors import (
    BenchSessionRequired,
    DowntimeClassificationRequired,
    ProductionRunHandoffConflict,
    ProductionRunNotFound,
    PulseDeviceUnavailable,
)
from production_control_app.domain.services.machine_load_handoff import (
    HandoffNextResolution,
    operation_balance_state,
    resolve_handoff_next,
)
from production_control_app.interface.http.routes import (
    public_machine_load_routes as public_routes,
)

from tests.test_production_run_service import (
    FakePulse,
    FakeRepo,
    make_mes,
    make_service,
    service_session,
)

DEV = {
    "deviceId": "dev-1",
    "name": "Contador CT01",
    "counter": 100,
    "counterEpoch": 1,
    "online": True,
    "status": "online",
}


def _op(
    production_order: str,
    operation_code: str,
    *,
    work_center: str = "CT01",
    pending: float | None = 50.0,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "production_order": production_order,
        "operation_code": operation_code,
        "work_center": work_center,
        "product_code": "PA-1",
        "product_description": "Produto",
        "operation_description": "Operacao",
    }
    if pending is None:
        item["operation_pending_qty"] = None
        item["pending_qty"] = None
    else:
        item["operation_pending_qty"] = pending
    return item


class FakePublications:
    """Linha PUBLISHED travavel — o conteudo e inspecionado pelo resolver."""

    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row if row is not None else {"id": "pub-1"}
        self.locked_calls: list[str] = []

    def get_locked(self, *, branch: str, conn: Any = None):
        self.locked_calls.append(branch)
        return self.row


class FakeHandoffRequests:
    """Idempotencia duravel fake — espelha o repositorio V020."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.fail_next_insert = False

    def get(self, request_id: str, conn: Any = None):
        row = self.rows.get(str(request_id))
        return dict(row) if row else None

    def insert(self, *, request_id, branch, work_center, previous_run_id,
               new_run_id, request_hash, response, conn=None):
        if self.fail_next_insert:
            self.fail_next_insert = False
            raise RuntimeError("handoff_request_insert_failed")
        row = {
            "request_id": str(request_id),
            "branch": branch,
            "work_center": work_center,
            "previous_run_id": previous_run_id,
            "new_run_id": new_run_id,
            "request_hash": request_hash,
            "response": dict(response),
        }
        self.rows[str(request_id)] = row
        return dict(row)


class FakeResolver:
    """Callable do handoff_resolver — pre-tx e re-resolucao travada podem
    divergir para simular a fila mudando entre previa e confirmacao."""

    def __init__(self, *resolutions: HandoffNextResolution) -> None:
        self.resolutions = list(resolutions)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.resolutions) > 1:
            return self.resolutions.pop(0)
        return self.resolutions[0]


class FakeAudit:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.fail_next = False
        self._seq = 0

    def append(self, **kwargs):
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("audit_insert_failed")
        self._seq += 1
        row = {"id": self._seq, **kwargs}
        self.rows.append(row)
        return dict(row)


def _ok_resolution(target, **kw) -> HandoffNextResolution:
    if target is None:
        return HandoffNextResolution(status="no_next_operation", **kw)
    return HandoffNextResolution(
        status="ok",
        target=target,
        queue_size=kw.get("queue_size", 2),
        current_position=kw.get("current_position", 1),
        target_position=kw.get("target_position", 2),
        balance_state="open",
    )


def make_handoff_service(
    repo: FakeRepo,
    pulse: FakePulse,
    *resolutions: HandoffNextResolution,
    audit: FakeAudit | None = None,
    handoff_requests: FakeHandoffRequests | None = None,
    publications: FakePublications | None = None,
    mes=None,
    states=None,
    downtimes=None,
):
    if mes is None:
        mes, states, downtimes = make_mes()
    service = make_service(
        repo,
        pulse,
        mes_lifecycle=mes,
        audit=audit or FakeAudit(),
        handoff_resolver=FakeResolver(*resolutions),
        publications=publications or FakePublications(),
        handoff_requests=handoff_requests or FakeHandoffRequests(),
    )
    return service


def _start_run(repo: FakeRepo, pulse: FakePulse, service) -> tuple[str, dict]:
    token = service_session(repo)
    run = service.start_run(
        branch="01",
        work_center="CT01",
        production_order="001",
        operation_code="05",
        session_token=token,
    )
    return token, run


def _expect_next(target) -> dict[str, Any]:
    return {
        "productionOrder": str(target["production_order"]),
        "operationCode": str(target["operation_code"]),
    }


# --- resolver puro -----------------------------------------------------------


def test_resolver_picks_next_open_same_center():
    ops = [
        _op("001", "05"),
        _op("002", "10"),
        _op("003", "10", work_center="CT99"),
    ]
    res = resolve_handoff_next(
        ops, work_center="CT01", production_order="001", operation_code="05"
    )
    assert res.status == "ok"
    assert res.target["production_order"] == "002"
    assert res.target_position == 2


def test_resolver_ignores_same_op_in_other_center():
    ops = [
        _op("001", "05"),
        _op("001", "10", work_center="CT99"),
    ]
    res = resolve_handoff_next(
        ops, work_center="CT01", production_order="001", operation_code="05"
    )
    assert res.status == "no_next_operation"


def test_resolver_current_not_in_queue():
    res = resolve_handoff_next(
        [_op("002", "10")],
        work_center="CT01",
        production_order="999",
        operation_code="05",
    )
    assert res.status == "current_not_in_queue"


def test_resolver_skips_zero_balance():
    ops = [
        _op("001", "05"),
        _op("002", "10", pending=0.0),
        _op("003", "15", pending=12.0),
    ]
    res = resolve_handoff_next(
        ops, work_center="CT01", production_order="001", operation_code="05"
    )
    assert res.status == "ok"
    assert res.target["production_order"] == "003"


def test_resolver_unknown_balance_blocks():
    ops = [_op("001", "05"), _op("002", "10", pending=None)]
    res = resolve_handoff_next(
        ops, work_center="CT01", production_order="001", operation_code="05"
    )
    assert res.status == "balance_unknown"
    assert res.balance_state == "unknown"
    assert res.target["production_order"] == "002"


def test_operation_balance_state_semantics():
    assert operation_balance_state(_op("1", "1", pending=0.0)) == "closed"
    assert operation_balance_state(_op("1", "1", pending=3.0)) == "open"
    assert operation_balance_state(_op("1", "1", pending=None)) == "unknown"
    item = {"production_order": "1", "operation_code": "1", "pending_qty": 4.0}
    assert operation_balance_state(item) == "open"


# --- previa ------------------------------------------------------------------


def test_preview_available_with_next_operation():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    target = _op("002", "10")
    service = make_handoff_service(repo, pulse, _ok_resolution(target))
    token, run = _start_run(repo, pulse, service)

    preview = service.handoff_preview(
        run["id"], session_token=token, branch="01", work_center="CT01"
    )
    assert preview["available"] is True
    assert preview["block"] is None
    assert preview["currentRun"]["id"] == run["id"]
    assert preview["nextOperation"]["productionOrder"] == "002"
    assert repo.runs[run["id"]]["status"] == "running"


def test_preview_no_next_blocks():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(
        repo, pulse, HandoffNextResolution(status="no_next_operation")
    )
    token, run = _start_run(repo, pulse, service)

    preview = service.handoff_preview(
        run["id"], session_token=token, branch="01", work_center="CT01"
    )
    assert preview["available"] is False
    assert preview["block"]["code"] == "no_next_operation"
    assert preview["nextOperation"] is None


def test_preview_pending_classification_blocks():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)
    service.pause_run(run["id"], session_token=token)

    preview = service.handoff_preview(
        run["id"], session_token=token, branch="01", work_center="CT01"
    )
    assert preview["available"] is False
    assert preview["block"]["code"] == "pending_classification"


def test_preview_pulse_unavailable_blocks():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)
    pulse.devices[0]["online"] = False

    preview = service.handoff_preview(
        run["id"], session_token=token, branch="01", work_center="CT01"
    )
    assert preview["available"] is False
    assert preview["block"]["code"] == "pulse_unavailable"


def test_preview_completed_run_blocks():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)
    service.stop_run(run["id"], session_token=token)

    preview = service.handoff_preview(
        run["id"], session_token=token, branch="01", work_center="CT01"
    )
    assert preview["available"] is False
    assert preview["block"]["code"] == "run_not_active"


def test_preview_requires_session_and_scope():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)

    with pytest.raises(BenchSessionRequired):
        service.handoff_preview(
            run["id"], session_token="wrong", branch="01", work_center="CT01"
        )
    with pytest.raises(ProductionRunNotFound):
        service.handoff_preview(
            run["id"], session_token=token, branch="01", work_center="CT99"
        )


# --- confirmacao: caminho positivo -------------------------------------------


def test_confirm_handoff_completes_and_starts():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    audit = FakeAudit()
    requests = FakeHandoffRequests()
    target = _op("002", "10")
    service = make_handoff_service(
        repo,
        pulse,
        _ok_resolution(target),
        audit=audit,
        handoff_requests=requests,
    )
    token, run = _start_run(repo, pulse, service)
    pulse.devices[0]["counter"] = 140  # 40 golpes desde a ancora

    response = service.confirm_handoff(
        run["id"],
        request_id=str(uuid.uuid4()),
        branch="01",
        work_center="CT01",
        expected_next=_expect_next(target),
        session_token=token,
    )

    old = repo.runs[run["id"]]
    assert old["status"] == "completed"
    assert old["pieces_total"] == 40
    old_segments = repo.segments[run["id"]]
    assert old_segments[0]["end_reason"] == "handoff"
    assert old_segments[0]["pieces"] == 40
    assert old_segments[0]["ended_at"] is not None

    new_run = next(r for r in repo.runs.values() if r["id"] != run["id"])
    assert new_run["status"] == "running"
    assert new_run["production_order"] == "002"
    assert new_run["operation_code"] == "10"
    new_seg = repo.segments[new_run["id"]][0]
    # mesma amostra Pulse = ancora do novo run (sem peca fantasma)
    assert new_seg["anchor_counter"] == 140
    assert new_seg["anchor_epoch"] == 1

    events = repo.list_count_events(run["id"])
    assert len(events) == 1
    assert events[0]["pieces_total"] == 40
    assert repo.list_count_events(new_run["id"]) == []

    actions = [row["action"] for row in audit.rows]
    assert actions.count("run_handoff") == 1
    # run_started do setup (run anterior) + um único run_started do novo run
    started_new = [
        r for r in audit.rows
        if r["action"] == "run_started" and r["run_id"] == new_run["id"]
    ]
    assert len(started_new) == 1
    handoff_row = next(r for r in audit.rows if r["action"] == "run_handoff")
    assert handoff_row["details"]["boundaryCounter"] == 140
    assert handoff_row["details"]["newRunId"] == new_run["id"]

    assert response["replayed"] is False
    assert response["completedRun"]["piecesTotal"] == 40
    assert response["newRun"]["id"] == new_run["id"]
    assert response["boundary"] == {"counter": 140, "counterEpoch": 1}

    stored = requests.rows[response["requestId"]]
    assert stored["previous_run_id"] == run["id"]
    assert stored["new_run_id"] == new_run["id"]


def test_confirm_paused_run_with_classified_downtime():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    mes, states, downtimes = make_mes()
    target = _op("002", "10")
    service = make_handoff_service(
        repo,
        pulse,
        _ok_resolution(target),
        mes=mes,
        states=states,
        downtimes=downtimes,
    )
    token, run = _start_run(repo, pulse, service)
    service.pause_run(run["id"], session_token=token)
    open_dt = downtimes.get_open(branch="01", work_center="CT01")
    downtimes.classify(
        open_dt["id"], reason_code="setup", planned=False,
        counts_as_availability_loss=True,
    )

    response = service.confirm_handoff(
        run["id"],
        request_id=str(uuid.uuid4()),
        branch="01",
        work_center="CT01",
        expected_next=_expect_next(target),
        session_token=token,
    )
    assert repo.runs[run["id"]]["status"] == "completed"
    assert response["newRun"]["status"] == "running"
    assert downtimes.get_open(branch="01", work_center="CT01") is None


def test_confirm_unclassified_downtime_blocks():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    mes, states, downtimes = make_mes()
    service = make_handoff_service(
        repo,
        pulse,
        _ok_resolution(_op("002", "10")),
        mes=mes,
        states=states,
        downtimes=downtimes,
    )
    token, run = _start_run(repo, pulse, service)
    service.pause_run(run["id"], session_token=token)  # parada sem motivo

    with pytest.raises(DowntimeClassificationRequired):
        service.confirm_handoff(
            run["id"],
            request_id=str(uuid.uuid4()),
            branch="01",
            work_center="CT01",
            expected_next=_expect_next(_op("002", "10")),
            session_token=token,
        )
    assert repo.runs[run["id"]]["status"] == "paused"


# --- idempotencia / replay ----------------------------------------------------


def test_confirm_replay_returns_original_response():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    target = _op("002", "10")
    service = make_handoff_service(repo, pulse, _ok_resolution(target))
    token, run = _start_run(repo, pulse, service)
    request_id = str(uuid.uuid4())

    first = service.confirm_handoff(
        run["id"], request_id=request_id, branch="01", work_center="CT01",
        expected_next=_expect_next(target), session_token=token,
    )
    second = service.confirm_handoff(
        run["id"], request_id=request_id, branch="01", work_center="CT01",
        expected_next=_expect_next(target), session_token=token,
    )

    assert second["replayed"] is True
    assert second["requestId"] == request_id
    assert second["newRun"]["id"] == first["newRun"]["id"]
    assert len(repo.runs) == 2


def test_confirm_same_request_id_different_payload_conflicts():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    target = _op("002", "10")
    service = make_handoff_service(repo, pulse, _ok_resolution(target))
    token, run = _start_run(repo, pulse, service)
    request_id = str(uuid.uuid4())

    service.confirm_handoff(
        run["id"], request_id=request_id, branch="01", work_center="CT01",
        expected_next=_expect_next(target), session_token=token,
    )
    with pytest.raises(ProductionRunHandoffConflict) as err:
        service.confirm_handoff(
            run["id"], request_id=request_id, branch="01", work_center="CT01",
            expected_next={"productionOrder": "999", "operationCode": "99"},
            session_token=token,
        )
    assert err.value.code == "request_conflict"


def test_confirm_new_request_on_completed_run_blocked():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    target = _op("002", "10")
    service = make_handoff_service(repo, pulse, _ok_resolution(target))
    token, run = _start_run(repo, pulse, service)

    service.confirm_handoff(
        run["id"], request_id=str(uuid.uuid4()), branch="01",
        work_center="CT01", expected_next=_expect_next(target),
        session_token=token,
    )
    with pytest.raises(ProductionRunHandoffConflict) as err:
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01", expected_next=_expect_next(target),
            session_token=token,
        )
    assert err.value.code == "run_not_active"
    assert len(repo.runs) == 2


# --- negativos ----------------------------------------------------------------


def test_confirm_no_next_operation_conflicts():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(
        repo, pulse, HandoffNextResolution(status="no_next_operation")
    )
    token, run = _start_run(repo, pulse, service)

    with pytest.raises(ProductionRunHandoffConflict) as err:
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )
    assert err.value.code == "no_next_operation"
    assert repo.runs[run["id"]]["status"] == "running"


def test_confirm_current_not_in_queue_conflicts():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(
        repo, pulse, HandoffNextResolution(status="current_not_in_queue")
    )
    token, run = _start_run(repo, pulse, service)

    with pytest.raises(ProductionRunHandoffConflict) as err:
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )
    assert err.value.code == "current_not_in_queue"
    assert repo.runs[run["id"]]["status"] == "running"


def test_confirm_balance_unknown_conflicts():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(
        repo,
        pulse,
        HandoffNextResolution(
            status="balance_unknown", target=_op("002", "10", pending=None)
        ),
    )
    token, run = _start_run(repo, pulse, service)

    with pytest.raises(ProductionRunHandoffConflict) as err:
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )
    assert err.value.code == "balance_unknown"
    assert repo.runs[run["id"]]["status"] == "running"


def test_confirm_expected_next_mismatch_conflicts():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)

    with pytest.raises(ProductionRunHandoffConflict) as err:
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "777", "operationCode": "10"},
            session_token=token,
        )
    assert err.value.code == "queue_changed"
    assert repo.runs[run["id"]]["status"] == "running"


def test_confirm_queue_changed_between_preview_and_lock():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(
        repo, pulse, _ok_resolution(_op("002", "10")), _ok_resolution(_op("003", "20"))
    )
    token, run = _start_run(repo, pulse, service)

    with pytest.raises(ProductionRunHandoffConflict) as err:
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )
    assert err.value.code == "queue_changed"
    assert repo.runs[run["id"]]["status"] == "running"
    assert len(repo.runs) == 1


def test_confirm_device_mismatch_conflicts():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)
    pulse.devices[0] = dict(DEV, deviceId="dev-2")  # device trocou apos o Play

    with pytest.raises(ProductionRunHandoffConflict) as err:
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )
    assert err.value.code == "device_mismatch"
    assert repo.runs[run["id"]]["status"] == "running"


def test_confirm_epoch_mismatch_blocks_without_fabricating():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)
    pulse.devices[0]["counterEpoch"] = 2  # reset do contador

    with pytest.raises(ProductionRunHandoffConflict) as err:
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )
    assert err.value.code == "epoch_conflict"
    assert repo.runs[run["id"]]["status"] == "running"
    assert repo.count_events.get(run["id"], []) == []


def test_confirm_pulse_unavailable_blocks():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)
    pulse.devices = []  # nenhum device elegivel

    with pytest.raises(PulseDeviceUnavailable):
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )
    assert repo.runs[run["id"]]["status"] == "running"


def test_confirm_wrong_session_scope_rejected():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)
    other = service.create_bench_session(
        branch="01", work_center="CT99", registration="USR02"
    )

    with pytest.raises(BenchSessionRequired):
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=other["sessionToken"],
        )
    with pytest.raises(ValueError):
        service.confirm_handoff(
            run["id"], request_id="not-a-uuid", branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )


# --- concorrencia -------------------------------------------------------------


def test_confirm_poller_wrote_between_read_and_lock():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)
    pulse.devices[0]["counter"] = 140

    original_lock = repo.lock_run

    def _lock_then_poller(run_id, *, conn=None):
        locked = original_lock(run_id, conn=conn)
        if locked is not None:
            # tick do poller persistiu +55 entre a pre-leitura e o lock
            repo.runs[run_id]["pieces_total"] = 55
            locked["pieces_total"] = 55
        return locked

    repo.lock_run = _lock_then_poller
    try:
        response = service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )
    finally:
        repo.lock_run = original_lock

    # observacao pre-lock e stale -> total persistido pelo poller prevalece,
    # sem correction falsa e sem peca perdida
    assert repo.runs[run["id"]]["status"] == "completed"
    assert repo.runs[run["id"]]["pieces_total"] == 55
    assert response["completedRun"]["piecesTotal"] == 55


def test_confirm_second_distinct_request_after_first_fails():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    target = _op("002", "10")
    service = make_handoff_service(repo, pulse, _ok_resolution(target))
    token, run = _start_run(repo, pulse, service)

    service.confirm_handoff(
        run["id"], request_id=str(uuid.uuid4()), branch="01",
        work_center="CT01", expected_next=_expect_next(target),
        session_token=token,
    )
    with pytest.raises(ProductionRunHandoffConflict):
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01", expected_next=_expect_next(target),
            session_token=token,
        )
    assert len(repo.runs) == 2


# --- rollback integral --------------------------------------------------------


def test_confirm_count_event_failure_rolls_back():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    requests = FakeHandoffRequests()
    service = make_handoff_service(
        repo, pulse, _ok_resolution(_op("002", "10")),
        handoff_requests=requests,
    )
    token, run = _start_run(repo, pulse, service)
    pulse.devices[0]["counter"] = 140
    repo.fail_next_count_event = True

    with pytest.raises(RuntimeError, match="count_event_insert_failed"):
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )

    assert repo.runs[run["id"]]["status"] == "running"
    assert len(repo.runs) == 1
    assert requests.rows == {}


def test_confirm_new_run_insert_failure_rolls_back():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    audit = FakeAudit()
    requests = FakeHandoffRequests()
    mes, states, downtimes = make_mes()
    service = make_handoff_service(
        repo, pulse, _ok_resolution(_op("002", "10")),
        audit=audit, handoff_requests=requests,
        mes=mes, states=states, downtimes=downtimes,
    )
    token, run = _start_run(repo, pulse, service)
    pulse.devices[0]["counter"] = 140

    # falha DEPOIS do encerramento logico, antes do insert do novo run:
    # a transacao fake restaura todos os stores, como o Postgres faria.
    original_tx = repo.transaction
    stores = (requests.rows, audit.rows, states.events, downtimes.events)

    @contextmanager
    def _tx():
        backups = [
            copy.deepcopy(s) if isinstance(s, dict) else copy.deepcopy(list(s))
            for s in stores
        ]
        rb, sb, eb = (
            copy.deepcopy(repo.runs),
            copy.deepcopy(repo.segments),
            copy.deepcopy(repo.count_events),
        )
        try:
            yield None
        except Exception:
            repo.runs, repo.segments, repo.count_events = rb, sb, eb
            for store, backup in zip(stores, backups):
                if isinstance(store, dict):
                    store.clear()
                    store.update(backup)
                else:
                    del store[:]
                    store.extend(backup)
            raise

    repo.transaction = _tx
    calls = {"n": 0}

    def _failing_create(**kwargs):
        calls["n"] += 1
        raise RuntimeError("new_run_insert_failed")

    original_create = repo.create_run_with_segment
    repo.create_run_with_segment = _failing_create
    try:
        with pytest.raises(RuntimeError, match="new_run_insert_failed"):
            service.confirm_handoff(
                run["id"], request_id=str(uuid.uuid4()), branch="01",
                work_center="CT01",
                expected_next={"productionOrder": "002", "operationCode": "10"},
                session_token=token,
            )
    finally:
        repo.create_run_with_segment = original_create
        repo.transaction = original_tx

    assert calls["n"] == 1
    assert repo.runs[run["id"]]["status"] == "running"
    seg = repo.segments[run["id"]][0]
    assert seg["ended_at"] is None  # segmento reaberto pelo rollback
    assert len(repo.runs) == 1
    assert requests.rows == {}
    # rollback restaura ate a auditoria — so resta o run_started do setup
    assert [r["action"] for r in audit.rows] == ["run_started"]
    assert any(e["ended_at"] is None for e in states.events)


def test_confirm_mes_state_failure_rolls_back():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    mes, states, downtimes = make_mes()
    service = make_handoff_service(
        repo, pulse, _ok_resolution(_op("002", "10")),
        mes=mes, states=states, downtimes=downtimes,
    )
    token, run = _start_run(repo, pulse, service)

    original_close = states.close_open

    def _failing_close(**kwargs):
        raise RuntimeError("mes_state_close_failed")

    states.close_open = _failing_close
    try:
        with pytest.raises(RuntimeError, match="mes_state_close_failed"):
            service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
                work_center="CT01",
                expected_next={"productionOrder": "002", "operationCode": "10"},
                session_token=token,
            )
    finally:
        states.close_open = original_close

    assert repo.runs[run["id"]]["status"] == "running"
    assert len(repo.runs) == 1


def test_confirm_audit_failure_rolls_back():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    audit = FakeAudit()
    requests = FakeHandoffRequests()
    service = make_handoff_service(
        repo, pulse, _ok_resolution(_op("002", "10")),
        audit=audit, handoff_requests=requests,
    )
    token, run = _start_run(repo, pulse, service)
    audit.fail_next = True

    with pytest.raises(RuntimeError, match="audit_insert_failed"):
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )

    assert repo.runs[run["id"]]["status"] == "running"
    assert len(repo.runs) == 1
    assert requests.rows == {}


def test_confirm_idempotency_insert_failure_rolls_back():
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    requests = FakeHandoffRequests()
    service = make_handoff_service(
        repo, pulse, _ok_resolution(_op("002", "10")),
        handoff_requests=requests,
    )
    token, run = _start_run(repo, pulse, service)
    requests.fail_next_insert = True

    with pytest.raises(RuntimeError, match="handoff_request_insert_failed"):
        service.confirm_handoff(
            run["id"], request_id=str(uuid.uuid4()), branch="01",
            work_center="CT01",
            expected_next={"productionOrder": "002", "operationCode": "10"},
            session_token=token,
        )

    assert repo.runs[run["id"]]["status"] == "running"
    assert len(repo.runs) == 1
    assert requests.rows == {}


# --- contrato HTTP ------------------------------------------------------------


class _FakeCockpitAccess:
    def is_valid_token(self, token: str) -> bool:
        return token == "tok-valid"


def _wire(monkeypatch, service) -> TestClient:
    monkeypatch.setattr(
        public_routes, "build_production_run_service", lambda: service
    )
    monkeypatch.setattr(
        public_routes,
        "build_public_cockpit_access_service",
        lambda: _FakeCockpitAccess(),
    )
    app = FastAPI()
    app.include_router(public_routes.router)
    return TestClient(app)


def test_route_preview_ok(monkeypatch):
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)
    client = _wire(monkeypatch, service)

    resp = client.get(
        f"/public/machine-load/tok-valid/runs/{run['id']}/handoff-preview",
        params={"branch": "01", "workCenter": "CT01"},
        headers={"X-Delpi-Bench-Session": token},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["available"] is True
    assert data["nextOperation"]["productionOrder"] == "002"


def test_route_preview_invalid_token_and_session(monkeypatch):
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(repo, pulse, _ok_resolution(_op("002", "10")))
    token, run = _start_run(repo, pulse, service)
    client = _wire(monkeypatch, service)

    resp = client.get(
        f"/public/machine-load/bad/runs/{run['id']}/handoff-preview",
        params={"branch": "01", "workCenter": "CT01"},
        headers={"X-Delpi-Bench-Session": token},
    )
    assert resp.status_code == 404

    resp = client.get(
        f"/public/machine-load/tok-valid/runs/{run['id']}/handoff-preview",
        params={"branch": "01", "workCenter": "CT01"},
    )
    assert resp.status_code == 401


def test_route_confirm_ok_and_replay(monkeypatch):
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    target = _op("002", "10")
    service = make_handoff_service(repo, pulse, _ok_resolution(target))
    token, run = _start_run(repo, pulse, service)
    client = _wire(monkeypatch, service)
    request_id = str(uuid.uuid4())
    body = {
        "requestId": request_id,
        "branch": "01",
        "workCenter": "CT01",
        "expectedNext": {"productionOrder": "002", "operationCode": "10"},
    }

    resp = client.post(
        f"/public/machine-load/tok-valid/runs/{run['id']}/handoff",
        json=body,
        headers={"X-Delpi-Bench-Session": token},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["replayed"] is False
    assert data["requestId"] == request_id

    resp2 = client.post(
        f"/public/machine-load/tok-valid/runs/{run['id']}/handoff",
        json=body,
        headers={"X-Delpi-Bench-Session": token},
    )
    assert resp2.status_code == 200
    assert resp2.json()["data"]["replayed"] is True


def test_route_confirm_conflict_carries_code(monkeypatch):
    repo, pulse = FakeRepo(), FakePulse(devices=[dict(DEV)])
    service = make_handoff_service(
        repo, pulse, HandoffNextResolution(status="no_next_operation")
    )
    token, run = _start_run(repo, pulse, service)
    client = _wire(monkeypatch, service)

    resp = client.post(
        f"/public/machine-load/tok-valid/runs/{run['id']}/handoff",
        json={
            "requestId": str(uuid.uuid4()),
            "branch": "01",
            "workCenter": "CT01",
            "expectedNext": {"productionOrder": "002", "operationCode": "10"},
        },
        headers={"X-Delpi-Bench-Session": token},
    )
    assert resp.status_code == 409
    body = resp.json()
    assert body["success"] is False
    assert body["data"]["code"] == "no_next_operation"
