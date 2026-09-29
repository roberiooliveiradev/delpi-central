"""Etapa 02 — lifecycle do run produzindo fatos MES de forma transacional.

Unitários usam fakes (sem banco). A seção ``_DB_REQUIRED`` repete o fluxo no
Postgres real para provar atomicidade/rollback das transições compostas.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from production_control_app.application.services.production_run_service import (
    ProductionRunService,
)
from production_control_app.domain.errors import (
    InvalidMesEvent,
    MesStateConflict,
    ProductionRunConflict,
)

from tests.test_production_run_service import (
    FakeDowntimeRepo,
    FakePulse,
    FakeRepo,
    FakeStateRepo,
    make_mes,
    make_service,
    service_session,
)


def _started_run(service, repo, session):
    return service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )


def _device() -> dict:
    return {"deviceId": "dev-1", "counter": 100, "counterEpoch": 1, "online": True}


def _pg_device() -> dict:
    """device_id é UUID no banco — integração precisa de um id válido."""
    return {
        "deviceId": "00000000-0000-4000-8000-0000000000d1",
        "counter": 100,
        "counterEpoch": 1,
        "online": True,
    }


class TestPlayProducesProducing:
    def test_start_opens_producing_linked_to_run(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, _ = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        started = _started_run(service, repo, session)

        events = states.list_for_run(started["id"])
        assert len(events) == 1
        assert events[0]["state"] == "producing"
        assert events[0]["source"] == "operator"
        assert events[0]["ended_at"] is None

    def test_start_conflicts_when_state_already_open(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, _ = make_mes()
        states.open_event(
            branch="01", work_center="CT01", state="idle", source="system"
        )
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        with pytest.raises(MesStateConflict):
            _started_run(service, repo, session)


class TestPauseProducesStoppedAndDowntime:
    def test_pause_records_facts_without_reason(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        started = _started_run(service, repo, session)

        service.pause_run(started["id"], session_token=session)

        run = repo.runs[started["id"]]
        assert run["status"] == "paused"

        events = states.list_for_run(started["id"])
        assert [e["state"] for e in events] == ["producing", "stopped"]
        assert events[0]["ended_at"] is not None
        assert events[1]["ended_at"] is None

        open_dt = downtimes.get_open(branch="01", work_center="CT01")
        assert open_dt is not None
        assert open_dt["run_id"] == started["id"]
        assert open_dt["state_event_id"] == events[1]["id"]
        assert open_dt["production_order"] == "OP1"
        assert open_dt["operation_code"] == "10"
        assert open_dt["source"] == "operator_pause"
        assert open_dt["reason_code"] is None
        assert open_dt["confirmed"] is False

    def test_pause_uses_single_transition_instant(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        started = _started_run(service, repo, session)
        service.pause_run(started["id"], session_token=session)

        events = states.list_for_run(started["id"])
        open_dt = downtimes.get_open(branch="01", work_center="CT01")
        assert events[0]["ended_at"] == events[1]["started_at"] == open_dt["started_at"]

    def test_double_pause_rejected(self):
        repo = FakeRepo()
        session = service_session(repo)
        service = make_service(repo, FakePulse(devices=[_device()]))
        started = _started_run(service, repo, session)
        service.pause_run(started["id"], session_token=session)
        with pytest.raises(ProductionRunConflict):
            service.pause_run(started["id"], session_token=session)


def _classify_open(downtimes) -> None:
    """Marca a parada aberta como classificada (simula POST classify da Etapa 03)."""
    for e in downtimes.events:
        if e["ended_at"] is None:
            e["reason_code"] = "other"
            e["confirmed"] = True
            e["confirmed_at"] = datetime.now(timezone.utc)
            return
    raise AssertionError("expected an open downtime")


class TestResumeClosesDowntime:
    def test_resume_closes_downtime_and_reopens_producing(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        started = _started_run(service, repo, session)
        service.pause_run(started["id"], session_token=session)
        _classify_open(downtimes)

        service.resume_run(started["id"], session_token=session)

        assert repo.runs[started["id"]]["status"] == "running"
        assert downtimes.get_open(branch="01", work_center="CT01") is None
        dts = downtimes.list_for_run(started["id"])
        assert len(dts) == 1
        assert dts[0]["ended_at"] is not None

        events = states.list_for_run(started["id"])
        assert [e["state"] for e in events] == ["producing", "stopped", "producing"]
        assert all(e["ended_at"] is not None for e in events[:2])
        assert events[2]["ended_at"] is None

        open_segments = [s for s in repo.segments[started["id"]] if s["ended_at"] is None]
        assert len(open_segments) == 1

    def test_resume_of_legacy_paused_run_records_producing(self):
        """Run pausado antes da fundação MES: resume abre producing, sem inventar histórico."""
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        started = _started_run(service, repo, session)
        # Simula o run legado: remove os fatos MES observados no start/pause.
        service.pause_run(started["id"], session_token=session)
        states.events.clear()
        downtimes.events.clear()

        service.resume_run(started["id"], session_token=session)

        open_state = states.get_open(branch="01", work_center="CT01")
        assert open_state["state"] == "producing"
        assert downtimes.list_for_run(started["id"]) == []

    def test_resume_rejects_when_downtime_missing(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        started = _started_run(service, repo, session)
        service.pause_run(started["id"], session_token=session)
        # Inconsistência observada: parada sumiu mas o stopped continua aberto.
        downtimes.events.clear()
        with pytest.raises(InvalidMesEvent):
            service.resume_run(started["id"], session_token=session)

    def test_double_resume_rejected(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, _, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        started = _started_run(service, repo, session)
        service.pause_run(started["id"], session_token=session)
        _classify_open(downtimes)
        service.resume_run(started["id"], session_token=session)
        with pytest.raises(ProductionRunConflict):
            service.resume_run(started["id"], session_token=session)


class TestStopClosesFacts:
    def test_stop_running_closes_producing(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        started = _started_run(service, repo, session)

        service.stop_run(started["id"], session_token=session)

        assert repo.runs[started["id"]]["status"] == "completed"
        assert states.get_open(branch="01", work_center="CT01") is None
        assert downtimes.get_open(branch="01", work_center="CT01") is None

    def test_stop_paused_closes_downtime_and_stopped(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        started = _started_run(service, repo, session)
        service.pause_run(started["id"], session_token=session)
        _classify_open(downtimes)

        service.stop_run(started["id"], session_token=session)

        assert repo.runs[started["id"]]["status"] == "completed"
        assert downtimes.list_for_run(started["id"])[0]["ended_at"] is not None
        assert all(
            e["ended_at"] is not None for e in states.list_for_run(started["id"])
        )

    def test_stop_rejects_foreign_open_state(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, _ = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        started = _started_run(service, repo, session)
        # Estado aberto de outro run — inconsistência, nunca sobrescrever.
        states.events[0]["run_id"] = "outro-run"
        with pytest.raises(MesStateConflict):
            service.stop_run(started["id"], session_token=session)


# ---------------------------------------------------------------------------
# Integração Postgres: atomicidade real das transições compostas
# ---------------------------------------------------------------------------

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestLifecyclePostgresAtomicity:
    @pytest.fixture()
    def pg(self):
        from production_control_app.application.services.mes_run_lifecycle_service import (  # noqa: E501
            MesRunLifecycleService,
        )
        from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
            PostgresDowntimeEventRepository,
            PostgresWorkCenterStateRepository,
        )
        from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
            PostgresProductionRunRepository,
        )

        states = PostgresWorkCenterStateRepository()
        downtimes = PostgresDowntimeEventRepository()
        return (
            PostgresProductionRunRepository(),
            MesRunLifecycleService(states=states, downtimes=downtimes),
            states,
            downtimes,
        )

    @pytest.fixture()
    def clean_ct(self):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        wc = "ZZ-TEST-LC"

        def _clean() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.downtime_events "
                        "WHERE work_center = %s",
                        (wc,),
                    )
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.work_center_state_events "
                        "WHERE work_center = %s",
                        (wc,),
                    )
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.production_runs "
                        "WHERE work_center = %s",
                        (wc,),
                    )
                conn.commit()

        _clean()
        yield wc
        _clean()

    def _service(self, repo, mes):
        device = _pg_device()
        service = ProductionRunService(
            repository=repo,
            pulse_gateway=FakePulse(
                devices=[device], device_by_id={device["deviceId"]: device}
            ),
            mes_lifecycle=mes,
        )
        return service

    def _session(self, service, wc):
        return service.create_bench_session(
            branch="01", work_center=wc, operator_code="USR01"
        )["sessionToken"]

    def test_pause_rolls_back_everything_when_downtime_fails(self, pg, clean_ct):
        """Falha ao criar a parada desfaz run.paused e o estado 'stopped'."""
        repo, mes, states, downtimes = pg
        service = self._service(repo, mes)
        token = self._session(service, clean_ct)
        run = service.start_run(
            branch="01",
            work_center=clean_ct,
            production_order="OP-ATOMIC",
            operation_code="10",
            session_token=token,
        )

        class ExplodingDowntimes:
            def __init__(self, inner):
                self._inner = inner

            def __getattr__(self, name):
                return getattr(self._inner, name)

            def create(self, **kwargs):
                raise InvalidMesEvent("falha forçada na criação da parada")

        from production_control_app.application.services.mes_run_lifecycle_service import (  # noqa: E501
            MesRunLifecycleService,
        )

        failing = ProductionRunService(
            repository=repo,
            pulse_gateway=FakePulse(
                device_by_id={_pg_device()["deviceId"]: _pg_device()}
            ),
            mes_lifecycle=MesRunLifecycleService(
                states=states, downtimes=ExplodingDowntimes(downtimes)
            ),
        )
        with pytest.raises(InvalidMesEvent):
            failing.pause_run(run["id"], session_token=token)

        fresh = repo.get_run(run["id"])
        assert fresh["status"] == "running"
        open_state = states.get_open(branch="01", work_center=clean_ct)
        assert open_state["state"] == "producing"
        assert downtimes.get_open(branch="01", work_center=clean_ct) is None

    def test_full_lifecycle_in_real_db(self, pg, clean_ct):
        repo, mes, states, downtimes = pg
        service = self._service(repo, mes)
        token = self._session(service, clean_ct)
        run = service.start_run(
            branch="01",
            work_center=clean_ct,
            production_order="OP-FLOW",
            operation_code="10",
            session_token=token,
        )
        service.pause_run(run["id"], session_token=token)
        open_dt = downtimes.get_open(branch="01", work_center=clean_ct)
        assert open_dt["reason_code"] is None
        assert open_dt["confirmed"] is False
        downtimes.classify(
            open_dt["id"],
            reason_code="raw_material",
            planned=None,
            counts_as_availability_loss=None,
            confirmed_by_type="operator",
            confirmed_by_ref="USR01",
        )
        service.resume_run(run["id"], session_token=token)
        service.stop_run(run["id"], session_token=token)

        events = states.list_for_run(run["id"])
        assert [e["state"] for e in events] == ["producing", "stopped", "producing"]
        assert all(e["ended_at"] is not None for e in events)
        dts = downtimes.list_for_run(run["id"])
        assert len(dts) == 1
        assert dts[0]["ended_at"] is not None
        assert dts[0]["reason_code"] == "raw_material"
        assert repo.get_run(run["id"])["status"] == "completed"
