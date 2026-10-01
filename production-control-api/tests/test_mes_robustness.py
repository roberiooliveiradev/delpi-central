"""Etapa 05 — robustez: política de falha do Pulse, auditoria e integridade."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.application.services.mes_runtime_integrity_service import (
    inspect_runtime_integrity,
)
from production_control_app.domain.errors import (
    PulseDeviceUnavailable,
    PulseGatewayError,
)
from production_control_app.domain.services.pulse_snapshot import (
    classify_pulse_snapshot,
)

import os

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)

from tests.test_mes_run_lifecycle import _classify_open, _pg_device
from tests.test_production_run_service import (
    FakePulse,
    FakeRepo,
    make_service,
    service_session,
)


class FakeAudit:
    def __init__(self):
        self.records: list[dict] = []

    def append(self, **kwargs):
        self.records.append(kwargs)
        return {"id": f"au-{len(self.records)}", **kwargs}


class FailingPulse(FakePulse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fail = False

    def fetch_device_snapshot(self, device_id: str):
        if self.fail:
            raise PulseGatewayError("pulse offline")
        return super().fetch_device_snapshot(device_id)


def _start(service, session):
    return service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )


def _setup(audit=None):
    repo = FakeRepo()
    pulse = FailingPulse(
        devices=[{"deviceId": "dev-1", "counter": 0, "counterEpoch": 1, "online": True}]
    )
    service = make_service(repo, pulse, audit=audit)
    session = service.create_bench_session(
        branch="01",
        work_center="CT01",
        registration="USR01",
    )["sessionToken"]
    return service, repo, pulse, session


class TestPulseSnapshotClassification:
    def test_usable(self):
        assert classify_pulse_snapshot(
            {"deviceId": "d", "counter": 5, "counterEpoch": 1, "online": True}
        ) == "usable"

    def test_missing_device(self):
        assert classify_pulse_snapshot(None) == "unavailable"
        assert classify_pulse_snapshot({}) == "invalid"

    def test_invalid_counter(self):
        base = {"deviceId": "d", "counterEpoch": 1, "online": True}
        assert classify_pulse_snapshot({**base, "counter": None}) == "invalid"
        assert classify_pulse_snapshot({**base, "counter": "x"}) == "invalid"
        assert classify_pulse_snapshot({**base, "counter": -1}) == "invalid"
        assert classify_pulse_snapshot(base) == "invalid"

    def test_invalid_epoch(self):
        base = {"deviceId": "d", "counter": 10, "online": True}
        assert classify_pulse_snapshot(base) == "invalid"
        assert classify_pulse_snapshot({**base, "counterEpoch": "y"}) == "invalid"

    def test_offline(self):
        assert classify_pulse_snapshot(
            {"deviceId": "d", "counter": 1, "counterEpoch": 1, "online": False}
        ) == "offline"

    def test_stale(self):
        stale = datetime.now(timezone.utc) - timedelta(seconds=30)
        assert classify_pulse_snapshot(
            {
                "deviceId": "d",
                "counter": 1,
                "counterEpoch": 1,
                "online": True,
                "lastSeenAt": stale.isoformat(),
                "pollIntervalMs": 500,
            }
        ) == "offline"


class TestPlayRequiresUsableSnapshot:
    def test_play_rejected_when_device_offline(self):
        repo = FakeRepo()
        pulse = FakePulse(
            devices=[{"deviceId": "d", "counter": 0, "counterEpoch": 0, "online": False}]
        )
        service = make_service(repo, pulse)
        session = service.create_bench_session(
            branch="01", work_center="CT01", registration="U"
        )["sessionToken"]
        with pytest.raises(PulseDeviceUnavailable):
            _start(service, session)
        assert repo.get_active_run(branch="01", work_center="CT01") is None

    def test_play_rejected_when_counter_missing(self):
        repo = FakeRepo()
        pulse = FakePulse(devices=[{"deviceId": "d", "counterEpoch": 1, "online": True}])
        service = make_service(repo, pulse)
        session = service.create_bench_session(
            branch="01", work_center="CT01", registration="U"
        )["sessionToken"]
        with pytest.raises(PulseDeviceUnavailable):
            _start(service, session)
        assert repo.get_active_run(branch="01", work_center="CT01") is None


class TestPauseWithoutPulse:
    def test_pause_works_when_pulse_fails(self):
        audit = FakeAudit()
        service, repo, pulse, session = _setup(audit=audit)
        run = _start(service, session)
        pulse.fail = True
        paused = service.pause_run(run["id"], session_token=session)
        assert paused["status"] == "paused"
        actions = [r["action"] for r in audit.records]
        assert "run_paused" in actions
        assert "telemetry_fallback_used" in actions

    def test_pause_preserves_last_persisted_count(self):
        audit = FakeAudit()
        service, repo, pulse, session = _setup(audit=audit)
        run = _start(service, session)
        pulse.counter = 150  # avançou mas não será mais lido
        pulse.fail = True
        paused = service.pause_run(run["id"], session_token=session)
        # último persistido = baseline do anchor (0 peças contadas)
        assert paused["piecesTotal"] == 0

    def test_pause_never_assumes_counter_zero(self):
        service, repo, pulse, session = _setup()
        run = _start(service, session)
        pulse.device_by_id[run["deviceId"]] = {
            "deviceId": run["deviceId"],
            "online": True,
            # counter e counterEpoch ausentes — nunca podem virar 0
        }
        paused = service.pause_run(run["id"], session_token=session)
        assert paused["status"] == "paused"
        segment = repo.get_open_segment(run["id"])
        assert segment is None  # fechado com o último conhecido, sem inventar


class TestResumeWithoutPulse:
    def test_resume_rejected_and_state_preserved(self):
        service, repo, pulse, session = _setup()
        run = _start(service, session)
        service.pause_run(run["id"], session_token=session)
        _classify_open(service._mes._downtimes)
        pulse.fail = True
        segments_before = len(repo.segments)
        with pytest.raises(PulseDeviceUnavailable):
            service.resume_run(run["id"], session_token=session)
        locked = repo.get_active_run(branch="01", work_center="CT01")
        assert locked["status"] == "paused"
        assert len(repo.segments) == segments_before  # nenhum segmento falso


class TestStopWithoutPulse:
    def test_stop_running_works_when_pulse_fails(self):
        audit = FakeAudit()
        service, repo, pulse, session = _setup(audit=audit)
        run = _start(service, session)
        pulse.fail = True
        stopped = service.stop_run(run["id"], session_token=session)
        assert stopped["status"] == "completed"
        actions = [r["action"] for r in audit.records]
        assert "run_stopped" in actions
        assert "telemetry_fallback_used" in actions

    def test_stop_paused_does_not_call_pulse(self):
        service, repo, pulse, session = _setup()
        run = _start(service, session)
        service.pause_run(run["id"], session_token=session)
        _classify_open(service._mes._downtimes)
        pulse.fail = True
        stopped = service.stop_run(run["id"], session_token=session)
        assert stopped["status"] == "completed"


class TestAuditTrail:
    def test_full_lifecycle_records_actor(self):
        audit = FakeAudit()
        service, repo, pulse, session = _setup(audit=audit)
        run = _start(service, session)
        service.pause_run(run["id"], session_token=session)
        _classify_open(service._mes._downtimes)
        service.resume_run(run["id"], session_token=session)
        service.stop_run(run["id"], session_token=session)
        actions = [r["action"] for r in audit.records]
        assert actions[:4] == [
            "run_started",
            "run_paused",
            "run_resumed",
            "run_stopped",
        ]
        assert all(r["actor_type"] == "operator" for r in audit.records)
        assert all(r["actor_ref"] == "USR01" for r in audit.records)
        assert all(r["run_id"] == run["id"] for r in audit.records)

    def test_epoch_change_is_audited(self):
        audit = FakeAudit()
        service, repo, pulse, session = _setup(audit=audit)
        run = _start(service, session)
        pulse.epoch = 2
        pulse.counter = 5
        service.pause_run(run["id"], session_token=session)
        actions = [r["action"] for r in audit.records]
        assert "counter_epoch_changed" in actions
        evt = next(r for r in audit.records if r["action"] == "counter_epoch_changed")
        assert evt["details"]["previousEpoch"] == 1
        assert evt["details"]["newEpoch"] == 2


class TestRuntimeIntegrity:
    def _report(self, **kwargs):
        base = {
            "runs": [],
            "open_states": [],
            "open_downtimes": [],
            "open_segments": [],
            "state_runs": {},
            "mes_observed_runs": set(),
        }
        base.update(kwargs)
        return base

    def test_running_ok(self):
        report = self._report(
            runs=[{"id": "r1", "status": "running", "branch": "01", "work_center": "CT01"}],
            open_states=[{"run_id": "r1", "branch": "01", "work_center": "CT01", "state": "producing"}],
            open_segments=[{"run_id": "r1"}],
            mes_observed_runs={"r1"},
        )
        assert inspect_runtime_integrity(report) == []

    def test_paused_ok(self):
        report = self._report(
            runs=[{"id": "r1", "status": "paused", "branch": "01", "work_center": "CT01"}],
            open_states=[{"run_id": "r1", "branch": "01", "work_center": "CT01", "state": "stopped"}],
            open_downtimes=[{"run_id": "r1", "branch": "01", "work_center": "CT01"}],
            mes_observed_runs={"r1"},
        )
        assert inspect_runtime_integrity(report) == []

    def test_legacy_run_warns(self):
        report = self._report(
            runs=[{"id": "r1", "status": "running", "branch": "01", "work_center": "CT01"}]
        )
        issues = inspect_runtime_integrity(report)
        assert issues[0]["severity"] == "WARNING"
        assert issues[0]["issue_code"] == "legacy_run_without_mes_events"

    def test_running_with_open_stopped_is_critical(self):
        report = self._report(
            runs=[{"id": "r1", "status": "running", "branch": "01", "work_center": "CT01"}],
            open_states=[{"run_id": "r1", "branch": "01", "work_center": "CT01", "state": "stopped"}],
            open_segments=[{"run_id": "r1"}],
            mes_observed_runs={"r1"},
        )
        codes = {i["issue_code"] for i in inspect_runtime_integrity(report)}
        assert "running_with_open_stopped" in codes
        assert "running_without_open_producing" in codes

    def test_paused_with_producing_is_critical(self):
        report = self._report(
            runs=[{"id": "r1", "status": "paused", "branch": "01", "work_center": "CT01"}],
            open_states=[{"run_id": "r1", "branch": "01", "work_center": "CT01", "state": "producing"}],
            open_downtimes=[{"run_id": "r1", "branch": "01", "work_center": "CT01"}],
            mes_observed_runs={"r1"},
        )
        codes = {i["issue_code"] for i in inspect_runtime_integrity(report)}
        assert "paused_with_open_producing" in codes
        assert "paused_without_open_stopped" in codes

    def test_orphan_downtime_is_critical(self):
        report = self._report(
            runs=[{"id": "r1", "status": "running", "branch": "01", "work_center": "CT01"}],
            open_states=[{"run_id": "r1", "branch": "01", "work_center": "CT01", "state": "producing"}],
            open_segments=[{"run_id": "r1"}],
            open_downtimes=[{"run_id": "r2", "branch": "01", "work_center": "CT01"}],
            mes_observed_runs={"r1", "r2"},
        )
        codes = {i["issue_code"] for i in inspect_runtime_integrity(report)}
        assert "open_downtime_of_other_run" in codes

    def test_completed_with_open_state_is_critical(self):
        report = self._report(
            runs=[{"id": "r1", "status": "completed", "branch": "01", "work_center": "CT01"}],
            open_states=[{"run_id": "r1", "branch": "01", "work_center": "CT01", "state": "producing"}],
            mes_observed_runs={"r1"},
        )
        codes = {i["issue_code"] for i in inspect_runtime_integrity(report)}
        assert "finished_with_open_state" in codes


@_DB_REQUIRED
class TestAuditPostgres:
    """Auditoria real no Postgres: append-only e atômica com a transição."""

    @pytest.fixture()
    def clean_ct(self):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        wc = "ZZ-TEST-AU"

        def _clean() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.production_run_segments "
                        f"WHERE run_id IN (SELECT id FROM "
                        f"{PC_SCHEMA_NAME}.production_runs WHERE work_center = %s)",
                        (wc,),
                    )
                    for table in (
                        "mes_audit_events",
                        "downtime_events",
                        "work_center_state_events",
                        "production_runs",
                        "operator_bench_sessions",
                    ):
                        cur.execute(
                            f"DELETE FROM {PC_SCHEMA_NAME}.{table} "
                            "WHERE work_center = %s",
                            (wc,),
                        )
                conn.commit()

        _clean()
        yield wc
        _clean()

    def _service(self):
        from production_control_app.application.services.mes_run_lifecycle_service import (  # noqa: E501
            MesRunLifecycleService,
        )
        from production_control_app.application.services.production_run_service import (  # noqa: E501
            ProductionRunService,
        )
        from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
            PostgresDowntimeEventRepository,
            PostgresDowntimeReasonRepository,
            PostgresMesAuditRepository,
            PostgresWorkCenterStateRepository,
        )
        from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
            PostgresProductionRunRepository,
        )

        device = _pg_device()
        service = ProductionRunService(
            repository=PostgresProductionRunRepository(),
            pulse_gateway=FakePulse(
                devices=[device], device_by_id={device["deviceId"]: device}
            ),
            mes_lifecycle=MesRunLifecycleService(
                states=PostgresWorkCenterStateRepository(),
                downtimes=PostgresDowntimeEventRepository(),
                reasons=PostgresDowntimeReasonRepository(),
            ),
            audit=PostgresMesAuditRepository(),
        )
        return service

    def test_lifecycle_persists_audit_rows(self, clean_ct):
        service = self._service()
        session = service.create_bench_session(
            branch="01",
            work_center=clean_ct,
            registration="USR01",
        )["sessionToken"]
        run = service.start_run(
            branch="01",
            work_center=clean_ct,
            production_order="OP-AU",
            operation_code="10",
            session_token=session,
        )
        service.pause_run(run["id"], session_token=session)
        from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
            PostgresMesAuditRepository,
        )

        rows = PostgresMesAuditRepository().list_for_run(run["id"])
        assert [r["action"] for r in rows] == ["run_started", "run_paused"]
        assert all(r["actor_type"] == "operator" for r in rows)
        assert all(r["actor_ref"] == "USR01" for r in rows)
        assert all(r["run_id"] == run["id"] for r in rows)

    def test_rollback_leaves_no_orphan_audit(self, clean_ct):
        from production_control_app.application.services.mes_run_lifecycle_service import (  # noqa: E501
            MesRunLifecycleService,
        )
        from production_control_app.application.services.production_run_service import (  # noqa: E501
            ProductionRunService,
        )
        from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
            PostgresDowntimeEventRepository,
            PostgresMesAuditRepository,
            PostgresWorkCenterStateRepository,
        )
        from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
            PostgresProductionRunRepository,
        )

        class ExplodingDowntimes(PostgresDowntimeEventRepository):
            def create(self, **kwargs):
                raise RuntimeError("boom")

        device = _pg_device()
        repo = PostgresProductionRunRepository()
        service = ProductionRunService(
            repository=repo,
            pulse_gateway=FakePulse(
                devices=[device], device_by_id={device["deviceId"]: device}
            ),
            mes_lifecycle=MesRunLifecycleService(
                states=PostgresWorkCenterStateRepository(),
                downtimes=ExplodingDowntimes(),
            ),
            audit=PostgresMesAuditRepository(),
        )
        session = service.create_bench_session(
            branch="01",
            work_center=clean_ct,
            registration="USR01",
        )["sessionToken"]
        run = service.start_run(
            branch="01",
            work_center=clean_ct,
            production_order="OP-AU2",
            operation_code="10",
            session_token=session,
        )
        with pytest.raises(RuntimeError):
            service.pause_run(run["id"], session_token=session)

        rows = PostgresMesAuditRepository().list_for_run(run["id"])
        actions = [r["action"] for r in rows]
        assert "run_paused" not in actions
        assert actions == ["run_started"]
        locked = repo.get_active_run(branch="01", work_center=clean_ct)
        assert locked["status"] == "running"
