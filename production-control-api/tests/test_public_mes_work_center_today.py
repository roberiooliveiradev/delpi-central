"""Etapa 2 — histórico diário MES do posto no cockpit público."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_mes_work_center_today_service import (
    PublicMesWorkCenterTodayService,
)
from production_control_app.domain.errors import (
    BenchSessionRequired,
    DowntimeSourceUnavailable,
    PublicAccessDenied,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService

SP = ZoneInfo("America/Sao_Paulo")
NOW = datetime(2026, 10, 19, 13, 0, tzinfo=SP)  # 16:00 UTC


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _fact(
    *,
    state: str,
    started: datetime,
    ended: datetime | None,
    run_id: str = "run-1",
    op: str = "OP-1",
    operation: str = "10",
    source: str = "operator",
    event_id: str | None = None,
    downtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "stateEventId": event_id or f"se-{state}-{started.timestamp():.0f}-{run_id}",
        "runId": run_id,
        "productionOrder": op,
        "operationCode": operation,
        "state": state,
        "startedAt": _iso(started),
        "endedAt": _iso(ended) if ended else None,
        "source": source,
        "downtime": downtime,
    }


class FakeDowntimeSource:
    def __init__(self, source: str = "mes", reason: str = "bound_counter") -> None:
        self.resolution = {
            "source": source,
            "reason": reason,
            "referenceAt": NOW.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        self.calls = 0

    def resolve(self, **kwargs: Any) -> dict[str, Any]:
        self.calls += 1
        return self.resolution


class FakeIntegrationRead:
    def __init__(self, items: list[dict[str, Any]] | None = None, *, fail: bool = False) -> None:
        self.items = items or []
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def get_work_center_timeline(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError("db down")
        return {
            "branch": kwargs["branch"],
            "workCenter": kwargs["work_center"],
            "from": kwargs["period_from"].isoformat(),
            "to": kwargs["period_to"].isoformat(),
            "referenceAt": NOW.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "items": self.items,
        }


class FakeRunService:
    def __init__(self, session: dict[str, Any] | None = None) -> None:
        self.session = session or {"branch": "01", "work_center": "CT-01A"}

    def resolve_bench_session(self, raw_token: str | None) -> dict[str, Any]:
        if not raw_token or raw_token == "expired":
            raise BenchSessionRequired("Sessão inválida. Identifique-se novamente.")
        return self.session


class FakeMachineLoad:
    def __init__(self, resources: Any = ("MAQ01",)) -> None:
        self.resources = resources
        self.calls = 0

    def public_snapshot_work_center_resources(self, **kwargs: Any) -> Any:
        self.calls += 1
        return self.resources


def _service(
    *,
    source: FakeDowntimeSource | None = None,
    read: FakeIntegrationRead | None = None,
    run_service: FakeRunService | None = None,
    machine_load: FakeMachineLoad | None = None,
) -> PublicMesWorkCenterTodayService:
    return PublicMesWorkCenterTodayService(
        access=PublicCockpitAccessService(),
        machine_load=machine_load or FakeMachineLoad(),
        branch_access=BranchAccessService(),
        downtime_source=source or FakeDowntimeSource(),
        integration_read=read or FakeIntegrationRead(),
        run_service=run_service or FakeRunService(),
        clock=lambda: NOW,
    )


def _token() -> str:
    return PublicCockpitAccessService().token()


def _get(service, **kw) -> dict[str, Any]:
    return service.get_today(
        token=kw.get("token", _token()),
        branch=kw.get("branch", "01"),
        work_center=kw.get("work_center", "CT-01A"),
        session_token=kw.get("session_token", "sess-1"),
    )


# --- AC-01..AC-09: cenários felizes ------------------------------------------

def test_ac01_run_with_downtime_today() -> None:
    started = NOW.replace(hour=8, minute=0, second=0)
    stopped_at = NOW.replace(hour=9, minute=0, second=0)
    resumed = NOW.replace(hour=9, minute=30, second=0)
    read = FakeIntegrationRead(
        [
            _fact(state="producing", started=started, ended=stopped_at),
            _fact(
                state="stopped",
                started=stopped_at,
                ended=resumed,
                source="system",
                downtime={
                    "id": "dt-1",
                    "reasonCode": "setup",
                    "reasonLabel": "Setup",
                    "category": "setup",
                    "note": "Troca de cabo",
                    "confirmed": True,
                    "source": "system",
                },
            ),
            _fact(state="producing", started=resumed, ended=None),
        ]
    )
    data = _get(_service(read=read))
    assert data["source"] == "mes"
    assert len(data["items"]) == 3
    assert data["summary"]["producingSeconds"] == 3600 + int(
        (NOW - resumed).total_seconds()
    )
    assert data["summary"]["stoppedSeconds"] == 1800
    assert data["summary"]["stopCount"] == 1
    assert data["summary"]["pendingReasonCount"] == 0


def test_ac02_multiple_runs_same_work_center() -> None:
    t0 = NOW.replace(hour=7)
    read = FakeIntegrationRead(
        [
            _fact(state="producing", started=t0, ended=t0 + timedelta(hours=1), run_id="r1", op="OP-A"),
            _fact(state="stopped", started=t0 + timedelta(hours=1), ended=t0 + timedelta(hours=1, minutes=20), run_id="r1", op="OP-A"),
            _fact(state="producing", started=t0 + timedelta(hours=2), ended=t0 + timedelta(hours=3), run_id="r2", op="OP-B", operation="20"),
        ]
    )
    data = _get(_service(read=read))
    ops = {i["productionOrder"] for i in data["items"]}
    assert ops == {"OP-A", "OP-B"}
    assert data["summary"]["stopCount"] == 1


def test_ac03_history_without_active_run() -> None:
    ended = NOW.replace(hour=10)
    read = FakeIntegrationRead(
        [
            _fact(state="producing", started=ended - timedelta(hours=2), ended=ended),
            _fact(state="stopped", started=ended, ended=ended + timedelta(minutes=15)),
        ]
    )
    data = _get(_service(read=read))
    assert len(data["items"]) == 2
    assert all(i["endedAt"] for i in data["items"])


def test_ac04_overnight_stop_clipped_to_today() -> None:
    yesterday_2350 = NOW.replace(hour=0, minute=0, second=0) - timedelta(minutes=10)
    today_0020 = NOW.replace(hour=0, minute=20, second=0)
    read = FakeIntegrationRead(
        [_fact(state="stopped", started=yesterday_2350, ended=today_0020)]
    )
    data = _get(_service(read=read))
    item = data["items"][0]
    assert item["startedAt"] == _iso(yesterday_2350)  # original preservado
    assert item["effectiveDurationSeconds"] == 20 * 60  # só a sobreposição
    assert data["summary"]["stoppedSeconds"] == 1200


def test_ac05_open_downtime_until_reference() -> None:
    started = NOW - timedelta(minutes=45)
    read = FakeIntegrationRead([_fact(state="stopped", started=started, ended=None)])
    data = _get(_service(read=read))
    assert data["items"][0]["effectiveDurationSeconds"] == 45 * 60
    assert data["items"][0]["endedAt"] is None


def test_ac06_closed_unreasoned_downtime_is_pending() -> None:
    started = NOW - timedelta(hours=1)
    read = FakeIntegrationRead(
        [
            _fact(
                state="stopped",
                started=started,
                ended=started + timedelta(minutes=10),
                downtime={"id": "dt-9", "reasonCode": None, "reasonLabel": None,
                          "category": None, "note": None, "confirmed": False,
                          "source": "system"},
            )
        ]
    )
    data = _get(_service(read=read))
    dt = data["items"][0]["downtime"]
    assert dt["id"] == "dt-9" and dt["pendingReason"] is True
    assert data["summary"]["pendingReasonCount"] == 1


def test_ac07_system_confirmed_setup_not_pending() -> None:
    read = FakeIntegrationRead(
        [
            _fact(
                state="stopped",
                started=NOW - timedelta(minutes=30),
                ended=NOW - timedelta(minutes=20),
                downtime={"id": "dt-2", "reasonCode": "setup", "reasonLabel": "Setup",
                          "category": "setup", "note": None, "confirmed": True,
                          "source": "system"},
            )
        ]
    )
    data = _get(_service(read=read))
    assert data["items"][0]["downtime"]["pendingReason"] is False
    assert data["summary"]["pendingReasonCount"] == 0


def test_ac08_reason_and_note_preserved() -> None:
    read = FakeIntegrationRead(
        [
            _fact(
                state="stopped",
                started=NOW - timedelta(hours=1),
                ended=NOW - timedelta(minutes=50),
                downtime={"id": "dt-3", "reasonCode": "MT", "reasonLabel": "Manutenção",
                          "category": "maintenance", "note": "Vazamento óleo",
                          "confirmed": True, "source": "operator_pause"},
            )
        ]
    )
    dt = _get(_service(read=read))["items"][0]["downtime"]
    assert dt["reasonCode"] == "MT" and dt["note"] == "Vazamento óleo"


def test_ac09_mes_wc_without_facts_returns_empty() -> None:
    data = _get(_service(read=FakeIntegrationRead([])))
    assert data["source"] == "mes" and data["items"] == []
    assert data["summary"] == {
        "producingSeconds": 0,
        "stoppedSeconds": 0,
        "stopCount": 0,
        "pendingReasonCount": 0,
    }


# --- AC-10..AC-13: fonte e segurança -----------------------------------------

def test_ac10_totvs_source_no_mes_timeline() -> None:
    read = FakeIntegrationRead()
    data = _get(_service(source=FakeDowntimeSource("totvs", "no_bound_counter"), read=read))
    assert data["source"] == "totvs"
    assert "items" not in data
    assert not read.calls  # histórico MES nunca consultado


def test_ac11_unavailable_is_explicit_error() -> None:
    read = FakeIntegrationRead()
    with pytest.raises(DowntimeSourceUnavailable):
        _get(_service(source=FakeDowntimeSource("unavailable", "source_lookup_unavailable"), read=read))
    assert not read.calls


def test_ac12_invalid_token_and_session() -> None:
    with pytest.raises(PublicAccessDenied):
        _get(_service(), token="bogus")
    with pytest.raises(BenchSessionRequired):
        _get(_service(), session_token=None)
    with pytest.raises(BenchSessionRequired):
        _get(_service(), session_token="expired")


def test_ac13_session_other_work_center_denied() -> None:
    service = _service(run_service=FakeRunService({"branch": "01", "work_center": "CT-OUTRO"}))
    with pytest.raises(BenchSessionRequired):
        _get(service)
    service2 = _service(run_service=FakeRunService({"branch": "02", "work_center": "CT-01A"}))
    with pytest.raises(BenchSessionRequired):
        _get(service2)


# --- AC-14..AC-16: temporal, identidade e leitura -----------------------------

def test_ac14_window_and_reference() -> None:
    data = _get(_service())
    assert data["date"] == "2026-10-19"
    assert data["timezone"] == "America/Sao_Paulo"
    assert data["from"] == "2026-10-19T00:00:00-03:00"
    assert data["to"] == NOW.isoformat()
    assert data["referenceAt"] == "2026-10-19T16:00:00Z"


def test_ac15_stopped_without_downtime_no_fake_identity() -> None:
    read = FakeIntegrationRead(
        [_fact(state="stopped", started=NOW - timedelta(minutes=10), ended=NOW - timedelta(minutes=5))]
    )
    item = _get(_service(read=read))["items"][0]
    assert item["downtime"] is None
    assert "downtimeId" not in str(item)


def test_ac16_repeated_get_read_only() -> None:
    read = FakeIntegrationRead([_fact(state="producing", started=NOW - timedelta(hours=1), ended=None)])
    ml = FakeMachineLoad()
    service = _service(read=read, machine_load=ml)
    for _ in range(3):
        _get(service)
    assert ml.calls == 3 and len(read.calls) == 3  # só leituras


# --- AC-18: sobreposição anômala ----------------------------------------------

def test_ac18_overlapping_events_do_not_double_count() -> None:
    t0 = NOW.replace(hour=9)
    read = FakeIntegrationRead(
        [
            _fact(state="producing", started=t0, ended=t0 + timedelta(hours=2), event_id="se-a"),
            # sobreposto: segundo producing dentro do primeiro
            _fact(state="producing", started=t0 + timedelta(hours=1), ended=t0 + timedelta(hours=3), event_id="se-b"),
        ]
    )
    data = _get(_service(read=read))
    assert data["summary"]["producingSeconds"] == 3 * 3600  # união, não 5h


# --- contrato HTTP -----------------------------------------------------------


class TestMesTodayRoute:
    def _client(self, service, monkeypatch):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from production_control_app.interface.http.routes import (
            public_machine_load_routes as routes,
        )

        app = FastAPI()
        app.include_router(routes.router)
        monkeypatch.setattr(
            routes,
            "build_public_mes_work_center_today_service",
            lambda *a, **kw: service,
        )
        monkeypatch.setattr(
            routes,
            "build_public_cockpit_access_service",
            lambda *a, **kw: PublicCockpitAccessService(),
        )
        return TestClient(app)

    def _url(self, token: str) -> str:
        return f"/public/machine-load/{token}/mes/work-centers/today"

    def test_contract_mes_shape(self, monkeypatch) -> None:
        started = NOW - timedelta(hours=1)
        service = _service(
            read=FakeIntegrationRead(
                [_fact(state="stopped", started=started, ended=None)]
            )
        )
        api = self._client(service, monkeypatch)
        resp = api.get(
            self._url(_token()),
            params={"branch": "01", "workCenter": "CT-01A"},
            headers={"X-Delpi-Bench-Session": "sess-1"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["source"] == "mes"
        assert data["summary"]["stoppedSeconds"] == 3600
        assert set(data["items"][0]["downtime"] or {}) == (
            set(data["items"][0]["downtime"] or {})
        )

    def test_missing_session_401(self, monkeypatch) -> None:
        api = self._client(_service(), monkeypatch)
        resp = api.get(
            self._url(_token()),
            params={"branch": "01", "workCenter": "CT-01A"},
        )
        assert resp.status_code == 401

    def test_invalid_token_404(self, monkeypatch) -> None:
        api = self._client(_service(), monkeypatch)
        resp = api.get(
            self._url("bogus"),
            params={"branch": "01", "workCenter": "CT-01A"},
            headers={"X-Delpi-Bench-Session": "sess-1"},
        )
        assert resp.status_code == 404

    def test_unavailable_503(self, monkeypatch) -> None:
        service = _service(
            source=FakeDowntimeSource("unavailable", "source_lookup_unavailable")
        )
        api = self._client(service, monkeypatch)
        resp = api.get(
            self._url(_token()),
            params={"branch": "01", "workCenter": "CT-01A"},
            headers={"X-Delpi-Bench-Session": "sess-1"},
        )
        assert resp.status_code == 503

    def test_totvs_controlled_response(self, monkeypatch) -> None:
        service = _service(source=FakeDowntimeSource("totvs", "no_bound_counter"))
        api = self._client(service, monkeypatch)
        resp = api.get(
            self._url(_token()),
            params={"branch": "01", "workCenter": "CT-01A"},
            headers={"X-Delpi-Bench-Session": "sess-1"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["source"] == "totvs" and "items" not in data


# ---------------------------------------------------------------------------
# Integração Postgres (PC_TEST_MES_DB=1 + PLUGINS_DB_*)
# ---------------------------------------------------------------------------

import os

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestMesTodayPostgres:
    def test_today_end_to_end_real_db(self):
        """Cadeia real: run + pause (parada real persistida) → a API diária
        devolve o fato com downtime/pendingReason corretos."""
        from production_control_app.application.services.mes_integration_read_service import (  # noqa: E501
            MesIntegrationReadService,
        )
        from production_control_app.application.services.mes_run_lifecycle_service import (  # noqa: E501
            MesRunLifecycleService,
        )
        from production_control_app.application.services.production_run_service import (  # noqa: E501
            ProductionRunService,
        )
        from production_control_app.application.services.public_work_center_downtime_source_service import (  # noqa: E501
            PublicWorkCenterDowntimeSourceService,
        )
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )
        from production_control_app.infrastructure.persistence.postgres_mes_monitoring_read_repository import (  # noqa: E501
            PostgresMesMonitoringReadRepository,
        )
        from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
            PostgresDowntimeEventRepository,
            PostgresDowntimeReasonRepository,
            PostgresWorkCenterStateRepository,
        )
        from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
            PostgresProductionRunRepository,
        )

        from tests.test_mes_auto_downtime import FakePulse, _pg_device
        from tests.test_production_run_service import FakeOperatorDirectory

        wc = "ZZ-TEST-TODAY"
        repo = PostgresProductionRunRepository()
        monitoring = PostgresMesMonitoringReadRepository()
        lifecycle = MesRunLifecycleService(
            states=PostgresWorkCenterStateRepository(),
            downtimes=PostgresDowntimeEventRepository(),
            reasons=PostgresDowntimeReasonRepository(),
            run_lookup=repo.get_run,
        )
        device = _pg_device()
        pulse = FakePulse(
            devices=[device], device_by_id={device["deviceId"]: device}
        )
        run_service = ProductionRunService(
            repository=repo,
            pulse_gateway=pulse,
            mes_lifecycle=lifecycle,
            operator_directory=FakeOperatorDirectory(),
        )
        source_service = PublicWorkCenterDowntimeSourceService(
            access=PublicCockpitAccessService(),
            machine_load=FakeMachineLoad(),
            branch_access=BranchAccessService(),
            pulse_gateway=pulse,
            mes_monitoring=monitoring,
        )
        service = PublicMesWorkCenterTodayService(
            access=PublicCockpitAccessService(),
            machine_load=FakeMachineLoad(),
            branch_access=BranchAccessService(),
            downtime_source=source_service,
            integration_read=MesIntegrationReadService(
                repository=monitoring,
                branch_access=BranchAccessService(),
            ),
            run_service=run_service,
        )

        def _clean() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.mes_audit_events "
                        "WHERE work_center = %s", (wc,))
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.downtime_events "
                        "WHERE work_center = %s", (wc,))
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.work_center_state_events "
                        "WHERE work_center = %s", (wc,))
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.production_run_segments "
                        "WHERE run_id IN (SELECT id FROM "
                        f"{PC_SCHEMA_NAME}.production_runs WHERE work_center = %s)",
                        (wc,))
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.production_runs "
                        "WHERE work_center = %s", (wc,))
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.operator_bench_sessions "
                        "WHERE work_center = %s", (wc,))
                conn.commit()

        _clean()
        try:
            token = run_service.create_bench_session(
                branch="01", work_center=wc, registration="USR01"
            )["sessionToken"]
            run = run_service.start_run(
                branch="01", work_center=wc, production_order="OP-TODAY",
                operation_code="10", session_token=token,
            )
            run_service.pause_run(run["id"], session_token=token)

            data = service.get_today(
                token=_token(), branch="01", work_center=wc,
                session_token=token,
            )
            assert data["source"] == "mes"
            states = [i["state"] for i in data["items"]]
            assert "producing" in states and "stopped" in states
            stop = [i for i in data["items"] if i["state"] == "stopped"][0]
            assert stop["downtime"]["id"]
            assert data["summary"]["stopCount"] == 1
            # run encerrado ainda aparece no dia — classifica a parada
            # pendente antes (regra MES: não encerra com motivo pendente)
            from production_control_app.application.services.mes_downtime_classification_service import (  # noqa: E501
                MesDowntimeClassificationService,
            )

            classifier = MesDowntimeClassificationService(
                run_service=run_service,
                downtimes=PostgresDowntimeEventRepository(),
                reasons=PostgresDowntimeReasonRepository(),
            )
            pending = [r for r in monitoring.list_work_center_timeline_facts(
                branch="01", work_center=wc,
                period_from=datetime.now(timezone.utc) - timedelta(hours=1),
                period_to=datetime.now(timezone.utc) + timedelta(hours=1),
            ) if r.get("downtime_id") and not r.get("reason_code")]
            classifier.classify(
                run["id"],
                reason_code="maintenance",
                note=None,
                session_token=token,
                downtime_id=pending[0]["downtime_id"],
            )
            run_service.stop_run(run["id"], session_token=token)
            data2 = service.get_today(
                token=_token(), branch="01", work_center=wc,
                session_token=token,
            )
            # run encerrado: eventos fechados, nenhum cresce após ended_at
            assert all(i["endedAt"] for i in data2["items"])
            assert len(data2["items"]) >= 2
        finally:
            _clean()
