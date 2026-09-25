from __future__ import annotations

from datetime import datetime, timedelta, timezone

from production_control_app.application.services.production_run_service import ProductionRunService
from production_control_app.domain.errors import (
    BenchSessionRequired,
    ProductionRunConflict,
    PulseDeviceUnavailable,
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
    service = ProductionRunService(repository=FakeRepo(), pulse_gateway=FakePulse())
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
    service = ProductionRunService(repository=repo, pulse_gateway=pulse)
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
    service = ProductionRunService(repository=repo, pulse_gateway=pulse)
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


def test_second_start_conflicts():
    repo = FakeRepo()
    session = service_session(repo)
    device = {"deviceId": "dev-1", "counter": 0, "counterEpoch": 0, "online": True}
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    service = ProductionRunService(repository=repo, pulse_gateway=pulse)
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


def service_session(repo: FakeRepo) -> str:
    service = ProductionRunService(repository=repo, pulse_gateway=FakePulse(devices=[{"deviceId": "x"}]))
    created = service.create_bench_session(
        branch="01",
        work_center="CT01",
        operator_code="USR01",
        operator_name="Operador",
    )
    return created["sessionToken"]
