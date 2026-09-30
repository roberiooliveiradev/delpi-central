"""Threshold dinâmico de auto-downtime (Fase 2 — Parte 2.7).

Resolver puro (fallback conservador, kill switch, ceil no candidato) +
integração no _tick_idle com relógio injetável: dinâmico só para
manual_workstation + qualidade complete + ciclo válido.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from production_control_app.application.services.mes_run_lifecycle_service import (
    MesRunLifecycleService,
)
from production_control_app.application.services.production_run_service import (
    ProductionRunService,
)
from production_control_app.domain.services.mes_auto_downtime_threshold import (
    resolve_auto_downtime_threshold,
)

from tests.test_mes_auto_downtime import FakeAudit, FakeClock, _start, _sync_clock
from tests.test_production_run_service import (
    FakeDowntimeRepo,
    FakePulse,
    FakeReasonRepo,
    FakeRepo,
    FakeStateRepo,
    service_session,
)

BASE = dict(
    legacy_seconds=120,
    dynamic_enabled=True,
    minimum_seconds=120,
    manual_cycle_multiplier=3.0,
)
MANUAL = dict(
    workstation_type="manual_workstation",
    standard_time_data_quality="complete",
)


def _resolve(**overrides):
    kwargs = {
        **BASE,
        "ideal_cycle_seconds": 60,
        **MANUAL,
        **overrides,
    }
    return resolve_auto_downtime_threshold(**kwargs)


# --- resolver puro -------------------------------------------------------

def test_flag_off_keeps_legacy():
    r = _resolve(dynamic_enabled=False)
    assert r.seconds == 120
    assert r.source == "legacy_dynamic_disabled"
    assert r.dynamic is False


def test_kill_switch_is_sovereign():
    r = _resolve(legacy_seconds=0)
    assert r.seconds == 0
    assert r.source == "disabled"


def test_manual_short_cycle_stays_on_minimum():
    r = _resolve(ideal_cycle_seconds=10)
    assert r.seconds == 120
    assert r.source == "dynamic_manual_cycle"


def test_manual_long_cycle_raises_threshold():
    r = _resolve(ideal_cycle_seconds=60)
    assert r.seconds == 180
    assert r.source == "dynamic_manual_cycle"
    assert r.dynamic is True


def test_decimal_cycle_uses_ceil_before_minimum():
    r = _resolve(ideal_cycle_seconds=40.1)  # 40.1 × 3 = 120.3 → 121
    assert r.seconds == 121
    assert r.source == "dynamic_manual_cycle"


def test_unknown_workstation_falls_back():
    assert _resolve(workstation_type=None).seconds == 120
    assert _resolve(workstation_type=None).source == "legacy_unknown_workstation"
    assert _resolve(workstation_type="automatic_workstation").seconds == 120


def test_degraded_standard_time_falls_back():
    for quality in ("standard_time_unavailable", "upstream_unavailable",
                    "piece_conversion_unavailable", "invalid_standard_time_snapshot"):
        r = _resolve(standard_time_data_quality=quality)
        assert r.seconds == 120
        assert r.source == "legacy_standard_time_unavailable"


def test_missing_or_invalid_cycle_falls_back():
    assert _resolve(ideal_cycle_seconds=None).source == "legacy_invalid_standard_time"
    assert _resolve(ideal_cycle_seconds=0).source == "legacy_invalid_standard_time"
    assert _resolve(ideal_cycle_seconds=-5).source == "legacy_invalid_standard_time"
    assert _resolve(ideal_cycle_seconds=float("nan")).source == "legacy_invalid_standard_time"


def test_invalid_config_falls_back():
    assert _resolve(manual_cycle_multiplier=0).source == "legacy_invalid_config"
    assert _resolve(manual_cycle_multiplier=-1).source == "legacy_invalid_config"
    assert _resolve(minimum_seconds=-5).source == "legacy_invalid_config"
    assert _resolve(manual_cycle_multiplier=0).seconds == 120


# --- integração no tick --------------------------------------------------

def _setup_dyn(
    *,
    legacy: int = 120,
    minimum: int = 120,
    multiplier: float = 3.0,
    enabled: bool = True,
):
    repo = FakeRepo()
    session = service_session(repo)
    device = {
        "deviceId": "dev-1", "counter": 100, "counterEpoch": 1,
        "online": True, "status": "online",
    }
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    states, downtimes = FakeStateRepo(), FakeDowntimeRepo()
    lifecycle = MesRunLifecycleService(
        states=states, downtimes=downtimes,
        reasons=FakeReasonRepo(), run_lookup=repo.get_run,
    )
    clock, audit = FakeClock(), FakeAudit()
    service = ProductionRunService(
        repository=repo, pulse_gateway=pulse, mes_lifecycle=lifecycle,
        audit=audit, clock=clock,
        auto_downtime_seconds=legacy,
        dynamic_auto_downtime_enabled=enabled,
        auto_downtime_min_seconds=minimum,
        auto_downtime_manual_cycle_multiplier=multiplier,
    )
    return service, states, downtimes, repo, pulse, clock, session, audit


def _snapshot(repo, run_id, *, cycle=60, quality="complete",
              workstation="manual_workstation"):
    run = repo.runs[run_id]
    run["ideal_cycle_seconds_snapshot"] = cycle
    run["standard_time_data_quality_snapshot"] = quality
    run["workstation_type_snapshot"] = workstation


def test_dynamic_threshold_holds_short_cycle_run_running():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup_dyn()
    run = _start(service, session)
    _snapshot(repo, run["id"], cycle=60)
    _sync_clock(clock, repo, run["id"])
    clock.advance(121)  # > legado 120, < dinâmico 180
    service.tick_running_runs()
    assert downtimes.events == []
    assert states.events[-1]["state"] == "producing"
    clock.advance(60)  # 181 s totais ≥ 180
    service.tick_running_runs()
    assert len(downtimes.events) == 1
    assert states.events[-1]["state"] == "stopped"


def test_dynamic_audit_records_resolution():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup_dyn()
    run = _start(service, session)
    _snapshot(repo, run["id"], cycle=60)
    _sync_clock(clock, repo, run["id"])
    clock.advance(181)
    service.tick_running_runs()
    evt = next(e for e in audit.events if e.get("action") == "automatic_downtime_started")
    d = evt.get("details", {})
    assert d["thresholdSeconds"] == 180
    assert d["thresholdSource"] == "dynamic_manual_cycle"
    assert d["dynamicThresholdEnabled"] is True
    assert d["idealCycleSeconds"] == 60
    assert d["workstationType"] == "manual_workstation"
    assert d["cycleMultiplier"] == 3.0
    assert d["minimumThresholdSeconds"] == 120


def test_unknown_workstation_uses_legacy_despite_long_cycle():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup_dyn()
    run = _start(service, session)
    _snapshot(repo, run["id"], cycle=60, workstation=None)
    _sync_clock(clock, repo, run["id"])
    clock.advance(121)
    service.tick_running_runs()
    assert len(downtimes.events) == 1  # legado 120 — não esperou 180


def test_degraded_quality_uses_legacy():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup_dyn()
    run = _start(service, session)
    _snapshot(repo, run["id"], cycle=60, quality="upstream_unavailable")
    _sync_clock(clock, repo, run["id"])
    clock.advance(121)
    service.tick_running_runs()
    assert len(downtimes.events) == 1
    evt = [e for e in audit.events if e.get("action") == "automatic_downtime_started"][-1]
    assert evt["details"]["thresholdSource"] == "legacy_standard_time_unavailable"
    assert evt["details"]["thresholdSeconds"] == 120


def test_kill_switch_overrides_dynamic():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup_dyn(legacy=0)
    run = _start(service, session)
    _snapshot(repo, run["id"], cycle=60)
    _sync_clock(clock, repo, run["id"])
    clock.advance(600)
    for _ in range(3):
        service.tick_running_runs()
    assert downtimes.events == []


def test_flag_off_ignores_long_cycle():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup_dyn(enabled=False)
    run = _start(service, session)
    _snapshot(repo, run["id"], cycle=60)
    _sync_clock(clock, repo, run["id"])
    clock.advance(121)
    service.tick_running_runs()
    assert len(downtimes.events) == 1


def test_boundary_idle_below_dynamic_threshold():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup_dyn()
    run = _start(service, session)
    _snapshot(repo, run["id"], cycle=60)
    _sync_clock(clock, repo, run["id"])
    clock.advance(179.999)
    service.tick_running_runs()
    assert downtimes.events == []
    clock.advance(0.001)  # exatamente 180
    service.tick_running_runs()
    assert len(downtimes.events) == 1
    # idempotente: ticks extras não criam nada
    clock.advance(300)
    for _ in range(3):
        service.tick_running_runs()
    assert len(downtimes.events) == 1


def test_auto_resume_still_works_with_dynamic_threshold():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup_dyn()
    run = _start(service, session)
    _snapshot(repo, run["id"], cycle=60)
    _sync_clock(clock, repo, run["id"])
    clock.advance(181)
    service.tick_running_runs()
    assert len(downtimes.events) == 1

    resumed_at = clock.now
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1", "counter": 105, "counterEpoch": 1,
        "online": True, "status": "online",
    }
    service.tick_running_runs()
    assert downtimes.events[0]["ended_at"] == resumed_at
    assert states.events[-1]["state"] == "producing"
    assert repo.runs[run["id"]]["last_count_activity_at"] == resumed_at


def test_correction_does_not_close_dynamic_downtime():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup_dyn()
    run = _start(service, session)
    _snapshot(repo, run["id"], cycle=60)
    _sync_clock(clock, repo, run["id"])
    clock.advance(181)
    service.tick_running_runs()
    assert len(downtimes.events) == 1
    baseline = repo.runs[run["id"]]["last_count_activity_at"]

    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1", "counter": 95, "counterEpoch": 1,
        "online": True, "status": "online",
    }
    service.tick_running_runs()
    assert downtimes.events[0]["ended_at"] is None
    assert repo.runs[run["id"]]["last_count_activity_at"] == baseline
    assert states.events[-1]["state"] == "stopped"


def test_offline_pulse_never_opens_downtime_even_dynamic():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup_dyn()
    run = _start(service, session)
    _snapshot(repo, run["id"], cycle=60)
    _sync_clock(clock, repo, run["id"])
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1", "counter": None, "counterEpoch": None,
        "online": False, "status": "offline",
    }
    clock.advance(600)
    for _ in range(3):
        service.tick_running_runs()
    assert downtimes.events == []
