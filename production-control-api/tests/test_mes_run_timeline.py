"""Etapa 04 — timeline operacional do run e timer server-side (`referenceAt`)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import os

import pytest

from production_control_app.application.services.mes_run_timeline_service import (
    MesRunTimelineService,
)
from production_control_app.application.services.production_run_service import (
    ProductionRunService,
)
from production_control_app.domain.errors import ProductionRunNotFound

from tests.test_production_run_service import (
    FakePulse,
    FakeReasonRepo,
    FakeRepo,
    make_mes,
    make_service,
    service_session,
)


def _device() -> dict:
    return {"deviceId": "dev-1", "counter": 100, "counterEpoch": 1, "online": True}


def _timeline(run_service, states, downtimes, reasons=None):
    return MesRunTimelineService(
        run_service=run_service,
        states=states,
        downtimes=downtimes,
        reasons=reasons or FakeReasonRepo(),
    )


def _running_run():
    repo = FakeRepo()
    session = service_session(repo)
    mes, states, downtimes = make_mes()
    service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
    run = service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    return service, repo, session, run, states, downtimes


def _classify(downtimes, code="raw_material"):
    for e in downtimes.events:
        if e["ended_at"] is None:
            e["reason_code"] = code
            e["confirmed"] = True
            e["confirmed_at"] = datetime.now(timezone.utc)
            return e
    raise AssertionError("expected open downtime")


class TestTimelineComposition:
    def test_only_producing(self):
        service, _, session, run, states, downtimes = _running_run()
        svc = _timeline(service, states, downtimes)
        data = svc.get_timeline(run["id"], session_token=session)
        assert data["runId"] == run["id"]
        assert data["status"] == "running"
        assert data["summary"]["producingSeconds"] >= 0
        assert data["summary"]["stoppedSeconds"] == 0
        assert data["summary"]["stopCount"] == 0
        assert len(data["items"]) == 1
        assert data["items"][0]["state"] == "producing"
        assert data["items"][0]["endedAt"] is None
        assert data["items"][0]["downtime"] is None

    def test_producing_stopped_with_downtime(self):
        service, _, session, run, states, downtimes = _running_run()
        service.pause_run(run["id"], session_token=session)
        _classify(downtimes)
        svc = _timeline(service, states, downtimes)
        data = svc.get_timeline(run["id"], session_token=session)

        assert [i["state"] for i in data["items"]] == ["producing", "stopped"]
        stopped = data["items"][1]
        assert stopped["endedAt"] is None
        assert stopped["downtime"]["reasonCode"] == "raw_material"
        assert stopped["downtime"]["reasonLabel"] == "Falta de material"
        assert stopped["downtime"]["confirmed"] is True
        assert data["summary"]["stopCount"] == 1
        assert data["summary"]["stoppedSeconds"] >= 0

    def test_unclassified_downtime_shows_pending(self):
        service, _, session, run, states, downtimes = _running_run()
        service.pause_run(run["id"], session_token=session)
        svc = _timeline(service, states, downtimes)
        data = svc.get_timeline(run["id"], session_token=session)
        dt = data["items"][1]["downtime"]
        assert dt["reasonCode"] is None
        assert dt["reasonLabel"] is None
        assert dt["confirmed"] is False

    def test_multiple_stops_chronological(self):
        service, _, session, run, states, downtimes = _running_run()
        svc = _timeline(service, states, downtimes)

        service.pause_run(run["id"], session_token=session)
        _classify(downtimes, "raw_material")
        service.resume_run(run["id"], session_token=session)
        service.pause_run(run["id"], session_token=session)
        _classify(downtimes, "maintenance")

        data = svc.get_timeline(run["id"], session_token=session)
        assert [i["state"] for i in data["items"]] == [
            "producing", "stopped", "producing", "stopped",
        ]
        assert data["items"][1]["downtime"]["reasonLabel"] == "Falta de material"
        assert data["items"][3]["downtime"]["reasonLabel"] == "Manutenção"
        assert data["summary"]["stopCount"] == 2

    def test_durations_never_negative_and_summary_sums(self):
        service, _, session, run, states, downtimes = _running_run()
        svc = _timeline(service, states, downtimes)
        # Evento defeituoso histórico: ended < started → clamp em 0.
        states.events[0]["ended_at"] = states.events[0]["started_at"] - timedelta(
            seconds=10
        )
        data = svc.get_timeline(run["id"], session_token=session)
        assert data["items"][0]["durationSeconds"] == 0
        assert data["summary"]["producingSeconds"] == 0
        assert data["summary"]["elapsedSeconds"] >= 0

    def test_open_item_uses_reference_at(self):
        service, _, session, run, states, downtimes = _running_run()
        svc = _timeline(service, states, downtimes)
        states.events[0]["started_at"] = datetime.now(timezone.utc) - timedelta(
            seconds=120
        )
        data = svc.get_timeline(run["id"], session_token=session)
        ref = datetime.fromisoformat(data["referenceAt"].replace("Z", "+00:00"))
        assert abs((ref - datetime.now(timezone.utc)).total_seconds()) < 30
        assert data["items"][0]["durationSeconds"] >= 119

    def test_downtime_linked_via_state_event_id(self):
        service, _, session, run, states, downtimes = _running_run()
        service.pause_run(run["id"], session_token=session)
        _classify(downtimes)
        stopped_event = next(e for e in states.events if e["state"] == "stopped")
        dt = downtimes.events[0]
        assert dt["state_event_id"] == stopped_event["id"]
        svc = _timeline(service, states, downtimes)
        data = svc.get_timeline(run["id"], session_token=session)
        assert data["items"][1]["downtime"]["id"] == dt["id"]

    def test_stopped_without_downtime_does_not_break(self):
        """Inconsistência histórica: stopped sem downtime → UI tolera."""
        service, _, session, run, states, downtimes = _running_run()
        service.pause_run(run["id"], session_token=session)
        downtimes.events.clear()
        svc = _timeline(service, states, downtimes)
        data = svc.get_timeline(run["id"], session_token=session)
        stopped = data["items"][1]
        assert stopped["state"] == "stopped"
        assert stopped["downtime"] is None

    def test_inactive_reason_in_history_does_not_break(self):
        service, _, session, run, states, downtimes = _running_run()
        service.pause_run(run["id"], session_token=session)
        _classify(downtimes, "obsolete")  # motivo inativo no catálogo fake
        reasons = FakeReasonRepo()
        svc = _timeline(service, states, downtimes, reasons=reasons)
        data = svc.get_timeline(run["id"], session_token=session)
        dt = data["items"][1]["downtime"]
        assert dt["reasonCode"] == "obsolete"
        assert dt["reasonLabel"] == "Obsoleto"  # label histórico ainda legível

    def test_session_of_other_work_center_cannot_read(self):
        service, repo, session, run, states, downtimes = _running_run()
        other = service.create_bench_session(
            branch="01", work_center="CT99", operator_code="USR02"
        )["sessionToken"]
        svc = _timeline(service, states, downtimes)
        with pytest.raises(ProductionRunNotFound):
            svc.get_timeline(run["id"], session_token=other)

    def test_unknown_run_rejected(self):
        service, _, session, run, states, downtimes = _running_run()
        svc = _timeline(service, states, downtimes)
        with pytest.raises(ProductionRunNotFound):
            svc.get_timeline("run-inexistente", session_token=session)


class TestLegacyRun:
    def test_legacy_run_without_events_returns_valid_timeline(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        run = service.start_run(
            branch="01", work_center="CT01",
            production_order="OP1", operation_code="10",
            session_token=session,
        )
        states.events.clear()  # simula run pré-Etapa 02
        svc = _timeline(service, states, downtimes)
        data = svc.get_timeline(run["id"], session_token=session)
        assert data["items"] == []
        assert data["summary"]["stopCount"] == 0
        assert data["referenceAt"]


# ---------------------------------------------------------------------------
# Integração Postgres
# ---------------------------------------------------------------------------

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestTimelinePostgres:
    @pytest.fixture()
    def pg(self):
        from production_control_app.application.services.mes_run_lifecycle_service import (  # noqa: E501
            MesRunLifecycleService,
        )
        from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
            PostgresDowntimeEventRepository,
            PostgresDowntimeReasonRepository,
            PostgresWorkCenterStateRepository,
        )
        from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
            PostgresProductionRunRepository,
        )

        states = PostgresWorkCenterStateRepository()
        downtimes = PostgresDowntimeEventRepository()
        reasons = PostgresDowntimeReasonRepository()
        return (
            PostgresProductionRunRepository(),
            MesRunLifecycleService(states=states, downtimes=downtimes, reasons=reasons),
            states,
            downtimes,
            reasons,
        )

    @pytest.fixture()
    def clean_ct(self):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        wc = "ZZ-TEST-TL"

        def _clean() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.downtime_events WHERE work_center = %s",
                        (wc,),
                    )
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.work_center_state_events WHERE work_center = %s",
                        (wc,),
                    )
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.production_runs WHERE work_center = %s",
                        (wc,),
                    )
                conn.commit()

        _clean()
        yield wc
        _clean()

    def test_timeline_against_real_db(self, pg, clean_ct):
        repo, mes, states, downtimes, reasons = pg
        device = {
            "deviceId": "00000000-0000-4000-8000-0000000000d3",
            "counter": 100,
            "counterEpoch": 1,
            "online": True,
        }
        service = ProductionRunService(
            repository=repo,
            pulse_gateway=FakePulse(devices=[device], device_by_id={device["deviceId"]: device}),
            mes_lifecycle=mes,
        )
        token = service.create_bench_session(
            branch="01", work_center=clean_ct, operator_code="USR03"
        )["sessionToken"]
        run = service.start_run(
            branch="01", work_center=clean_ct,
            production_order="OP-TL", operation_code="10",
            session_token=token,
        )
        service.pause_run(run["id"], session_token=token)
        downtimes.classify(
            downtimes.get_open(branch="01", work_center=clean_ct)["id"],
            reason_code="tool",
            planned=None,
            counts_as_availability_loss=None,
            confirmed_by_type="operator",
            confirmed_by_ref="USR03",
        )
        service.resume_run(run["id"], session_token=token)

        svc = MesRunTimelineService(
            run_service=service, states=states, downtimes=downtimes, reasons=reasons
        )
        data = svc.get_timeline(run["id"], session_token=token)

        assert [i["state"] for i in data["items"]] == [
            "producing", "stopped", "producing",
        ]
        stopped = data["items"][1]
        assert stopped["downtime"]["reasonLabel"] == "Ferramenta"
        assert stopped["endedAt"] is not None
        assert data["summary"]["stopCount"] == 1
        assert data["items"][2]["endedAt"] is None
        assert data["items"][2]["durationSeconds"] >= 0
        ref = datetime.fromisoformat(data["referenceAt"].replace("Z", "+00:00"))
        assert abs((ref - datetime.now(timezone.utc)).total_seconds()) < 30
