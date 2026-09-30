"""Fase 2.4 — motor interno de Performance do Production Run.

Performance = (ideal_cycle x pieces_total) / producing_seconds x 100.
Somente leitura derivada: sem TOTVS, sem Pulse, sem persistência.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.application.services.mes_run_performance_service import (
    MesRunPerformanceService,
)
from production_control_app.application.services.mes_timeline_builder import (
    MesTimelineBuilder,
)
from production_control_app.domain.errors import ProductionRunNotFound
from production_control_app.domain.services.mes_performance import (
    MesPerformanceCalculator,
)

REF = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)


def _run(**kwargs):
    base = {
        "id": "run-1",
        "branch": "01",
        "work_center": "CT01",
        "status": "running",
        "started_at": REF - timedelta(minutes=30),
        "ended_at": None,
        "pieces_total": 0,
        "ideal_cycle_seconds_snapshot": None,
        "setup_seconds_snapshot": None,
        "standard_time_source": None,
        "standard_time_data_quality_snapshot": None,
        "pieces_per_pulse_snapshot": 1,
    }
    base.update(kwargs)
    return base


def _event(state, start_min_ago, end_min_ago=None, **kw):
    ev = {
        "id": kw.get("id", f"ev-{state}-{start_min_ago}"),
        "state": state,
        "started_at": REF - timedelta(minutes=start_min_ago),
        "ended_at": (
            REF - timedelta(minutes=end_min_ago) if end_min_ago is not None else None
        ),
        "source": "system",
        "downtime": None,
    }
    return ev


class FakeMonitoringRepo:
    """Apenas leitura — não possui métodos de escrita por design."""

    def __init__(self, run=None, events=None):
        self.run = run
        self.events = events or []
        self.get_run_calls = 0
        self.facts_calls = 0

    def get_run(self, run_id):
        self.get_run_calls += 1
        return dict(self.run) if self.run and self.run["id"] == run_id else None

    def list_timeline_facts(self, run_id):
        self.facts_calls += 1
        return [dict(e) for e in self.events]


def _service(repo, clock=None):
    return MesRunPerformanceService(
        repository=repo, clock=clock or (lambda: REF)
    )


# ---------------------------------------------------------------------------
# Calculator puro
# ---------------------------------------------------------------------------


def test_calculator_normal_case():
    calc = MesPerformanceCalculator()
    result = calc.calculate(
        ideal_cycle_seconds="1.8",
        produced_pieces=1000,
        producing_seconds=2100,
        standard_time_data_quality="complete",
    )
    assert float(result["idealProductionSeconds"]) == 1800.0
    assert float(result["performancePercent"]) == 85.71
    assert float(result["actualAverageCycleSeconds"]) == 2.1
    assert float(result["actualThroughputPerHour"]) == pytest.approx(1714.285714, abs=1e-4)
    assert float(result["expectedThroughputPerHour"]) == 2000.0
    assert result["dataQuality"] == "complete"


def test_calculator_performance_above_100_not_capped():
    calc = MesPerformanceCalculator()
    result = calc.calculate(
        ideal_cycle_seconds=2,
        produced_pieces=100,
        producing_seconds=180,
        standard_time_data_quality="complete",
    )
    assert float(result["performancePercent"]) == 111.11


def test_calculator_zero_pieces_is_not_zero_percent():
    calc = MesPerformanceCalculator()
    result = calc.calculate(
        ideal_cycle_seconds=1.8,
        produced_pieces=0,
        producing_seconds=120,
        standard_time_data_quality="complete",
    )
    assert result["performancePercent"] is None
    assert result["actualAverageCycleSeconds"] is None
    assert result["actualThroughputPerHour"] is None
    assert float(result["expectedThroughputPerHour"]) == 2000.0
    assert float(result["idealProductionSeconds"]) == 0.0
    assert result["dataQuality"] == "insufficient_count_data"


def test_calculator_zero_producing_is_not_zero_percent():
    calc = MesPerformanceCalculator()
    result = calc.calculate(
        ideal_cycle_seconds=1.8,
        produced_pieces=50,
        producing_seconds=0,
        standard_time_data_quality="complete",
    )
    assert result["performancePercent"] is None
    assert result["actualAverageCycleSeconds"] is None
    assert result["actualThroughputPerHour"] is None
    assert result["dataQuality"] == "insufficient_producing_time"
    assert float(result["idealProductionSeconds"]) == 90.0


@pytest.mark.parametrize(
    "quality",
    ["standard_time_unavailable", "piece_conversion_unavailable", "upstream_unavailable"],
)
def test_calculator_unavailable_standard_keeps_real_metrics_only(quality):
    calc = MesPerformanceCalculator()
    result = calc.calculate(
        ideal_cycle_seconds=None,
        produced_pieces=40,
        producing_seconds=100,
        standard_time_data_quality=quality,
    )
    assert result["dataQuality"] == quality
    assert result["performancePercent"] is None
    assert result["idealProductionSeconds"] is None
    assert result["expectedThroughputPerHour"] is None
    # métricas reais não dependem do tempo padrão
    assert float(result["actualAverageCycleSeconds"]) == 2.5
    assert float(result["actualThroughputPerHour"]) == 1440.0


def test_calculator_invalid_snapshot_degrades_quality():
    calc = MesPerformanceCalculator()
    result = calc.calculate(
        ideal_cycle_seconds=0,
        produced_pieces=40,
        producing_seconds=100,
        standard_time_data_quality="complete",
    )
    assert result["dataQuality"] == "invalid_standard_time_snapshot"
    assert result["performancePercent"] is None
    assert result["expectedThroughputPerHour"] is None


def test_calculator_none_quality_treated_as_unavailable():
    calc = MesPerformanceCalculator()
    result = calc.calculate(
        ideal_cycle_seconds=None,
        produced_pieces=10,
        producing_seconds=50,
        standard_time_data_quality=None,
    )
    assert result["dataQuality"] == "standard_time_unavailable"


# ---------------------------------------------------------------------------
# Timeline builder — run encerrado congela producing
# ---------------------------------------------------------------------------


def test_builder_caps_open_event_at_run_ended_at():
    builder = MesTimelineBuilder()
    run = _run(status="completed", ended_at=REF - timedelta(minutes=10))
    events = [_event("producing", 60)]  # ainda aberto por inconsistência
    timeline = builder.build(run=run, events=events, reference_at=REF)
    # 60 min atrás até ended_at (10 min atrás) = 50 min, nunca até REF
    assert timeline["summary"]["producingSeconds"] == 3000


def test_builder_active_run_open_producing_uses_reference():
    builder = MesTimelineBuilder()
    run = _run(status="running")
    events = [_event("producing", 5)]
    timeline = builder.build(run=run, events=events, reference_at=REF)
    assert timeline["summary"]["producingSeconds"] == 300


# ---------------------------------------------------------------------------
# Service — caminhos
# ---------------------------------------------------------------------------


def test_service_run_not_found():
    repo = FakeMonitoringRepo(run=None)
    with pytest.raises(ProductionRunNotFound):
        _service(repo).get_run_performance("missing")


def test_service_only_producing_counts_in_denominator():
    run = _run(
        pieces_total=100,
        ideal_cycle_seconds_snapshot=1.8,
        standard_time_data_quality_snapshot="complete",
        standard_time_source="shy_tempad",
    )
    events = [
        _event("producing", 40, 30, id="p1"),   # 600 s
        _event("stopped", 30, 20, id="s1"),     # fora
        _event("producing", 20, 10, id="p2"),   # 600 s
        _event("setup", 10, 5, id="se1"),       # fora
        _event("planned_stop", 5, 0, id="ps1"), # fora
    ]
    repo = FakeMonitoringRepo(run=run, events=events)
    result = _service(repo).get_run_performance("run-1")
    assert result["producingSeconds"] == 1200
    assert float(result["performancePercent"]) == pytest.approx(15.0)
    assert result["dataQuality"] == "complete"


def test_service_correction_reflected_via_pieces_total():
    # +100 production -5 correction => pieces_total=95 (canônico)
    run = _run(
        pieces_total=95,
        ideal_cycle_seconds_snapshot=1.8,
        standard_time_data_quality_snapshot="complete",
    )
    events = [_event("producing", 30)]  # 1800 s abertos
    repo = FakeMonitoringRepo(run=run, events=events)
    result = _service(repo).get_run_performance("run-1")
    assert result["producedPieces"] == 95
    assert float(result["idealProductionSeconds"]) == 171.0
    assert float(result["performancePercent"]) == pytest.approx(9.5)


def test_service_paused_run_excludes_pause_time():
    # producing 20..10 min atrás; run pausado (sem producing aberto)
    run = _run(
        status="paused",
        pieces_total=50,
        ideal_cycle_seconds_snapshot=1.8,
        standard_time_data_quality_snapshot="complete",
    )
    events = [_event("producing", 20, 10)]
    repo = FakeMonitoringRepo(run=run, events=events)
    result = _service(repo).get_run_performance("run-1")
    assert result["producingSeconds"] == 600
    assert float(result["performancePercent"]) == pytest.approx(15.0)


def test_service_completed_run_frozen_at_ended_at():
    run = _run(
        status="completed",
        ended_at=REF - timedelta(minutes=10),
        pieces_total=100,
        ideal_cycle_seconds_snapshot=2,
        standard_time_data_quality_snapshot="complete",
    )
    # evento producing aberto indevidamente: trava em ended_at
    events = [_event("producing", 30)]
    repo = FakeMonitoringRepo(run=run, events=events)
    result = _service(repo).get_run_performance("run-1")
    assert result["producingSeconds"] == 1200  # 30→10 min atrás
    assert float(result["performancePercent"]) == pytest.approx(16.67)


def test_service_empty_timeline_no_fictitious_production():
    run = _run(
        pieces_total=10,
        ideal_cycle_seconds_snapshot=1.8,
        standard_time_data_quality_snapshot="complete",
    )
    repo = FakeMonitoringRepo(run=run, events=[])
    result = _service(repo).get_run_performance("run-1")
    assert result["producingSeconds"] == 0
    assert result["dataQuality"] == "insufficient_producing_time"
    assert result["performancePercent"] is None


def test_service_fresh_run_zero_pieces():
    run = _run(
        pieces_total=0,
        ideal_cycle_seconds_snapshot=1.8,
        standard_time_data_quality_snapshot="complete",
    )
    events = [_event("producing", 1)]
    repo = FakeMonitoringRepo(run=run, events=events)
    result = _service(repo).get_run_performance("run-1")
    assert result["performancePercent"] is None
    assert result["dataQuality"] == "insufficient_count_data"
    assert float(result["expectedThroughputPerHour"]) == 2000.0


def test_service_single_reference_at_and_no_external_calls():
    calls = []

    def clock():
        calls.append(1)
        return REF

    run = _run(
        pieces_total=10,
        ideal_cycle_seconds_snapshot=1.8,
        standard_time_data_quality_snapshot="complete",
        standard_time_source="sg2_tempad",
    )
    repo = FakeMonitoringRepo(run=run, events=[_event("producing", 10)])
    service = MesRunPerformanceService(
        repository=repo, clock=clock, timeline_builder=MesTimelineBuilder()
    )
    result = service.get_run_performance("run-1")
    assert len(calls) == 1
    assert result["referenceAt"] == REF.isoformat()
    assert result["producingSeconds"] == 600
    assert result["standardTimeSource"] == "sg2_tempad"
    # leitura pura: repo só expõe os dois reads
    assert repo.get_run_calls == 1 and repo.facts_calls == 1


# ---------------------------------------------------------------------------
# Integração Postgres — PC_TEST_MES_DB=1
# ---------------------------------------------------------------------------

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestRunPerformancePostgres:
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

        wc = "ZZ-TEST-PERF"
        runs = PostgresProductionRunRepository()

        def _cleanup():
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.work_center_state_events "
                        "WHERE work_center = %s",
                        (wc,),
                    )
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.production_runs WHERE work_center = %s",
                        (wc,),
                    )
                conn.commit()

        _cleanup()
        yield runs, PostgresMesMonitoringReadRepository(), PC_SCHEMA_NAME, get_connection
        _cleanup()
        _cleanup()

    def test_smoke_performance_above_100(self, stack):
        runs, monitoring, schema, get_connection = stack
        run = runs.create_run_with_segment(
            branch="01",
            work_center="ZZ-TEST-PERF",
            production_order="OPPERF",
            operation_code="10",
            device_id="00000000-0000-4000-8000-0000000000d1",
            operator_code="USR01",
            operator_name=None,
            bench_session_id=None,
            planned_qty_snapshot=1.0,
            target_pieces_snapshot=200,
            anchor_counter=0,
            anchor_epoch=0,
            ideal_cycle_seconds_snapshot=2,
            standard_time_source="shy_tempad",
            standard_time_data_quality_snapshot="complete",
            pieces_per_pulse_snapshot=1,
        )
        # 100 peças + 180 s de producing fechado
        runs.update_run_pieces(run["id"], pieces_total=100, open_segment_pieces=100)
        ref = datetime.now(timezone.utc)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {schema}.work_center_state_events (
                        branch, work_center, state, source, run_id,
                        started_at, ended_at
                    )
                    VALUES ('01', 'ZZ-TEST-PERF', 'producing', 'system',
                            %s::uuid, %s, %s)
                    """,
                    (
                        run["id"],
                        ref - timedelta(seconds=180),
                        ref,
                    ),
                )
            conn.commit()

        service = MesRunPerformanceService(
            repository=monitoring, clock=lambda: ref
        )
        result = service.get_run_performance(run["id"])
        assert float(result["idealProductionSeconds"]) == 200.0
        assert float(result["performancePercent"]) == 111.11
        assert float(result["actualAverageCycleSeconds"]) == 1.8
        assert float(result["actualThroughputPerHour"]) == 2000.0
        assert float(result["expectedThroughputPerHour"]) == 1800.0
        assert result["dataQuality"] == "complete"
