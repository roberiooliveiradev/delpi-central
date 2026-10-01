"""Etapa 03 — classificação do motivo da parada e proteções de Resume/Stop."""

from __future__ import annotations

import os

import pytest

from production_control_app.application.services.mes_downtime_classification_service import (  # noqa: E501
    MesDowntimeClassificationService,
)
from production_control_app.application.services.production_run_service import (
    ProductionRunService,
)
from production_control_app.domain.errors import (
    DowntimeClassificationRequired,
    DowntimeNotFound,
    InvalidMesEvent,
)

from tests.test_production_run_service import (
    FakeDowntimeRepo,
    FakePulse,
    FakeReasonRepo,
    FakeRepo,
    FakeStateRepo,
    make_mes,
    make_service,
    service_session,
)


def _device() -> dict:
    return {"deviceId": "dev-1", "counter": 100, "counterEpoch": 1, "online": True}


def _paused_run():
    """Sobe um run, pausa e devolve (service, repo, session, run, downtimes)."""
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
    service.pause_run(run["id"], session_token=session)
    return service, repo, session, run, downtimes


def _classification(run_service, downtimes, reasons) -> MesDowntimeClassificationService:
    return MesDowntimeClassificationService(
        run_service=run_service, downtimes=downtimes, reasons=reasons
    )


class TestReasonCatalog:
    def test_lists_only_active_reasons(self):
        reasons = FakeReasonRepo()
        service, _, _, _, downtimes = _paused_run()
        svc = _classification(service, downtimes, reasons)
        items = svc.list_reasons()
        codes = {i["code"] for i in items}
        assert "raw_material" in codes
        assert "obsolete" not in codes
        other = next(i for i in items if i["code"] == "other")
        assert other["requiresNote"] is True
        # contrato mínimo: nada de campos internos/OEE
        assert set(other.keys()) == {"code", "label", "category", "requiresNote"}


class TestClassify:
    def test_classify_records_reason_snapshots_and_operator(self):
        service, _, session, run, downtimes = _paused_run()
        svc = _classification(service, downtimes, FakeReasonRepo())
        result = svc.classify(
            run["id"],
            reason_code="RAW_MATERIAL",
            note=None,
            session_token=session,
        )
        assert result["confirmed"] is True
        assert result["reasonCode"] == "raw_material"
        assert result["reasonLabel"] == "Falta de material"
        assert result["endedAt"] is None

        stored = downtimes.get_open(branch="01", work_center="CT01")
        assert stored["reason_code"] == "raw_material"
        assert stored["confirmed"] is True
        assert stored["confirmed_by_type"] == "operator"
        assert stored["confirmed_by_ref"] == "USR01"
        # snapshots do catálogo aplicados (NULL enquanto não governado)
        assert stored["planned"] is None

    def test_unknown_reason_rejected(self):
        service, _, session, run, downtimes = _paused_run()
        svc = _classification(service, downtimes, FakeReasonRepo())
        with pytest.raises(InvalidMesEvent):
            svc.classify(run["id"], reason_code="nao_existe", note=None, session_token=session)

    def test_inactive_reason_rejected(self):
        service, _, session, run, downtimes = _paused_run()
        svc = _classification(service, downtimes, FakeReasonRepo())
        with pytest.raises(InvalidMesEvent):
            svc.classify(run["id"], reason_code="obsolete", note=None, session_token=session)

    def test_requires_note_enforced(self):
        service, _, session, run, downtimes = _paused_run()
        svc = _classification(service, downtimes, FakeReasonRepo())
        with pytest.raises(InvalidMesEvent):
            svc.classify(run["id"], reason_code="other", note=None, session_token=session)
        ok = svc.classify(
            run["id"], reason_code="other", note="travou a grade", session_token=session
        )
        assert ok["note"] == "travou a grade"

    def test_reclassify_updates_same_downtime(self):
        service, _, session, run, downtimes = _paused_run()
        svc = _classification(service, downtimes, FakeReasonRepo())
        first = svc.classify(run["id"], reason_code="raw_material", note=None, session_token=session)
        second = svc.classify(run["id"], reason_code="maintenance", note=None, session_token=session)
        assert second["id"] == first["id"]
        assert len(downtimes.events) == 1

    def test_classify_rejects_when_no_open_downtime(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, _, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        run = service.start_run(
            branch="01", work_center="CT01",
            production_order="OP1", operation_code="10",
            session_token=session,
        )
        svc = _classification(service, downtimes, FakeReasonRepo())
        with pytest.raises(DowntimeNotFound):
            svc.classify(run["id"], reason_code="raw_material", note=None, session_token=session)

    def test_classify_rejects_downtime_of_other_run(self):
        service, _, session, run, downtimes = _paused_run()
        downtimes.events[0]["run_id"] = "outro-run"
        svc = _classification(service, downtimes, FakeReasonRepo())
        with pytest.raises(DowntimeNotFound):
            svc.classify(run["id"], reason_code="raw_material", note=None, session_token=session)


class TestResumeStopGuards:
    def test_resume_blocked_while_unclassified(self):
        service, _, session, run, _ = _paused_run()
        with pytest.raises(DowntimeClassificationRequired):
            service.resume_run(run["id"], session_token=session)

    def test_resume_works_after_classification(self):
        service, _, session, run, downtimes = _paused_run()
        svc = _classification(service, downtimes, FakeReasonRepo())
        svc.classify(run["id"], reason_code="raw_material", note=None, session_token=session)
        resumed = service.resume_run(run["id"], session_token=session)
        assert resumed["status"] == "running"

    def test_stop_paused_blocked_while_unclassified(self):
        service, _, session, run, _ = _paused_run()
        with pytest.raises(DowntimeClassificationRequired):
            service.stop_run(run["id"], session_token=session)

    def test_stop_paused_works_after_classification(self):
        service, _, session, run, downtimes = _paused_run()
        svc = _classification(service, downtimes, FakeReasonRepo())
        svc.classify(run["id"], reason_code="maintenance", note=None, session_token=session)
        stopped = service.stop_run(run["id"], session_token=session)
        assert stopped["status"] == "completed"

    def test_legacy_paused_run_resume_not_blocked(self):
        """Run pausado sem downtime MES observado não é bloqueado pela regra nova."""
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        run = service.start_run(
            branch="01", work_center="CT01",
            production_order="OP1", operation_code="10",
            session_token=session,
        )
        service.pause_run(run["id"], session_token=session)
        states.events.clear()
        downtimes.events.clear()

        resumed = service.resume_run(run["id"], session_token=session)
        assert resumed["status"] == "running"

    def test_legacy_paused_run_stop_not_blocked(self):
        repo = FakeRepo()
        session = service_session(repo)
        mes, states, downtimes = make_mes()
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        run = service.start_run(
            branch="01", work_center="CT01",
            production_order="OP1", operation_code="10",
            session_token=session,
        )
        service.pause_run(run["id"], session_token=session)
        states.events.clear()
        downtimes.events.clear()

        stopped = service.stop_run(run["id"], session_token=session)
        assert stopped["status"] == "completed"


class TestDowntimeViewInSnapshots:
    def test_pause_response_includes_open_downtime(self):
        repo = FakeRepo()
        session = service_session(repo)
        reasons = FakeReasonRepo()
        mes, states, downtimes = make_mes(reasons=reasons)
        service = make_service(repo, FakePulse(devices=[_device()]), mes_lifecycle=mes)
        run = service.start_run(
            branch="01", work_center="CT01",
            production_order="OP1", operation_code="10",
            session_token=session,
        )
        paused = service.pause_run(run["id"], session_token=session)
        assert paused["downtime"]["reasonCode"] is None
        assert paused["downtime"]["confirmed"] is False

        svc = _classification(service, downtimes, reasons)
        svc.classify(run["id"], reason_code="raw_material", note=None, session_token=session)
        active = service.get_active(branch="01", work_center="CT01")
        assert active["downtime"]["reasonCode"] == "raw_material"
        assert active["downtime"]["reasonLabel"] == "Falta de material"


# ---------------------------------------------------------------------------
# Integração Postgres: classify real + guarda de resume no banco
# ---------------------------------------------------------------------------

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestClassificationPostgres:
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
            downtimes,
            reasons,
        )

    @pytest.fixture()
    def clean_ct(self):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        wc = "ZZ-TEST-CLS"

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

    def _start_pause(self, pg, wc):
        repo, mes, downtimes, reasons = pg
        device = {
            "deviceId": "00000000-0000-4000-8000-0000000000d2",
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
            branch="01", work_center=wc, registration="USR02"
        )["sessionToken"]
        run = service.start_run(
            branch="01", work_center=wc,
            production_order="OP-CLS", operation_code="10",
            session_token=token,
        )
        service.pause_run(run["id"], session_token=token)
        return service, repo, downtimes, reasons, token, run

    def test_classify_then_resume_in_real_db(self, pg, clean_ct):
        service, repo, downtimes, reasons, token, run = self._start_pause(pg, clean_ct)
        svc = MesDowntimeClassificationService(
            run_service=service, downtimes=downtimes, reasons=reasons
        )
        with pytest.raises(DowntimeClassificationRequired):
            service.resume_run(run["id"], session_token=token)

        result = svc.classify(
            run["id"], reason_code="raw_material", note=None, session_token=token
        )
        assert result["confirmed"] is True

        resumed = service.resume_run(run["id"], session_token=token)
        assert resumed["status"] == "running"
        stored = downtimes.list_for_run(run["id"])[0]
        assert stored["reason_code"] == "raw_material"
        assert stored["confirmed_by_ref"] == "USR02"
        assert stored["ended_at"] is not None
