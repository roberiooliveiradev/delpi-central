from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from production_control_app.application.services.machine_load_realtime_hub import (
    machine_load_realtime_hub,
)
from production_control_app.application.services.mes_run_lifecycle_service import (
    MesRunLifecycleService,
)
from production_control_app.application.services.production_run_poller_service import (
    remaining_cycle_delay,
)
from production_control_app.application.services.production_run_service import ProductionRunService
from production_control_app.domain.errors import (
    BenchSessionRequired,
    DowntimeConflict,
    InvalidMesEvent,
    MesStateConflict,
    ProductionRunConflict,
    PulseDeviceUnavailable,
)
from production_control_app.infrastructure.gateways.production_pulse_gateway import (
    ProductionPulseGateway,
)
from production_control_app.infrastructure.persistence.postgres_production_run_repository import (
    hash_session_token,
)


class FakeRepo:
    def __init__(self) -> None:
        self.sessions: dict[str, dict] = {}
        self.runs: dict[str, dict] = {}
        self.segments: dict[str, list[dict]] = {}
        self._seq = 0

    def _id(self) -> str:
        self._seq += 1
        return f"id-{self._seq}"

    def create_bench_session(self, **kwargs):
        sid = self._id()
        token_hash = hash_session_token(kwargs["raw_token"])
        row = {
            "id": sid,
            "branch": kwargs["branch"],
            "work_center": kwargs["work_center"],
            "operator_code": kwargs["operator_code"],
            "operator_name": kwargs.get("operator_name"),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=12),
            "created_at": datetime.now(timezone.utc),
            "ended_at": None,
            "_token_hash": token_hash,
        }
        self.sessions[token_hash] = row
        return row

    def get_bench_session_by_token(self, raw_token: str):
        return self.sessions.get(hash_session_token(raw_token))

    def end_bench_session(self, session_id: str) -> None:
        for row in self.sessions.values():
            if row["id"] == session_id:
                row["ended_at"] = datetime.now(timezone.utc)

    def get_active_run(self, *, branch: str, work_center: str):
        for run in self.runs.values():
            if (
                run["branch"] == branch
                and run["work_center"] == work_center
                and run["status"] in {"running", "paused"}
            ):
                return dict(run)
        return None

    def get_run(self, run_id: str):
        run = self.runs.get(run_id)
        return dict(run) if run else None

    def create_run_with_segment(self, **kwargs):
        rid = self._id()
        run = {
            "id": rid,
            "branch": kwargs["branch"],
            "work_center": kwargs["work_center"],
            "production_order": kwargs["production_order"],
            "operation_code": kwargs["operation_code"],
            "device_id": kwargs["device_id"],
            "operator_code": kwargs["operator_code"],
            "operator_name": kwargs.get("operator_name"),
            "bench_session_id": kwargs.get("bench_session_id"),
            "status": "running",
            "started_at": datetime.now(timezone.utc),
            "ended_at": None,
            "pieces_total": 0,
            "planned_qty_snapshot": kwargs.get("planned_qty_snapshot"),
            "target_pieces_snapshot": kwargs.get("target_pieces_snapshot"),
        }
        seg = {
            "id": self._id(),
            "run_id": rid,
            "device_id": kwargs["device_id"],
            "anchor_counter": kwargs["anchor_counter"],
            "anchor_epoch": kwargs["anchor_epoch"],
            "started_at": datetime.now(timezone.utc),
            "ended_at": None,
            "pieces": 0,
            "end_reason": None,
        }
        self.runs[rid] = run
        self.segments[rid] = [seg]
        out = dict(run)
        out["open_segment"] = seg
        return out

    def get_open_segment(self, run_id: str):
        for seg in self.segments.get(run_id, []):
            if seg.get("ended_at") is None:
                return dict(seg)
        return None

    def list_segments(self, run_id: str):
        return [dict(s) for s in self.segments.get(run_id, [])]

    def update_run_pieces(self, run_id, *, pieces_total, open_segment_pieces):
        self.runs[run_id]["pieces_total"] = pieces_total
        for seg in self.segments[run_id]:
            if seg.get("ended_at") is None:
                seg["pieces"] = open_segment_pieces

    def close_segment_open_new(self, **kwargs):
        for seg in self.segments[kwargs["run_id"]]:
            if seg["id"] == kwargs["segment_id"]:
                seg["ended_at"] = datetime.now(timezone.utc)
                seg["pieces"] = kwargs["pieces"]
                seg["end_reason"] = kwargs["end_reason"]
        new_seg = {
            "id": self._id(),
            "run_id": kwargs["run_id"],
            "device_id": kwargs["device_id"],
            "anchor_counter": kwargs["anchor_counter"],
            "anchor_epoch": kwargs["anchor_epoch"],
            "started_at": datetime.now(timezone.utc),
            "ended_at": None,
            "pieces": 0,
            "end_reason": None,
        }
        self.segments[kwargs["run_id"]].append(new_seg)
        self.runs[kwargs["run_id"]]["pieces_total"] = kwargs["pieces_total"]
        return {"id": kwargs["run_id"], "pieces_total": kwargs["pieces_total"], "open_segment": new_seg}

    def set_run_status(self, run_id, **kwargs):
        run = self.runs[run_id]
        if kwargs.get("close_open_segment"):
            for seg in self.segments[run_id]:
                if seg.get("ended_at") is None:
                    seg["ended_at"] = datetime.now(timezone.utc)
                    seg["pieces"] = kwargs.get("open_segment_pieces", 0)
                    seg["end_reason"] = kwargs.get("end_reason")
        run["status"] = kwargs["status"]
        if kwargs.get("pieces_total") is not None:
            run["pieces_total"] = kwargs["pieces_total"]
        if kwargs["status"] in {"completed", "aborted"}:
            run["ended_at"] = datetime.now(timezone.utc)
        return dict(run)

    def reopen_segment_on_resume(self, **kwargs):
        self.runs[kwargs["run_id"]]["status"] = "running"
        seg = {
            "id": self._id(),
            "run_id": kwargs["run_id"],
            "device_id": kwargs["device_id"],
            "anchor_counter": kwargs["anchor_counter"],
            "anchor_epoch": kwargs["anchor_epoch"],
            "started_at": datetime.now(timezone.utc),
            "ended_at": None,
            "pieces": 0,
            "end_reason": None,
        }
        self.segments[kwargs["run_id"]].append(seg)
        return {"id": kwargs["run_id"], "status": "running", "open_segment": seg}

    def list_open_running_runs(self):
        return [dict(r) for r in self.runs.values() if r["status"] == "running"]

    @contextmanager
    def transaction(self):
        yield None

    def lock_run(self, run_id: str, *, conn=None):
        return self.get_run(run_id)


class FakeStateRepo:
    def __init__(self) -> None:
        self.events: list[dict] = []
        self._seq = 0

    def get_open(self, *, branch, work_center, conn=None):
        for e in self.events:
            if (
                e["branch"] == branch
                and e["work_center"] == work_center
                and e["ended_at"] is None
            ):
                return dict(e)
        return None

    def open_event(self, *, branch, work_center, state, source, run_id=None, started_at=None, conn=None):
        if self.get_open(branch=branch, work_center=work_center) is not None:
            raise MesStateConflict("Já existe um estado operacional aberto neste posto.")
        self._seq += 1
        ev = {
            "id": f"st-{self._seq}",
            "branch": branch,
            "work_center": work_center,
            "run_id": run_id,
            "state": state,
            "source": source,
            "started_at": started_at or datetime.now(timezone.utc),
            "ended_at": None,
            "created_at": datetime.now(timezone.utc),
        }
        self.events.append(ev)
        return dict(ev)

    def close_open(self, *, branch, work_center, ended_at=None, conn=None):
        for e in self.events:
            if (
                e["branch"] == branch
                and e["work_center"] == work_center
                and e["ended_at"] is None
            ):
                e["ended_at"] = ended_at or datetime.now(timezone.utc)
                return dict(e)
        return None

    def list_for_work_center(self, *, branch, work_center, limit=200):
        out = [e for e in self.events if e["branch"] == branch and e["work_center"] == work_center]
        return [dict(e) for e in sorted(out, key=lambda e: e["started_at"], reverse=True)]

    def list_for_run(self, run_id):
        out = [e for e in self.events if e["run_id"] == run_id]
        return [dict(e) for e in sorted(out, key=lambda e: e["started_at"])]


class FakeDowntimeRepo:
    def __init__(self) -> None:
        self.events: list[dict] = []
        self._seq = 0

    def get_open(self, *, branch, work_center, conn=None):
        for e in self.events:
            if (
                e["branch"] == branch
                and e["work_center"] == work_center
                and e["ended_at"] is None
            ):
                return dict(e)
        return None

    def get(self, downtime_id):
        for e in self.events:
            if e["id"] == downtime_id:
                return dict(e)
        return None

    def create(self, *, branch, work_center, source, run_id=None, state_event_id=None,
               production_order=None, operation_code=None, started_at=None, conn=None):
        if self.get_open(branch=branch, work_center=work_center) is not None:
            raise DowntimeConflict("Já existe uma parada aberta neste posto.")
        self._seq += 1
        ev = {
            "id": f"dt-{self._seq}",
            "branch": branch,
            "work_center": work_center,
            "run_id": run_id,
            "state_event_id": state_event_id,
            "production_order": production_order,
            "operation_code": operation_code,
            "started_at": started_at or datetime.now(timezone.utc),
            "ended_at": None,
            "reason_code": None,
            "planned": None,
            "counts_as_availability_loss": None,
            "source": source,
            "confirmed": False,
            "confirmed_at": None,
            "confirmed_by_type": None,
            "confirmed_by_ref": None,
            "note": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.events.append(ev)
        return dict(ev)

    def classify(self, downtime_id, *, reason_code, planned, counts_as_availability_loss,
                 note=None, confirmed_by_type=None, confirmed_by_ref=None, confirmed=True,
                 conn=None):
        from production_control_app.domain.errors import DowntimeNotFound

        for e in self.events:
            if e["id"] == downtime_id:
                e["reason_code"] = reason_code
                e["planned"] = planned
                e["counts_as_availability_loss"] = counts_as_availability_loss
                if note is not None:
                    e["note"] = note
                e["confirmed"] = confirmed
                e["confirmed_at"] = datetime.now(timezone.utc) if confirmed else None
                e["confirmed_by_type"] = confirmed_by_type
                e["confirmed_by_ref"] = confirmed_by_ref
                e["updated_at"] = datetime.now(timezone.utc)
                return dict(e)
        raise DowntimeNotFound("Parada nao encontrada.")

    def close_open(self, *, branch, work_center, ended_at=None, conn=None):
        for e in self.events:
            if (
                e["branch"] == branch
                and e["work_center"] == work_center
                and e["ended_at"] is None
            ):
                e["ended_at"] = ended_at or datetime.now(timezone.utc)
                return dict(e)
        return None

    def list_for_run(self, run_id):
        out = [e for e in self.events if e["run_id"] == run_id]
        return [dict(e) for e in sorted(out, key=lambda e: e["started_at"])]

    def list_for_work_center(self, *, branch, work_center, start=None, end=None, limit=200):
        out = [e for e in self.events if e["branch"] == branch and e["work_center"] == work_center]
        return [dict(e) for e in sorted(out, key=lambda e: e["started_at"], reverse=True)]


class FakeReasonRepo:
    def __init__(self) -> None:
        self.reasons: dict[str, dict] = {
            "raw_material": {
                "code": "raw_material",
                "label": "Falta de material",
                "category": "material",
                "default_planned": None,
                "default_counts_as_availability_loss": None,
                "requires_note": False,
                "active": True,
                "sort_order": 40,
            },
            "maintenance": {
                "code": "maintenance",
                "label": "Manutenção",
                "category": "maintenance",
                "default_planned": None,
                "default_counts_as_availability_loss": None,
                "requires_note": False,
                "active": True,
                "sort_order": 70,
            },
            "other": {
                "code": "other",
                "label": "Outro",
                "category": "other",
                "default_planned": None,
                "default_counts_as_availability_loss": None,
                "requires_note": True,
                "active": True,
                "sort_order": 990,
            },
            "obsolete": {
                "code": "obsolete",
                "label": "Obsoleto",
                "category": "other",
                "default_planned": None,
                "default_counts_as_availability_loss": None,
                "requires_note": False,
                "active": False,
                "sort_order": 999,
            },
        }

    def get(self, code: str):
        row = self.reasons.get(str(code).strip().lower())
        return dict(row) if row else None

    def list_active(self):
        return [
            dict(r)
            for r in sorted(self.reasons.values(), key=lambda r: (r["sort_order"], r["code"]))
            if r["active"]
        ]

    def set_active(self, code: str, *, active: bool):
        row = self.reasons.get(code)
        if row is None:
            return None
        row["active"] = active
        return dict(row)


def make_mes(reasons=None) -> tuple[MesRunLifecycleService, FakeStateRepo, FakeDowntimeRepo]:
    states = FakeStateRepo()
    downtimes = FakeDowntimeRepo()
    return (
        MesRunLifecycleService(states=states, downtimes=downtimes, reasons=reasons),
        states,
        downtimes,
    )


def make_service(repo: FakeRepo, pulse: "FakePulse", **kwargs) -> ProductionRunService:
    if "mes_lifecycle" not in kwargs:
        kwargs["mes_lifecycle"] = make_mes()[0]
    return ProductionRunService(repository=repo, pulse_gateway=pulse, **kwargs)


class FakePulse:
    def __init__(self, devices=None, device_by_id=None):
        self.devices = devices or []
        self.device_by_id = device_by_id or {}
        self.counter = 100
        self.epoch = 1

    def fetch_work_center_snapshot(self, **kwargs):
        return {"items": list(self.devices)}

    def fetch_device_snapshot(self, device_id: str):
        if device_id in self.device_by_id:
            return self.device_by_id[device_id]
        return {
            "deviceId": device_id,
            "counter": self.counter,
            "counterEpoch": self.epoch,
            "online": True,
            "status": "online",
        }


def test_start_run_requires_session():
    service = make_service(FakeRepo(), FakePulse())
    try:
        service.start_run(
            branch="01",
            work_center="CT01",
            production_order="OP1",
            operation_code="10",
            session_token=None,
        )
        assert False
    except BenchSessionRequired:
        pass


def test_start_run_requires_exactly_one_device():
    repo = FakeRepo()
    session = service_session(repo)
    pulse = FakePulse(devices=[])
    service = make_service(repo, pulse)
    try:
        service.start_run(
            branch="01",
            work_center="CT01",
            production_order="OP1",
            operation_code="10",
            session_token=session,
        )
        assert False
    except PulseDeviceUnavailable:
        pass


def test_start_and_count_pieces():
    repo = FakeRepo()
    session = service_session(repo)
    device = {
        "deviceId": "dev-1",
        "counter": 100,
        "counterEpoch": 1,
        "online": True,
        "name": "Pad",
    }
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    service = make_service(repo, pulse)
    started = service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    assert started["status"] == "running"
    assert started["piecesTotal"] == 0

    pulse.device_by_id["dev-1"] = {**device, "counter": 130}
    active = service.get_active(branch="01", work_center="CT01")
    assert active is not None
    assert active["piecesTotal"] == 30
    assert active["countedPieces"] == 30


def test_run_target_is_frozen_from_queue_and_survives_pause_resume():
    repo = FakeRepo()
    session = service_session(repo)
    device = {"deviceId": "dev-1", "counter": 100, "counterEpoch": 1, "online": True}
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    operation = {
        "operation_pending_qty": 0.5,
        "planned_qty": 1.0,
        "unit": "MI",
        "pieces_conversion_factor": 1000,
    }
    mes, _, downtimes = make_mes()
    service = make_service(
        repo,
        pulse,
        queue_lookup=lambda **_kwargs: dict(operation),
        mes_lifecycle=mes,
    )

    started = service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    assert started["plannedQty"] == 0.5
    assert started["targetPieces"] == 500
    assert started["remainingPieces"] == 500
    assert started["progressPercent"] == 0
    assert started["targetReached"] is False

    pulse.device_by_id["dev-1"] = {**device, "counter": 350}
    halfway = service.get_active(branch="01", work_center="CT01")
    assert halfway["piecesTotal"] == 250
    assert halfway["remainingPieces"] == 250
    assert halfway["progressPercent"] == 50
    assert halfway["targetReached"] is False

    pulse.device_by_id["dev-1"] = {**device, "counter": 600}
    reached = service.get_active(branch="01", work_center="CT01")
    assert reached["piecesTotal"] == 500
    assert reached["remainingPieces"] == 0
    assert reached["targetReached"] is True

    pulse.device_by_id["dev-1"] = {**device, "counter": 620}
    exceeded = service.get_active(branch="01", work_center="CT01")
    assert exceeded["piecesTotal"] == 520
    assert exceeded["progressPercent"] == 104
    assert exceeded["overproductionPieces"] == 20

    pulse.device_by_id["dev-1"] = {**device, "counter": 345}
    decreased = service.get_active(branch="01", work_center="CT01")
    assert decreased["piecesTotal"] == 245
    assert decreased["progressPercent"] == 49

    operation["operation_pending_qty"] = 0.2
    paused = service.pause_run(started["id"], session_token=session)
    assert paused["targetPieces"] == 500
    for e in downtimes.events:
        if e["ended_at"] is None:
            e["reason_code"] = "other"
            e["confirmed"] = True
    resumed = service.resume_run(started["id"], session_token=session)
    assert resumed["targetPieces"] == 500
    assert repo.runs[started["id"]]["target_pieces_snapshot"] == 500


def test_run_target_uses_header_balance_only_for_legacy_queue_snapshot():
    repo = FakeRepo()
    session = service_session(repo)
    device = {"deviceId": "dev-1", "counter": 100, "counterEpoch": 1, "online": True}
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    service = make_service(
        repo,
        pulse,
        queue_lookup=lambda **_kwargs: {
            "planned_qty": 1.0,
            "pending_qty": 0.25,
            "unit": "MI",
            "pieces_conversion_factor": 1000,
        },
    )

    started = service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )

    assert started["plannedQty"] == 0.25
    assert started["targetPieces"] == 250


def test_run_target_stays_unknown_when_unit_has_no_piece_factor():
    repo = FakeRepo()
    session = service_session(repo)
    device = {"deviceId": "dev-1", "counter": 100, "counterEpoch": 1, "online": True}
    service = make_service(
        repo,
        FakePulse(devices=[device], device_by_id={"dev-1": device}),
        queue_lookup=lambda **_kwargs: {
            "operation_pending_qty": 0.5,
            "unit": "KG",
            "pieces_conversion_factor": None,
        },
    )

    started = service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )

    assert started["plannedQty"] == 0.5
    assert started["targetPieces"] is None


def test_legacy_run_without_target_has_no_progress():
    repo = FakeRepo()
    session = service_session(repo)
    device = {"deviceId": "dev-1", "counter": 100, "counterEpoch": 1, "online": True}
    service = make_service(
        repo,
        FakePulse(devices=[device], device_by_id={"dev-1": device}),
    )
    payload = service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    assert payload["targetPieces"] is None
    assert payload["remainingPieces"] is None
    assert payload["progressPercent"] is None
    assert payload["targetReached"] is False


def test_tick_emits_absolute_minimal_run_snapshot(monkeypatch: pytest.MonkeyPatch):
    repo = FakeRepo()
    session = service_session(repo)
    device = {"deviceId": "dev-1", "counter": 100, "counterEpoch": 1, "online": True}
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    service = make_service(repo, pulse)
    started = service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    messages = []
    monkeypatch.setattr(
        machine_load_realtime_hub,
        "schedule_broadcast",
        lambda room, message: messages.append((room, dict(message))),
    )

    pulse.device_by_id["dev-1"] = {**device, "counter": 142}
    assert service.tick_running_runs() == 1
    assert messages == [
        (
            "01:CT01",
            {
                "type": "production_run_updated",
                "reason": "pieces_updated",
                "branch": "01",
                "workCenter": "CT01",
                "runId": started["id"],
                "piecesTotal": 42,
            },
        ),
        (
            "01",
            {
                "type": "production_run_updated",
                "reason": "pieces_updated",
                "branch": "01",
                "workCenter": "CT01",
                "runId": started["id"],
                "piecesTotal": 42,
            },
        ),
    ]

    messages.clear()
    pulse.device_by_id["dev-1"] = {**device, "counter": 130}
    assert service.tick_running_runs() == 1
    assert [message["piecesTotal"] for _, message in messages] == [30, 30]

    messages.clear()
    assert service.tick_running_runs() == 0
    assert messages == []


def test_second_start_conflicts():
    repo = FakeRepo()
    session = service_session(repo)
    device = {"deviceId": "dev-1", "counter": 0, "counterEpoch": 0, "online": True}
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    service = make_service(repo, pulse)
    service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    try:
        service.start_run(
            branch="01",
            work_center="CT01",
            production_order="OP2",
            operation_code="10",
            session_token=session,
        )
        assert False
    except ProductionRunConflict:
        pass


def test_production_pulse_gateway_reuses_injected_client():
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": {"deviceId": "dev-1"}})

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        gateway = ProductionPulseGateway(base_url="http://pulse", client=client)
        gateway.fetch_device_snapshot("dev-1")
        gateway.fetch_device_snapshot("dev-1")
        gateway.close()
        assert not client.is_closed

    assert len(requests) == 2


def test_remaining_cycle_delay_compensates_processing_time():
    assert round(remaining_cycle_delay(500, 0.08), 3) == 0.42


def test_remaining_cycle_delay_does_not_wait_after_overrun():
    assert remaining_cycle_delay(500, 0.65) == 0.0


def service_session(repo: FakeRepo) -> str:
    service = make_service(repo, FakePulse(devices=[{"deviceId": "x"}]))
    created = service.create_bench_session(
        branch="01",
        work_center="CT01",
        operator_code="USR01",
        operator_name="Operador",
    )
    return created["sessionToken"]
