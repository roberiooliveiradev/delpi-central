"""Fase 2.5 — exposição de Performance nos contratos MES (S2S + live)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.mes_integration_read_service import (
    MesIntegrationReadService,
)
from production_control_app.domain.errors import ProductionRunNotFound
from production_control_app.domain.services.branch_access_service import (
    BranchAccessService,
)
from production_control_app.interface.http.routes import integration_mes_routes

NOW = datetime(2026, 9, 30, 14, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Live monitoring com Performance (batch, referenceAt único)
# ---------------------------------------------------------------------------


class FakeRepo:
    def __init__(self, rows=None, facts=None):
        self.rows = rows or []
        self.facts = facts or []
        self.live_calls = 0
        self.batch_calls = 0
        self.batch_run_ids = None

    def list_live_work_centers(self, *, branch):
        self.live_calls += 1
        return [dict(r) for r in self.rows]

    def list_timeline_facts_for_runs(self, run_ids):
        self.batch_calls += 1
        self.batch_run_ids = list(run_ids)
        return [f for f in self.facts if f.get("run_id") in set(run_ids)]


def _live_row(run_id="run-1", **kw):
    row = {
        "run_id": run_id, "branch": "01", "work_center": "CT-01",
        "run_status": "running", "production_order": "1", "operation_code": "10",
        "operator_code": "OP", "operator_name": None, "pieces_total": 100,
        "target_pieces": 200, "last_count_activity_at": None,
        "run_started_at": NOW - timedelta(minutes=60), "run_ended_at": None,
        "ideal_cycle_seconds_snapshot": 2,
        "standard_time_source": "shy_tempad",
        "standard_time_data_quality_snapshot": "complete",
        "state_id": "s1", "operational_state": "producing",
        "state_started_at": None, "state_source": "system",
        "downtime_id": None, "downtime_started_at": None, "downtime_source": None,
        "reason_code": None, "reason_label": None, "category": None,
        "confirmed": False, "note": None,
    }
    row.update(kw)
    return row


def _fact(run_id, state, start_min_ago, end_min_ago=None):
    return {
        "id": f"{run_id}-{state}-{start_min_ago}", "run_id": run_id,
        "state": state,
        "started_at": NOW - timedelta(minutes=start_min_ago),
        "ended_at": NOW - timedelta(minutes=end_min_ago) if end_min_ago is not None else None,
        "source": "system", "downtime_id": None, "reason_code": None,
        "reason_label": None, "category": None, "confirmed": False,
        "note": None, "downtime_source": None,
    }


def _service(repo, clock=None):
    return MesIntegrationReadService(
        repository=repo, branch_access=BranchAccessService(),
        clock=clock or (lambda: NOW),
    )


def test_live_item_carries_performance_block():
    repo = FakeRepo(rows=[_live_row()], facts=[_fact("run-1", "producing", 3)])
    data = _service(repo).get_live_work_centers(branch="01")
    perf = data["items"][0]["performance"]
    # producing 180s, ciclo 2s, 100 peças → 111.11
    assert perf["producingSeconds"] == 180
    assert perf["producedPieces"] == 100
    assert float(perf["performancePercent"]) == 111.11
    assert float(perf["actualThroughputPerHour"]) == 2000.0
    assert float(perf["expectedThroughputPerHour"]) == 1800.0
    assert perf["dataQuality"] == "complete"
    assert perf["standardTimeSource"] == "shy_tempad"


def test_live_anti_n_plus_one_single_batch_for_many_runs():
    rows = [_live_row(run_id=f"run-{i}") for i in range(10)]
    facts = [_fact(f"run-{i}", "producing", 5) for i in range(10)]
    repo = FakeRepo(rows=rows, facts=facts)
    data = _service(repo).get_live_work_centers(branch="01")
    assert len(data["items"]) == 10
    assert repo.live_calls == 1
    assert repo.batch_calls == 1
    assert repo.batch_run_ids == [f"run-{i}" for i in range(10)]
    assert all(item["performance"]["producingSeconds"] == 300 for item in data["items"])


def test_live_empty_makes_no_batch_query():
    repo = FakeRepo()
    data = _service(repo).get_live_work_centers(branch="01")
    assert data["items"] == []
    assert repo.batch_calls == 0


def test_live_single_reference_at_for_all_runs():
    calls = []

    def clock():
        calls.append(1)
        return NOW

    repo = FakeRepo(
        rows=[_live_row("r1"), _live_row("r2", work_center="CT-02")],
        facts=[_fact("r1", "producing", 2), _fact("r2", "producing", 2)],
    )
    service = MesIntegrationReadService(
        repository=repo, branch_access=BranchAccessService(), clock=clock
    )
    data = service.get_live_work_centers(branch="01")
    assert len(calls) == 1
    assert data["referenceAt"] == NOW.isoformat()


def test_live_paused_run_does_not_accumulate_pause_time():
    repo = FakeRepo(
        rows=[_live_row(run_status="paused")],
        facts=[_fact("run-1", "producing", 30, 20)],  # fechado na pausa
    )
    data = _service(repo).get_live_work_centers(branch="01")
    perf = data["items"][0]["performance"]
    assert perf["producingSeconds"] == 600
    assert float(perf["performancePercent"]) == pytest.approx(33.33)


def test_live_run_without_standard_keeps_nulls_not_absent():
    repo = FakeRepo(
        rows=[_live_row(
            ideal_cycle_seconds_snapshot=None,
            standard_time_source=None,
            standard_time_data_quality_snapshot="standard_time_unavailable",
        )],
        facts=[_fact("run-1", "producing", 5)],
    )
    perf = _service(repo).get_live_work_centers(branch="01")["items"][0]["performance"]
    assert perf["performancePercent"] is None
    assert perf["idealCycleSeconds"] is None
    assert perf["expectedThroughputPerHour"] is None
    assert perf["dataQuality"] == "standard_time_unavailable"
    # métricas reais continuam calculáveis
    assert float(perf["actualThroughputPerHour"]) == 1200.0


def test_live_fresh_run_zero_pieces():
    repo = FakeRepo(
        rows=[_live_row(pieces_total=0)],
        facts=[_fact("run-1", "producing", 1)],
    )
    perf = _service(repo).get_live_work_centers(branch="01")["items"][0]["performance"]
    assert perf["performancePercent"] is None
    assert perf["dataQuality"] == "insufficient_count_data"
    assert float(perf["expectedThroughputPerHour"]) == 1800.0


# ---------------------------------------------------------------------------
# Contrato S2S /integrations/mes/runs/{id}/performance
# ---------------------------------------------------------------------------


class FakePerfService:
    def __init__(self, result=None, exc=None):
        self.result = result
        self.exc = exc
        self.calls = []

    def get_run_performance(self, run_id):
        self.calls.append(run_id)
        if self.exc:
            raise self.exc
        return self.result


def _perf_result(**kw):
    base = {
        "runId": "run-1", "branch": "01", "workCenter": "CT-01",
        "status": "running", "referenceAt": NOW.isoformat(),
        "idealCycleSeconds": 2, "producedPieces": 100, "producingSeconds": 180,
        "idealProductionSeconds": 200, "performancePercent": 111.11,
        "actualAverageCycleSeconds": 1.8, "actualThroughputPerHour": 2000,
        "expectedThroughputPerHour": 1800, "dataQuality": "complete",
        "standardTimeSource": "shy_tempad", "standardTimeDataQuality": "complete",
    }
    base.update(kw)
    return base


def _route_client(monkeypatch, service):
    app = FastAPI()
    app.include_router(integration_mes_routes.router)
    monkeypatch.setattr(
        integration_mes_routes, "build_mes_run_performance_service", lambda: service
    )
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    return TestClient(app)


_S2S = {
    "X-Delpi-Service-Token": "internal-secret",
    "X-Delpi-Caller-App": "delpi-mes-api",
}


def test_performance_route_requires_service_token(monkeypatch):
    api = _route_client(monkeypatch, FakePerfService(result=_perf_result()))
    assert api.get("/integrations/mes/runs/run-1/performance").status_code == 401
    assert api.get(
        "/integrations/mes/runs/run-1/performance",
        headers={"X-Delpi-Service-Token": "wrong"},
    ).status_code == 401
    assert api.get(
        "/integrations/mes/runs/run-1/performance",
        headers={"Authorization": "Bearer human-jwt"},
    ).status_code == 401


def test_performance_route_full_contract(monkeypatch):
    service = FakePerfService(result=_perf_result())
    api = _route_client(monkeypatch, service)
    response = api.get("/integrations/mes/runs/run-1/performance", headers=_S2S)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["runId"] == "run-1"
    assert data["branch"] == "01" and data["workCenter"] == "CT-01"
    assert data["status"] == "running"
    perf = data["performance"]
    assert perf["performancePercent"] == 111.11  # >100% preservado
    assert perf["idealProductionSeconds"] == 200
    assert perf["dataQuality"] == "complete"
    assert perf["standardTimeSource"] == "shy_tempad"
    assert set(perf) == set(integration_mes_routes._PERFORMANCE_FIELDS)


def test_performance_route_preserves_nulls(monkeypatch):
    service = FakePerfService(result=_perf_result(
        idealCycleSeconds=None, idealProductionSeconds=None,
        performancePercent=None, expectedThroughputPerHour=None,
        dataQuality="standard_time_unavailable",
        standardTimeSource=None,
        standardTimeDataQuality="standard_time_unavailable",
    ))
    api = _route_client(monkeypatch, service)
    perf = api.get("/integrations/mes/runs/run-1/performance", headers=_S2S).json()["data"]["performance"]
    assert perf["performancePercent"] is None
    assert perf["dataQuality"] == "standard_time_unavailable"
    assert perf["producedPieces"] == 100


def test_performance_route_404_for_missing_run(monkeypatch):
    service = FakePerfService(exc=ProductionRunNotFound("Produção não encontrada."))
    api = _route_client(monkeypatch, service)
    response = api.get("/integrations/mes/runs/missing/performance", headers=_S2S)
    assert response.status_code == 404
    assert response.json()["success"] is False


# ---------------------------------------------------------------------------
# Postgres — batch e live com dados reais (PC_TEST_MES_DB=1)
# ---------------------------------------------------------------------------

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestLivePerformancePostgres:
    @pytest.fixture()
    def stack(self):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )
        from production_control_app.infrastructure.persistence.postgres_mes_monitoring_read_repository import (  # noqa: E501
            PostgresMesMonitoringReadRepository,
        )
        from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
            PostgresProductionRunRepository,
        )

        wcs = ["ZZ-TEST-LP1", "ZZ-TEST-LP2"]

        def _cleanup():
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.work_center_state_events "
                        "WHERE work_center = ANY(%s)",
                        (wcs,),
                    )
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.production_runs "
                        "WHERE work_center = ANY(%s)",
                        (wcs,),
                    )
                conn.commit()

        _cleanup()
        yield PostgresProductionRunRepository(), PostgresMesMonitoringReadRepository(), wcs
        _cleanup()

    def test_batch_and_live_performance(self, stack):
        runs, monitoring, wcs = stack
        ref = datetime.now(timezone.utc)
        for i, wc in enumerate(wcs, start=1):
            run = runs.create_run_with_segment(
                branch="01", work_center=wc, production_order=f"LP{i}",
                operation_code="10",
                device_id="00000000-0000-4000-8000-0000000000d1",
                operator_code="USR01", operator_name=None, bench_session_id=None,
                planned_qty_snapshot=1.0, target_pieces_snapshot=100,
                anchor_counter=0, anchor_epoch=0,
                ideal_cycle_seconds_snapshot=2,
                standard_time_source="shy_tempad",
                standard_time_data_quality_snapshot="complete",
                pieces_per_pulse_snapshot=1,
            )
            runs.update_run_pieces(run["id"], pieces_total=100, open_segment_pieces=100)
            with __import__("production_control_app.infrastructure.persistence.plugins_postgres_connection", fromlist=["get_connection"]).get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO production_control.work_center_state_events "
                        "(branch, work_center, state, source, run_id, started_at) "
                        "VALUES ('01', %s, 'producing', 'system', %s::uuid, %s)",
                        (wc, run["id"], ref - timedelta(seconds=180)),
                    )
                conn.commit()

        service = MesIntegrationReadService(
            repository=monitoring,
            branch_access=BranchAccessService(),
            clock=lambda: ref,
        )
        data = service.get_live_work_centers(branch="01")
        items = [i for i in data["items"] if i["workCenter"] in wcs]
        assert len(items) == 2
        for item in items:
            perf = item["performance"]
            assert perf["producingSeconds"] == 180
            assert float(perf["performancePercent"]) == 111.11
            assert perf["dataQuality"] == "complete"
