"""Monitoramento autônomo de CT sem OP (PC-MES-CT-AUTONOMOUS-DOWNTIME).

Cobre o ciclo completo do observador: baseline, atividade sem run,
parada com run_id=NULL após threshold, retomada automática, arbitragem
com Play/Stop, epoch/device change, telemetria degradada e classificação
por identidade do downtime — tudo com fakes e relógio injetável.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.application.services.mes_autonomous_monitor_service import (
    MesAutonomousMonitorService,
)
from production_control_app.application.services.mes_downtime_classification_service import (
    MesDowntimeClassificationService,
)
from production_control_app.domain.errors import (
    BenchSessionRequired,
    PulseGatewayError,
)

from tests.test_mes_auto_downtime import FakeAudit
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

THRESHOLD = 120
BASE = datetime(2026, 1, 15, 8, 0, 0, tzinfo=timezone.utc)


class FakeConn:
    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class FakeObserverRepo:
    """Cursor durável do observador em memória (mesmo shape do Postgres)."""

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict] = {}
        self.lock_granted = True

    def try_lock_work_center(self, *, branch, work_center, conn):
        return self.lock_granted

    def lock_work_center(self, *, branch, work_center, conn=None):
        pass

    def get(self, *, branch, work_center, conn=None):
        row = self.rows.get((branch, work_center))
        return dict(row) if row else None

    def upsert(
        self,
        *,
        branch,
        work_center,
        device_id,
        counter_epoch,
        last_counter,
        last_increment_at,
        baseline_established_at,
        device_online,
        degraded_reason,
        last_seen_at,
        conn=None,
    ):
        row = {
            "branch": branch,
            "work_center": work_center,
            "device_id": device_id,
            "counter_epoch": counter_epoch,
            "last_counter": last_counter,
            "last_increment_at": last_increment_at,
            "baseline_established_at": baseline_established_at,
            "device_online": device_online,
            "degraded_reason": degraded_reason,
            "last_seen_at": last_seen_at,
        }
        self.rows[(branch, work_center)] = row
        return dict(row)


def _device(counter=100, epoch=1, device_id="dev-1", **over):
    return {
        "deviceId": device_id,
        "workCenterCode": "CT01",
        "counter": counter,
        "counterEpoch": epoch,
        "online": True,
        "status": "online",
        **over,
    }


class _Clock:
    def __init__(self, at: datetime):
        self.at = at

    def __call__(self) -> datetime:
        return self.at


def _monitor(
    *,
    repo=None,
    pulse=None,
    observers=None,
    states=None,
    downtimes=None,
    audit=None,
    clock=None,
    enabled=True,
    allowlist="",
    threshold=THRESHOLD,
):
    from production_control_app.application.services.mes_run_lifecycle_service import (
        MesRunLifecycleService,
    )

    repo = repo or FakeRepo()
    pulse = pulse or FakePulse(devices=[_device()])
    observers = observers or FakeObserverRepo()
    if states is None or downtimes is None:
        mes, states, downtimes = make_mes()
    else:
        mes = MesRunLifecycleService(states=states, downtimes=downtimes)
    clock = clock or _Clock(BASE)
    service = MesAutonomousMonitorService(
        pulse_gateway=pulse,
        run_repository=repo,
        observer_repository=observers,
        mes_lifecycle=mes,
        audit_repository=audit,
        connection_factory=lambda: FakeConn(),
        enabled=enabled,
        work_centers_allowlist=allowlist,
        auto_downtime_seconds=threshold,
        clock=clock,
    )
    return service, repo, pulse, observers, states, downtimes, clock


def _open_states(states, wc="CT01"):
    return [
        e
        for e in states.events
        if e["work_center"] == wc and e["ended_at"] is None
    ]


def _open_downtimes(downtimes, wc="CT01"):
    return [
        e
        for e in downtimes.events
        if e["work_center"] == wc and e["ended_at"] is None
    ]


# ---------- Baseline / observação ----------


def test_first_observation_creates_cursor_only():
    service, repo, pulse, observers, states, downtimes, _ = _monitor()
    assert service.tick_all() == 0
    observer = observers.get(branch="01", work_center="CT01")
    assert observer is not None
    assert observer["last_counter"] == 100
    assert observer["last_increment_at"] is None
    assert states.events == []
    assert downtimes.events == []


def test_disabled_flag_is_noop():
    service, _, _, observers, states, downtimes, _ = _monitor(enabled=False)
    assert service.tick_all() == 0
    assert observers.rows == {}
    assert states.events == []


def test_allowlist_limits_monitoring():
    service, _, _, observers, states, downtimes, _ = _monitor(
        allowlist="01:OUTRO"
    )
    assert service.tick_all() == 0
    assert observers.rows == {}


# ---------- Atividade sem OP (AC-01) ----------


def test_increment_opens_autonomous_producing():
    service, _, pulse, observers, states, downtimes, clock = _monitor()
    service.tick_all()  # baseline
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    assert service.tick_all() == 1

    states_open = _open_states(states)
    assert len(states_open) == 1
    assert states_open[0]["state"] == "producing"
    assert states_open[0]["run_id"] is None
    observer = observers.get(branch="01", work_center="CT01")
    assert observer["last_increment_at"] == clock.at


def test_continuous_increments_preserve_single_producing_period():
    """Produção contínua (~1h, múltiplos pulsos): um único producing
    aberto, mesmo id e started_at — sem fragmentação por incremento."""
    audit = FakeAudit()
    service, _, pulse, observers, states, downtimes, clock = _monitor(
        audit=audit
    )
    service.tick_all()  # baseline
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    assert service.tick_all() == 1
    open_first = _open_states(states)[0]
    first_id = open_first["id"]
    first_started = open_first["started_at"]

    # 12 incrementos a cada 5 min (~1h) — limiar de parada nunca atingido.
    for i in range(2, 14):
        pulse.devices = [_device(counter=100 + i)]
        clock.at = BASE + timedelta(minutes=5 * (i - 1))
        assert service.tick_all() == 0  # cursor avança; fato operacional intacto
        open_now = _open_states(states)
        assert len(open_now) == 1
        assert open_now[0]["id"] == first_id
        assert open_now[0]["started_at"] == first_started
        assert open_now[0]["state"] == "producing"
        assert open_now[0]["run_id"] is None
        assert open_now[0]["ended_at"] is None

    assert len([e for e in states.events if e["state"] == "producing"]) == 1
    assert downtimes.events == []
    started_audits = [
        a for a in audit.events if a["action"] == "autonomous_producing_started"
    ]
    assert len(started_audits) == 1
    observer = observers.get(branch="01", work_center="CT01")
    assert observer["last_counter"] == 113
    assert observer["last_increment_at"] == clock.at


def test_activity_while_already_producing_is_idempotent_on_lifecycle():
    """Irmão: record_autonomous_resumed sem parada aberta não muta estado;
    producing idempotente preserva o evento."""
    mes, states, _downtimes = make_mes()
    conn = FakeConn()
    at0 = BASE
    opened = mes.record_autonomous_producing(
        branch="01", work_center="CT01", conn=conn, at=at0
    )
    assert opened is not None
    assert mes.record_autonomous_resumed(
        branch="01", work_center="CT01", conn=conn, at=at0 + timedelta(seconds=10)
    ) is None
    assert mes.record_autonomous_producing(
        branch="01", work_center="CT01", conn=conn, at=at0 + timedelta(seconds=10)
    ) is None
    open_now = _open_states(states)[0]
    assert open_now["id"] == opened["id"]
    assert open_now["started_at"] == at0
    assert len(states.events) == 1


# ---------- Parada autônoma (AC-02) ----------


def test_inactivity_past_threshold_opens_downtime_without_run():
    service, _, pulse, observers, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()  # producing

    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 1)
    assert service.tick_all() == 1

    states_open = _open_states(states)
    assert len(states_open) == 1
    assert states_open[0]["state"] == "stopped"
    assert states_open[0]["run_id"] is None
    dts = _open_downtimes(downtimes)
    assert len(dts) == 1
    assert dts[0]["run_id"] is None
    assert dts[0]["production_order"] is None
    assert dts[0]["source"] == "system"
    # A parada retroage ao último incremento observado.
    assert dts[0]["started_at"] == BASE + timedelta(seconds=5)


def test_below_threshold_no_downtime():
    service, _, pulse, _, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD - 1)
    assert service.tick_all() == 0
    assert _open_downtimes(downtimes) == []


def test_stopped_tick_is_idempotent():
    service, _, pulse, _, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 1)
    service.tick_all()
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 60)
    assert service.tick_all() == 0
    assert len(_open_downtimes(downtimes)) == 1
    assert len(_open_states(states)) == 1


# ---------- Retomada (AC-03) ----------


def test_returning_counter_closes_downtime_without_duplication():
    service, _, pulse, _, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 1)
    service.tick_all()  # parada aberta

    pulse.devices = [_device(counter=105)]
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 30)
    assert service.tick_all() == 1

    assert _open_downtimes(downtimes) == []
    assert len(downtimes.events) == 1  # linha única, encerrada
    assert downtimes.events[0]["ended_at"] == clock.at
    states_open = _open_states(states)
    assert len(states_open) == 1
    assert states_open[0]["state"] == "producing"
    assert states_open[0]["run_id"] is None


def test_produce_stop_resume_creates_distinct_producing_periods():
    """Negativo do contínuo: produce → stop → resume gera dois producing
    distintos; só a retomada após parada fecha/abre estado."""
    audit = FakeAudit()
    service, _, pulse, _, states, downtimes, clock = _monitor(audit=audit)
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()
    first = _open_states(states)[0]

    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 1)
    service.tick_all()
    assert _open_states(states)[0]["state"] == "stopped"

    pulse.devices = [_device(counter=110)]
    resume_at = BASE + timedelta(seconds=5 + THRESHOLD + 40)
    clock.at = resume_at
    assert service.tick_all() == 1
    second = _open_states(states)[0]
    assert second["state"] == "producing"
    assert second["id"] != first["id"]
    assert second["started_at"] == resume_at
    assert first["ended_at"] is not None
    producing = [e for e in states.events if e["state"] == "producing"]
    assert len(producing) == 2
    ended = [a for a in audit.events if a["action"] == "automatic_downtime_ended"]
    assert len(ended) == 1


# ---------- Baseline/epoch/dispositivo (AC-09, AC-10) ----------


def test_no_initial_increment_never_creates_retroactive_downtime():
    service, _, _, observers, states, downtimes, clock = _monitor()
    for i in range(10):
        clock.at = BASE + timedelta(seconds=30 * i)
        assert service.tick_all() == 0
    assert states.events == []
    assert downtimes.events == []


def test_offline_snapshot_never_creates_downtime():
    service, _, pulse, observers, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()  # producing
    pulse.devices = [_device(counter=101, online=False)]
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 999)
    assert service.tick_all() == 0
    assert _open_downtimes(downtimes) == []
    observer = observers.get(branch="01", work_center="CT01")
    assert observer["degraded_reason"] == "offline"


def test_ambiguous_binding_fails_closed():
    service, _, pulse, _, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [
        _device(counter=101),
        _device(counter=50, device_id="dev-2"),
    ]
    clock.at = BASE + timedelta(days=1)
    assert service.tick_all() == 0
    assert states.events == []
    assert downtimes.events == []


def test_invalid_snapshot_is_degraded_not_stopped():
    service, _, pulse, observers, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()
    pulse.devices = [_device(counter=None)]
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 999)
    assert service.tick_all() == 0
    assert _open_downtimes(downtimes) == []


def test_epoch_change_reanchors_without_retroactive_downtime():
    service, _, pulse, observers, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()
    pulse.devices = [_device(counter=3, epoch=2)]
    clock.at = BASE + timedelta(seconds=10)
    assert service.tick_all() == 0  # realinha cursor
    observer = observers.get(branch="01", work_center="CT01")
    assert observer["counter_epoch"] == 2
    assert observer["last_counter"] == 3
    assert observer["last_increment_at"] is None
    clock.at = BASE + timedelta(days=1)
    assert service.tick_all() == 0  # baseline zerado → nada retroativo
    assert _open_downtimes(downtimes) == []


def test_pulse_unavailable_records_nothing():
    pulse = FakePulse(devices=[_device()])
    pulse.branch_error = PulseGatewayError("timeout")
    service, _, _, observers, states, downtimes, _ = _monitor(pulse=pulse)
    assert service.tick_all() == 0
    assert observers.rows == {}
    assert states.events == []


# ---------- Reconexão pós-degradação (rework: sem parada retroativa) ----------


def test_reconnect_with_unchanged_counter_never_covers_telemetry_gap():
    """Incremento → offline > threshold → online inalterado: nenhuma
    parada retroativa cobre o período sem telemetria confiável."""
    service, _, pulse, observers, states, downtimes, clock = _monitor()
    service.tick_all()  # baseline
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()  # producing — last_increment_at = BASE+5

    # Gap de telemetria: muito além do threshold, tudo degradado.
    pulse.devices = [_device(counter=101, online=False)]
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 999)
    assert service.tick_all() == 0
    assert _open_downtimes(downtimes) == []

    # Retorno online com contador inalterado: só reancora o cursor.
    reconnect = clock.at + timedelta(seconds=1)
    pulse.devices = [_device(counter=101)]
    clock.at = reconnect
    assert service.tick_all() == 0
    assert _open_downtimes(downtimes) == []
    observer = observers.get(branch="01", work_center="CT01")
    assert observer["degraded_reason"] is None
    # A referência de inatividade reancora no retorno — nunca no
    # incremento anterior ao gap.
    assert observer["last_increment_at"] == reconnect

    # A parada só pode abrir a partir do novo baseline confiável.
    clock.at = reconnect + timedelta(seconds=THRESHOLD + 1)
    assert service.tick_all() == 1
    dts = _open_downtimes(downtimes)
    assert len(dts) == 1
    assert dts[0]["started_at"] == reconnect


def test_reconnect_then_increment_then_idle_uses_new_baseline():
    """Após reconexão, novo incremento real → inatividade > threshold:
    a parada parte do incremento pós-reconexão, não do baseline velho."""
    service, _, pulse, observers, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()

    pulse.devices = [_device(counter=101, online=False)]
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 999)
    service.tick_all()

    reconnect = clock.at + timedelta(seconds=1)
    pulse.devices = [_device(counter=101)]
    clock.at = reconnect
    service.tick_all()  # rebaseline

    new_increment = reconnect + timedelta(seconds=10)
    pulse.devices = [_device(counter=102)]
    clock.at = new_increment
    # producing autônomo permanece aberto no gap degradado — incremento
    # só avança o cursor (sem reabrir fato / sem audit falso).
    assert service.tick_all() == 0
    assert observers.get(branch="01", work_center="CT01")[
        "last_increment_at"
    ] == new_increment
    assert _open_states(states)[0]["state"] == "producing"

    clock.at = new_increment + timedelta(seconds=THRESHOLD + 1)
    assert service.tick_all() == 1
    dts = _open_downtimes(downtimes)
    assert len(dts) == 1
    assert dts[0]["started_at"] == new_increment


def test_open_downtime_survives_telemetry_gap_without_extension():
    """Parada legítima aberta antes da falha é preservada: o gap não a
    duplica nem a estende retroativamente — permanece aberta e
    classificável até atividade real."""
    service, _, pulse, observers, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()
    stop_at = BASE + timedelta(seconds=5 + THRESHOLD + 1)
    clock.at = stop_at
    service.tick_all()  # parada aberta, started_at = BASE+5
    dts = _open_downtimes(downtimes)
    assert len(dts) == 1
    original_started = dts[0]["started_at"]

    pulse.devices = [_device(counter=101, online=False)]
    clock.at = stop_at + timedelta(seconds=THRESHOLD * 5)
    service.tick_all()  # degradado — parada intacta

    pulse.devices = [_device(counter=101)]
    clock.at = stop_at + timedelta(seconds=THRESHOLD * 5 + 1)
    service.tick_all()  # reconexão: rebaseline, parada segue aberta

    dts = _open_downtimes(downtimes)
    assert len(dts) == 1
    assert dts[0]["started_at"] == original_started
    assert len(downtimes.events) == 1
    assert len(states.events) <= 2  # producing + stopped, sem duplicatas

    # Retorno real fecha a parada uma única vez.
    pulse.devices = [_device(counter=110)]
    clock.at = clock.at + timedelta(seconds=30)
    service.tick_all()
    assert _open_downtimes(downtimes) == []
    assert len(downtimes.events) == 1


def test_intermittent_degradation_never_duplicates_facts():
    """Flapping degradado↔online sem incremento: nenhum fato, nenhuma
    duplicação — cada retorno só reancora o cursor."""
    service, _, pulse, observers, states, downtimes, clock = _monitor()
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()  # producing

    at = clock.at
    for _ in range(4):
        at += timedelta(seconds=THRESHOLD + 50)
        pulse.devices = [_device(counter=101, online=False)]
        clock.at = at
        assert service.tick_all() == 0
        at += timedelta(seconds=1)
        pulse.devices = [_device(counter=101)]
        clock.at = at
        assert service.tick_all() == 0  # rebaseline a cada retorno
        assert _open_downtimes(downtimes) == []
    assert len(downtimes.events) == 0
    assert _open_states(states)[0]["state"] == "producing"


def test_degraded_then_online_without_prior_baseline_stays_silent():
    """CT sem nenhum incremento observado (AC-10): degradado → online
    inalterado não arma baseline — nunca nasce parada."""
    service, _, pulse, observers, states, downtimes, clock = _monitor()
    pulse.devices = [_device(online=False)]
    service.tick_all()  # primeiro contato já degradado

    pulse.devices = [_device(counter=100)]
    clock.at = BASE + timedelta(seconds=1)
    assert service.tick_all() == 0
    assert observers.get(branch="01", work_center="CT01")[
        "last_increment_at"
    ] is None

    clock.at = BASE + timedelta(days=3)
    assert service.tick_all() == 0
    assert states.events == []
    assert downtimes.events == []


# ---------- Concorrência / arbitragem (AC-07, AC-08, AC-13) ----------


def test_lock_contended_skips_tick():
    service, _, _, observers, states, downtimes, _ = _monitor()
    observers.lock_granted = False
    assert service.tick_all() == 0
    assert observers.rows == {}


def test_active_run_skips_autonomous_tick():
    repo = FakeRepo()
    session = service_session(repo)
    device = _device()
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    run_service = make_service(repo, pulse)
    started = run_service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    assert started["status"] == "running"

    service, _, _, observers, states, downtimes, clock = _monitor(
        repo=repo, pulse=pulse
    )
    assert service.tick_all() == 0
    assert _open_states(states) == []  # o estado producing pertence ao run
    assert _open_downtimes(downtimes) == []


def test_start_run_closes_autonomous_facts_and_anchors_fresh():
    """Play sobre CT monitorado: fatos autônomos encerram na fronteira e
    nenhum pulso anterior é atribuído ao run (AC-07)."""
    repo = FakeRepo()
    device = _device()
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    mes, states, downtimes = make_mes()
    run_service = make_service(repo, pulse, mes_lifecycle=mes)
    session = service_session(repo)

    service, _, _, observers, _, _, clock = _monitor(
        repo=repo,
        pulse=pulse,
        states=states,
        downtimes=downtimes,
    )
    service.tick_all()
    pulse.devices = [_device(counter=140)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()
    assert _open_states(states)[0]["run_id"] is None

    pulse.device_by_id["dev-1"] = _device(counter=140)
    started = run_service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    assert started["status"] == "running"
    assert started["piecesTotal"] == 0  # pulsos pré-Play não viram produção
    open_states = _open_states(states)
    assert len(open_states) == 1
    assert open_states[0]["run_id"] == started["id"]


def test_start_run_closes_open_autonomous_downtime():
    """Play com parada autônoma aberta: encerra a parada (classificável
    depois) e abre o run — um único fato aberto por CT (RQ-02/AC-07)."""
    repo = FakeRepo()
    device = _device()
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    mes, states, downtimes = make_mes()
    run_service = make_service(repo, pulse, mes_lifecycle=mes)
    session = service_session(repo)

    service, _, _, _, _, _, clock = _monitor(
        repo=repo, pulse=pulse, states=states, downtimes=downtimes
    )
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 1)
    service.tick_all()
    assert len(_open_downtimes(downtimes)) == 1

    started = run_service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    assert started["status"] == "running"
    assert _open_downtimes(downtimes) == []
    assert len(downtimes.events) == 1
    assert downtimes.events[0]["ended_at"] is not None


def test_stop_run_resumes_autonomous_monitoring():
    """Após o Stop o monitoramento continua sem ação do operador (AC-08)."""
    repo = FakeRepo()
    device = _device()
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    mes, states, downtimes = make_mes()
    run_service = make_service(repo, pulse, mes_lifecycle=mes)
    session = service_session(repo)
    started = run_service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    run_service.stop_run(started["id"], session_token=session)

    service, _, _, observers, _, _, clock = _monitor(
        repo=repo, pulse=pulse, states=states, downtimes=downtimes
    )
    service.tick_all()  # baseline do observador
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    assert service.tick_all() == 1
    assert _open_states(states)[0]["run_id"] is None


def test_restart_survives_via_durable_cursor():
    """Cursor persistido preserva baseline após restart da API (AC-04)."""
    observers = FakeObserverRepo()
    states_repo = FakeStateRepo()
    downtimes_repo = FakeDowntimeRepo()
    pulse = FakePulse(devices=[_device()])
    clock = _Clock(BASE)

    svc1, repo, _, _, _, _, _ = _monitor(
        pulse=pulse,
        observers=observers,
        states=states_repo,
        downtimes=downtimes_repo,
        clock=clock,
    )
    svc1.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    svc1.tick_all()

    # "Restart": nova instância, mesmos repositórios duráveis.
    svc2, _, _, _, _, _, _ = _monitor(
        pulse=pulse,
        observers=observers,
        states=states_repo,
        downtimes=downtimes_repo,
        clock=clock,
        repo=repo,
    )
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 1)
    assert svc2.tick_all() == 1  # baseline preservado → parada após threshold
    assert len(_open_downtimes(downtimes_repo)) == 1


# ---------- Classificação sem run (AC-05) ----------


def _classifier(repo, downtimes, reasons=None, audit=None):
    run_service = make_service(repo, FakePulse())
    return MesDowntimeClassificationService(
        downtimes=downtimes,
        reasons=reasons or FakeReasonRepo(),
        run_service=run_service,
        audit=audit,
    )


def _monitor_with_downtime():
    """Abre uma parada autônoma e devolve (repo, pulse, downtimes, clock, service)."""
    repo = FakeRepo()
    pulse = FakePulse(devices=[_device()])
    mes, states, downtimes = make_mes()
    service, _, _, observers, _, _, clock = _monitor(
        repo=repo, pulse=pulse, states=states, downtimes=downtimes
    )
    service.tick_all()
    pulse.devices = [_device(counter=101)]
    clock.at = BASE + timedelta(seconds=5)
    service.tick_all()
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 1)
    service.tick_all()
    return repo, pulse, downtimes, clock, service


def test_classify_open_autonomous_downtime_by_identity():
    repo, pulse, downtimes, clock, service = _monitor_with_downtime()
    session = service_session(repo)
    dt = _open_downtimes(downtimes)[0]
    classifier = _classifier(repo, downtimes)
    payload = classifier.classify_work_center_downtime(
        dt["id"],
        reason_code="raw_material",
        note=None,
        session_token=session,
    )
    assert payload["reasonCode"] == "raw_material"
    assert payload["runId"] is None
    assert payload["confirmed"] is True


def test_classify_closed_autonomous_downtime():
    repo, pulse, downtimes, clock, service = _monitor_with_downtime()
    # Retomada encerra a parada antes da classificação.
    pulse.devices = [_device(counter=105)]
    clock.at = BASE + timedelta(seconds=5 + THRESHOLD + 30)
    service.tick_all()
    assert _open_downtimes(downtimes) == []

    session = service_session(repo)
    dt = downtimes.events[0]
    classifier = _classifier(repo, downtimes)
    payload = classifier.classify_work_center_downtime(
        dt["id"],
        reason_code="maintenance",
        note="Troca de ferramenta",
        session_token=session,
    )
    assert payload["reasonCode"] == "maintenance"
    assert payload["endedAt"] is not None


def test_classify_rejects_session_from_other_work_center():
    repo, pulse, downtimes, clock, service = _monitor_with_downtime()
    other = make_service(repo, FakePulse())
    session = other.create_bench_session(
        branch="01", work_center="CT02", registration="USR02"
    )["sessionToken"]
    dt = _open_downtimes(downtimes)[0]
    classifier = _classifier(repo, downtimes)
    with pytest.raises(BenchSessionRequired):
        classifier.classify_work_center_downtime(
            dt["id"],
            reason_code="raw_material",
            note=None,
            session_token=session,
        )
