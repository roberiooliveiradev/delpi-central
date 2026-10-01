"""Detecção automática de parada por ausência de peças contadas (Fase 1+).

Cobre threshold configurável, baseline persistido, idempotência do tick,
auto-resume por incremento, Pulse offline, Pause/Stop durante auto-stop e
classificação de parada encerrada — tudo com relógio injetável.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.application.services.mes_downtime_classification_service import (
    MesDowntimeClassificationService,
)
from production_control_app.application.services.mes_run_lifecycle_service import (
    MesRunLifecycleService,
)
from production_control_app.application.services.machine_load_realtime_hub import (
    machine_load_realtime_hub,
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
    service_session,
)

THRESHOLD = 120


class FakeAudit:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def append(self, **kwargs):
        self.events.append(dict(kwargs))


class FakeClock:
    """Relógio injetável — parte do tempo real para casar com o baseline
    persistido pelo repositório fake (NOW() na criação do run)."""

    def __init__(self, at: datetime | None = None) -> None:
        self.now = at or datetime.now(timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def _setup(
    *,
    counter: int = 100,
    auto_seconds: int = THRESHOLD,
    with_reasons: bool = True,
):
    """Devolve (service, lifecycle repos, repo, pulse, clock, session, audit)."""
    repo = FakeRepo()
    session = service_session(repo)
    device = {
        "deviceId": "dev-1",
        "counter": counter,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    states = FakeStateRepo()
    downtimes = FakeDowntimeRepo()
    reasons = FakeReasonRepo() if with_reasons else None
    lifecycle = MesRunLifecycleService(
        states=states,
        downtimes=downtimes,
        reasons=reasons,
        run_lookup=repo.get_run,
    )
    clock = FakeClock()
    audit = FakeAudit()
    service = ProductionRunService(
        repository=repo,
        pulse_gateway=pulse,
        mes_lifecycle=lifecycle,
        audit=audit,
        clock=clock,
        auto_downtime_seconds=auto_seconds,
    )
    return service, states, downtimes, repo, pulse, clock, session, audit


def _start(service: ProductionRunService, session: str) -> dict:
    return service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )


def _sync_clock(clock: "FakeClock", repo, run_id: str) -> None:
    """Alinha o relógio fake ao baseline persistido — permite testar o
    threshold exato (120 s) sem depender de microssegundos de wall-clock."""
    clock.now = repo.runs[run_id]["last_count_activity_at"]


def _classifier(service: ProductionRunService, downtimes: FakeDowntimeRepo):
    return MesDowntimeClassificationService(
        run_service=service,
        downtimes=downtimes,
        reasons=FakeReasonRepo(),
        audit=FakeAudit(),
    )


def test_play_sets_count_activity_baseline():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    assert repo.runs[run["id"]]["last_count_activity_at"] is not None


def test_idle_below_threshold_keeps_producing():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    clock.advance(THRESHOLD - 1)  # 119 s sem golpe
    service.tick_running_runs()
    assert downtimes.events == []
    assert states.events[-1]["state"] == "producing"


def test_threshold_opens_exactly_one_auto_downtime():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    clock.advance(THRESHOLD)  # 120 s
    service.tick_running_runs()
    assert len(downtimes.events) == 1
    dt = downtimes.events[0]
    assert dt["run_id"] == run["id"]
    assert dt["source"] == "system"
    # Sem peça contada desde o Play: motivo inicial setup confirmado
    # pelo sistema (operador pode alterar enquanto a parada segue aberta).
    assert dt["reason_code"] == "setup" and dt["confirmed"] is True
    assert dt["confirmed_by_type"] == "system"
    assert states.events[-1]["state"] == "stopped"
    assert states.events[-1]["source"] == "system"
    # started_at retroage à última atividade (baseline do run neste caso)
    assert dt["started_at"] == repo.runs[run["id"]]["last_count_activity_at"]

    # Ticks seguintes são idempotentes: nenhuma parada extra nem novo estado.
    clock.advance(300)
    for _ in range(3):
        service.tick_running_runs()
    assert len(downtimes.events) == 1
    assert len([e for e in states.events if e["ended_at"] is None]) == 1


def test_new_increment_auto_resumes_and_updates_activity():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    assert downtimes.events[0]["ended_at"] is None

    resumed_at = clock.now
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 105,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    service.tick_running_runs()

    dt = downtimes.events[0]
    assert dt["ended_at"] == resumed_at
    assert states.events[-1]["state"] == "producing"
    assert states.events[-1]["ended_at"] is None
    assert repo.runs[run["id"]]["status"] == "running"
    assert repo.runs[run["id"]]["last_count_activity_at"] == resumed_at
    assert repo.runs[run["id"]]["pieces_total"] == 5


def test_counter_unchanged_does_not_refresh_activity():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    baseline = repo.runs[run["id"]]["last_count_activity_at"]
    clock.advance(30)
    service.tick_running_runs()
    assert repo.runs[run["id"]]["last_count_activity_at"] == baseline
    assert downtimes.events == []


def test_counter_decrease_is_not_a_hit():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    baseline_clock = clock.now
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 90,  # correção — menor que a âncora
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    clock.advance(30)
    service.tick_running_runs()
    run = next(iter(repo.runs.values()))
    assert run["last_count_activity_at"] == baseline_clock


def test_offline_pulse_never_creates_downtime():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": None,
        "counterEpoch": None,
        "online": False,
        "status": "offline",
    }
    clock.advance(600)
    for _ in range(3):
        service.tick_running_runs()
    assert downtimes.events == []


def test_offline_pulse_does_not_close_auto_downtime():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    assert len(downtimes.events) == 1

    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "online": False,
        "status": "offline",
        "counter": None,
        "counterEpoch": None,
    }
    clock.advance(60)
    service.tick_running_runs()
    assert downtimes.events[0]["ended_at"] is None
    assert states.events[-1]["state"] == "stopped"


def test_pulse_back_without_increment_keeps_downtime_open():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    clock.advance(10)
    service.tick_running_runs()  # counter igual — sem auto-resume
    assert downtimes.events[0]["ended_at"] is None


def test_manual_pause_during_auto_stop_does_not_duplicate_facts():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    assert len(downtimes.events) == 1

    paused = service.pause_run(run["id"], session_token=session)
    assert paused["status"] == "paused"
    assert len(downtimes.events) == 1  # mesma parada reutilizada
    assert len([e for e in states.events if e["ended_at"] is None]) == 1
    assert states.events[-1]["state"] == "stopped"


def test_paused_run_never_auto_resumes_on_hit():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    # força classificação para poder pausar/retomar sem ruído
    service.pause_run(run["id"], session_token=session)
    dt = downtimes.events[0]
    dt["reason_code"] = "raw_material"
    dt["confirmed"] = True

    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 150,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    clock.advance(10)
    service.tick_running_runs()
    assert repo.runs[run["id"]]["status"] == "paused"
    assert downtimes.events[0]["ended_at"] is None


def test_stop_during_auto_stop_requires_classification_then_closes():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    # Produz peças antes — só parada após produção nasce sem motivo.
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 105,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    service.tick_running_runs()
    clock.advance(THRESHOLD)
    service.tick_running_runs()

    with pytest.raises(DowntimeClassificationRequired):
        service.stop_run(run["id"], session_token=session)

    downtimes.events[0]["reason_code"] = "raw_material"
    downtimes.events[0]["confirmed"] = True
    stopped = service.stop_run(run["id"], session_token=session)
    assert stopped["status"] == "completed"
    assert downtimes.events[0]["ended_at"] is not None
    assert all(e["ended_at"] is not None for e in states.events)


def test_legacy_run_null_baseline_gets_initialized_without_retroactive_stop():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    repo.runs[run["id"]]["last_count_activity_at"] = None  # simula legado

    clock.advance(3600)  # horas depois
    service.tick_running_runs()
    assert downtimes.events == []
    assert repo.runs[run["id"]]["last_count_activity_at"] == clock.now

    clock.advance(THRESHOLD - 1)
    service.tick_running_runs()
    assert downtimes.events == []
    clock.advance(1)
    service.tick_running_runs()
    assert len(downtimes.events) == 1


def test_restart_keeps_baseline_and_downtime():
    """Restart simulado: baseline persiste no run e a parada automática aberta
    não é duplicada pelo próximo tick."""
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    baseline = repo.runs[run["id"]]["last_count_activity_at"]

    clock.advance(THRESHOLD)
    service.tick_running_runs()
    assert len(downtimes.events) == 1
    assert downtimes.events[0]["started_at"] == baseline

    # "restart" → tick seguinte enxerga o estado persistido, sem duplicar.
    clock.advance(600)
    service.tick_running_runs()
    assert len(downtimes.events) == 1
    assert downtimes.events[0]["ended_at"] is None


def test_classification_during_open_downtime_and_after_close():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    dt_id = downtimes.events[0]["id"]

    classifier = _classifier(service, downtimes)
    # durante a parada aberta
    out = classifier.classify(
        run["id"],
        reason_code="raw_material",
        note=None,
        session_token=session,
    )
    assert out["reasonCode"] == "raw_material"

    # incremento encerra a parada classificada e reabre producing
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 105,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    service.tick_running_runs()
    assert downtimes.events[0]["ended_at"] is not None

    # outra parada automática, encerrada pelo auto-resume
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    assert len(downtimes.events) == 2
    dt2 = downtimes.events[1]
    assert dt2["reason_code"] is None

    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 110,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    service.tick_running_runs()
    assert dt2["ended_at"] is not None

    # classifica parada já encerrada pelo ID
    out2 = classifier.classify(
        run["id"],
        reason_code="other",
        note="teste",
        session_token=session,
        downtime_id=dt2["id"],
    )
    assert out2["reasonCode"] == "other"
    assert out2["endedAt"] is not None

    # downtime de outro run não pode ser classificado aqui
    with pytest.raises(DowntimeNotFound):
        classifier.classify(
            run["id"],
            reason_code="raw_material",
            note=None,
            session_token=session,
            downtime_id="dt-inexistente",
        )


def test_requires_note_still_enforced_on_closed_downtime():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    dt_id = downtimes.events[0]["id"]
    classifier = _classifier(service, downtimes)
    with pytest.raises(InvalidMesEvent):
        classifier.classify(
            run["id"],
            reason_code="other",
            note=None,
            session_token=session,
            downtime_id=dt_id,
        )


def test_pending_downtime_survives_in_snapshot():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    # Produz peças antes — parada automática pós-produção fica pendente.
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 103,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    service.tick_running_runs()
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 107,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    service.tick_running_runs()
    active = service.get_active(branch="01", work_center="CT01")
    assert active["operationalState"] == "producing"
    assert active["pendingDowntime"]["id"] == downtimes.events[0]["id"]
    assert active["pendingDowntime"]["endedAt"] is not None
    assert active["pendingDowntimeCount"] == 1


def test_get_active_exposes_operational_state_stopped():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    active = service.get_active(branch="01", work_center="CT01")
    assert active["status"] == "running"
    assert active["operationalState"] == "stopped"
    assert active["downtime"]["reasonCode"] == "setup"


def test_ws_emitted_once_per_transition(monkeypatch: pytest.MonkeyPatch):
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    messages: list[dict] = []
    monkeypatch.setattr(
        machine_load_realtime_hub,
        "schedule_broadcast",
        lambda room, message: messages.append(dict(message)),
    )
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    clock.advance(60)
    service.tick_running_runs()
    service.tick_running_runs()
    # Um evento por transição (broadcast em room do CT + room da filial);
    # ticks seguintes sem novo golpe não retransmitem.
    reasons = [m["reason"] for m in messages]
    assert reasons == ["automatic_downtime_started"] * 2
    assert messages[0]["operationalState"] == "stopped"
    assert messages[0]["downtime"]["source"] == "system"


def test_audit_records_auto_transitions():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 103,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    service.tick_running_runs()
    actions = [e["action"] for e in audit.events]
    assert "automatic_downtime_started" in actions
    assert "automatic_downtime_ended" in actions
    started_ev = next(
        e for e in audit.events if e["action"] == "automatic_downtime_started"
    )
    assert started_ev["actor_type"] == "system"
    assert started_ev["details"]["thresholdSeconds"] == THRESHOLD
    assert "lastCountActivityAt" in started_ev["details"]
    assert "detectedAt" in started_ev["details"]


def test_auto_detection_disabled_with_zero():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup(
        auto_seconds=0
    )
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    clock.advance(3600)
    service.tick_running_runs()
    assert downtimes.events == []


def test_multiple_auto_downtimes_same_run():
    service, states, downtimes, repo, pulse, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    for i in range(2):
        clock.advance(THRESHOLD)
        service.tick_running_runs()
        pulse.device_by_id["dev-1"] = {
            "deviceId": "dev-1",
            "counter": 200 + i,
            "counterEpoch": 1,
            "online": True,
            "status": "online",
        }
        service.tick_running_runs()
    assert len(downtimes.events) == 2
    assert all(e["ended_at"] is not None for e in downtimes.events)


# ---------------------------------------------------------------------------
# Integração Postgres (banco descartável): PC_TEST_MES_DB=1 + PLUGINS_DB_*
# ---------------------------------------------------------------------------

import os

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


def _pg_device(counter: int = 100) -> dict:
    return {
        "deviceId": "00000000-0000-4000-8000-0000000000a1",
        "counter": counter,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }


@_DB_REQUIRED
class TestAutoDowntimePostgres:
    @pytest.fixture()
    def pg(self):
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
        repo = PostgresProductionRunRepository()
        lifecycle = MesRunLifecycleService(
            states=states,
            downtimes=downtimes,
            reasons=reasons,
            run_lookup=repo.get_run,
        )
        return repo, lifecycle, states, downtimes

    @pytest.fixture()
    def clean_ct(self):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        wc = "ZZ-TEST-AUTODT"

        def _clean() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.mes_audit_events "
                        "WHERE work_center = %s",
                        (wc,),
                    )
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
                        f"DELETE FROM {PC_SCHEMA_NAME}.production_run_segments "
                        "WHERE run_id IN (SELECT id FROM "
                        f"{PC_SCHEMA_NAME}.production_runs WHERE work_center = %s)",
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

    def _service(self, repo, lifecycle, clock, device=None):
        device = device or _pg_device()
        return ProductionRunService(
            repository=repo,
            pulse_gateway=FakePulse(
                devices=[device], device_by_id={device["deviceId"]: device}
            ),
            mes_lifecycle=lifecycle,
            clock=clock,
            auto_downtime_seconds=THRESHOLD,
        )

    def _session(self, service, wc):
        return service.create_bench_session(
            branch="01", work_center=wc, registration="USR01"
        )["sessionToken"]

    def _start(self, service, wc, token):
        return service.start_run(
            branch="01",
            work_center=wc,
            production_order="OP-AUTO",
            operation_code="10",
            session_token=token,
        )

    def test_auto_stop_and_resume_persisted(self, pg, clean_ct):
        repo, lifecycle, states, downtimes = pg
        clock = FakeClock()
        service = self._service(repo, lifecycle, clock)
        token = self._session(service, clean_ct)
        run = self._start(service, clean_ct, token)

        baseline = repo.get_run(run["id"])["last_count_activity_at"]
        assert baseline is not None

        # Produz peças antes — parada pós-produção nasce sem motivo.
        clock.now = baseline + timedelta(seconds=10)
        service._pulse.device_by_id["00000000-0000-4000-8000-0000000000a1"] = _pg_device(counter=140)
        service.tick_running_runs()
        activity = repo.get_run(run["id"])["last_count_activity_at"]

        clock.now = activity + timedelta(seconds=THRESHOLD)
        service.tick_running_runs()

        open_dt = downtimes.get_open(branch="01", work_center=clean_ct)
        assert open_dt is not None and open_dt["source"] == "system"
        assert open_dt["started_at"] == activity
        assert open_dt["reason_code"] is None
        open_state = states.get_open(branch="01", work_center=clean_ct)
        assert open_state["state"] == "stopped" and open_state["source"] == "system"
        assert repo.get_run(run["id"])["status"] == "running"

        # tick seguinte é idempotente
        clock.advance(60)
        service.tick_running_runs()
        assert len(downtimes.list_for_run(run["id"])) == 1

        # incremento real → auto-resume
        resumed_at = clock.now
        service._pulse.device_by_id["00000000-0000-4000-8000-0000000000a1"] = _pg_device(counter=180)
        service.tick_running_runs()
        assert downtimes.get_open(branch="01", work_center=clean_ct) is None
        open_state = states.get_open(branch="01", work_center=clean_ct)
        assert open_state["state"] == "producing"
        fresh = repo.get_run(run["id"])
        assert fresh["status"] == "running"
        assert fresh["pieces_total"] == 80
        assert fresh["last_count_activity_at"] == resumed_at

        # pendente de classificação aparece no snapshot
        active = service.get_active(branch="01", work_center=clean_ct)
        assert active["operationalState"] == "producing"
        assert active["pendingDowntime"]["id"] == open_dt["id"]
        assert active["pendingDowntimeCount"] == 1

    def test_pause_during_auto_stop_reuses_facts(self, pg, clean_ct):
        repo, lifecycle, states, downtimes = pg
        clock = FakeClock()
        service = self._service(repo, lifecycle, clock)
        token = self._session(service, clean_ct)
        run = self._start(service, clean_ct, token)

        clock.now = repo.get_run(run["id"])["last_count_activity_at"] + timedelta(
            seconds=THRESHOLD
        )
        service.tick_running_runs()
        assert len(downtimes.list_for_run(run["id"])) == 1

        paused = service.pause_run(run["id"], session_token=token)
        assert paused["status"] == "paused"
        assert len(downtimes.list_for_run(run["id"])) == 1
        open_state = states.get_open(branch="01", work_center=clean_ct)
        assert open_state["state"] == "stopped"

    def test_legacy_run_null_baseline_initialized_not_stopped(self, pg, clean_ct):
        repo, lifecycle, states, downtimes = pg
        clock = FakeClock()
        service = self._service(repo, lifecycle, clock)
        token = self._session(service, clean_ct)
        run = self._start(service, clean_ct, token)

        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE {PC_SCHEMA_NAME}.production_runs "
                    "SET last_count_activity_at = NULL WHERE id = %s::uuid",
                    (run["id"],),
                )
            conn.commit()

        clock.advance(3600)
        service.tick_running_runs()
        assert downtimes.get_open(branch="01", work_center=clean_ct) is None
        baseline = repo.get_run(run["id"])["last_count_activity_at"]
        assert baseline is not None

        clock.now = baseline + timedelta(seconds=THRESHOLD)
        service.tick_running_runs()
        assert downtimes.get_open(branch="01", work_center=clean_ct) is not None


def _integrity_report(run, states_rows, dts_rows):
    return {
        "runs": [run],
        "open_states": states_rows,
        "open_downtimes": dts_rows,
        "open_segments": [{"id": "seg-1", "run_id": run["id"]}],
        "state_runs": {},
        "mes_observed_runs": {run["id"]},
    }


def test_integrity_accepts_running_plus_system_stopped():
    from production_control_app.application.services.mes_runtime_integrity_service import (  # noqa: E501
        inspect_runtime_integrity,
    )

    run = {"id": "r1", "status": "running", "branch": "01", "work_center": "CT01"}
    report = _integrity_report(
        run,
        [{"id": "st1", "run_id": "r1", "branch": "01", "work_center": "CT01",
          "state": "stopped", "source": "system"}],
        [{"id": "dt1", "run_id": "r1", "state_event_id": "st1", "branch": "01",
          "work_center": "CT01", "source": "system"}],
    )
    assert inspect_runtime_integrity(report) == []


def test_integrity_rejects_running_with_manual_stopped():
    from production_control_app.application.services.mes_runtime_integrity_service import (  # noqa: E501
        inspect_runtime_integrity,
    )

    run = {"id": "r1", "status": "running", "branch": "01", "work_center": "CT01"}
    report = _integrity_report(
        run,
        [{"id": "st1", "run_id": "r1", "branch": "01", "work_center": "CT01",
          "state": "stopped", "source": "operator"}],
        [{"id": "dt1", "run_id": "r1", "state_event_id": "st1", "branch": "01",
          "work_center": "CT01", "source": "operator_pause"}],
    )
    codes = {i["issue_code"] for i in inspect_runtime_integrity(report)}
    assert "running_with_open_stopped" in codes
    assert "running_without_open_producing" in codes


def _finish_run_with_unclassified_downtime(
    service, downtimes, repo, pulse, clock, session
):
    """Run com parada automática já encerrada sem motivo → run stop."""
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    # Produz 4 peças — a parada seguinte nasce sem motivo (não é setup).
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 104,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    service.tick_running_runs()
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    assert downtimes.events and downtimes.events[0]["ended_at"] is None
    assert downtimes.events[0]["reason_code"] is None
    clock.advance(60)
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 110,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    service.tick_running_runs()
    assert downtimes.events[0]["ended_at"] is not None
    service.stop_run(run["id"], session_token=session)
    return run


def test_unclassified_list_covers_finished_run_and_classify_by_id():
    service, _st, downtimes, repo, pulse, clock, session, _a = _setup()
    run = _finish_run_with_unclassified_downtime(
        service, downtimes, repo, pulse, clock, session
    )
    classifier = _classifier(service, downtimes)

    items = classifier.list_unclassified(
        branch="01", work_center="CT01", session_token=session
    )
    assert len(items) == 1
    item = items[0]
    assert item["runId"] == run["id"]
    assert item["confirmed"] is False
    assert item["endedAt"] is not None
    assert item["durationSeconds"] > 0
    assert item["productionOrder"] == "OP1"

    # Classifica a parada encerrada do run já finalizado, pela identidade.
    payload = classifier.classify(
        run["id"],
        reason_code="raw_material",
        note=None,
        session_token=session,
        downtime_id=item["id"],
    )
    assert payload["reasonCode"] == "raw_material"
    assert payload["endedAt"] is not None
    assert (
        classifier.list_unclassified(
            branch="01", work_center="CT01", session_token=session
        )
        == []
    )


def test_unclassified_list_excludes_open_and_classified_downtimes():
    service, _st, downtimes, repo, pulse, clock, session, _a = _setup()
    _finish_run_with_unclassified_downtime(
        service, downtimes, repo, pulse, clock, session
    )
    classifier = _classifier(service, downtimes)
    downtimes.events[0]["reason_code"] = "raw_material"
    downtimes.events[0]["confirmed"] = True
    assert (
        classifier.list_unclassified(
            branch="01", work_center="CT01", session_token=session
        )
        == []
    )

    # Parada ainda aberta não entra na lista de pendências encerradas.
    run2 = _start(service, session)
    _sync_clock(clock, repo, run2["id"])
    service.tick_running_runs()  # 1º tick: delta do contador conta como atividade
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    open_items = classifier.list_unclassified(
        branch="01", work_center="CT01", session_token=session
    )
    assert open_items == []
    open_dt = [e for e in downtimes.events if e["ended_at"] is None]
    assert len(open_dt) == 1 and open_dt[0]["run_id"] == run2["id"]


def test_unclassified_list_requires_session_of_same_work_center():
    service, _st, downtimes, repo, pulse, clock, session, _a = _setup()
    _finish_run_with_unclassified_downtime(
        service, downtimes, repo, pulse, clock, session
    )
    classifier = _classifier(service, downtimes)

    from production_control_app.domain.errors import BenchSessionRequired

    with pytest.raises(BenchSessionRequired):
        classifier.list_unclassified(
            branch="01", work_center="CT99", session_token=session
        )
    with pytest.raises(BenchSessionRequired):
        classifier.list_unclassified(
            branch="01", work_center="CT01", session_token=None
        )


def test_auto_stop_after_pieces_has_no_reason():
    """Parada automática DEPOIS de produzir nasce sem motivo — setup só
    vale para parada antes da primeira peça do run."""
    service, _st, downtimes, _r, pulse, clock, session, _a = _setup()
    _start(service, session)
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": 105,
        "counterEpoch": 1,
        "online": True,
        "status": "online",
    }
    service.tick_running_runs()  # 5 peças
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    assert len(downtimes.events) == 1
    dt = downtimes.events[0]
    assert dt["source"] == "system"
    assert dt["reason_code"] is None
    assert dt["confirmed"] is False


def test_setup_reason_is_editable_while_downtime_open():
    """O motivo inicial setup pode ser trocado pelo operador com a
    parada ainda aberta — mesmo fluxo de classificação de sempre."""
    service, _st, downtimes, repo, _p, clock, session, _a = _setup()
    run = _start(service, session)
    _sync_clock(clock, repo, run["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    dt = downtimes.events[0]
    assert dt["reason_code"] == "setup" and dt["ended_at"] is None

    classifier = _classifier(service, downtimes)
    out = classifier.classify(
        run["id"],
        reason_code="maintenance",
        note=None,
        session_token=session,
    )
    assert out["reasonCode"] == "maintenance"
    assert downtimes.events[0]["reason_code"] == "maintenance"
    assert downtimes.events[0]["confirmed_by_type"] == "operator"


def test_setup_stop_audit_carries_initial_reason():
    service, _st, _dt, repo, _p, clock, session, audit = _setup()
    run_ = _start(service, session)
    _sync_clock(clock, repo, run_["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    started = next(
        e for e in audit.events if e["action"] == "automatic_downtime_started"
    )
    assert started["details"]["initialReasonCode"] == "setup"


def test_orphan_downtime_of_finished_run_is_healed_on_detection():
    """Parada órfã de um run já encerrado não pode bloquear a detecção do
    run atual: o tick a encerra no ended_at do run dono (fronteira
    real) e abre a parada do run corrente."""
    service, states, downtimes, repo, _p, clock, session, _a = _setup()
    run_a = _start(service, session)
    _sync_clock(clock, repo, run_a["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    orphan = downtimes.events[0]
    assert orphan["run_id"] == run_a["id"] and orphan["ended_at"] is None

    # Simula o zumbi: run encerra sem fechar a parada (fecha só o estado
    # para o Play do próximo run não colidir no estado aberto).
    states.close_open(branch="01", work_center="CT01")
    repo.set_run_status(run_a["id"], status="completed")
    owner_ended = repo.runs[run_a["id"]]["ended_at"]

    run_b = _start(service, session)
    _sync_clock(clock, repo, run_b["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()

    assert orphan["ended_at"] == owner_ended
    current = [e for e in downtimes.events if e["ended_at"] is None]
    assert len(current) == 1
    assert current[0]["run_id"] == run_b["id"]
    assert current[0]["source"] == "system"
    assert current[0]["reason_code"] == "setup"


def test_orphan_downtime_of_active_run_still_conflicts():
    """Se o dono da parada aberta segue ativo, o conflito é real: nada é
    fechado e o erro de domínio continua."""
    from production_control_app.domain.errors import DowntimeConflict

    service, _st, downtimes, repo, _p, clock, session, _a = _setup()
    run_a = _start(service, session)
    _sync_clock(clock, repo, run_a["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    orphan = downtimes.events[0]
    assert orphan["ended_at"] is None

    run_b = {
        "id": "run-b",
        "branch": "01",
        "work_center": "CT01",
        "production_order": "OP2",
        "operation_code": "10",
        "pieces_total": 0,
        "status": "running",
    }
    with pytest.raises(DowntimeConflict):
        service._mes.record_automatic_stopped(run_b, conn=None, at=clock.now)
    assert orphan["ended_at"] is None


def test_orphan_state_of_finished_run_is_healed_on_detection():
    """Estado operacional órfão de run encerrado é fechado na fronteira do
    run dono em vez de bloquear a detecção para sempre."""
    service, states, downtimes, repo, _p, clock, session, _a = _setup()
    run_a = _start(service, session)
    _sync_clock(clock, repo, run_a["id"])
    clock.advance(THRESHOLD)
    service.tick_running_runs()
    orphan_state = states.events[-1]
    assert orphan_state["state"] == "stopped" and orphan_state["ended_at"] is None
    orphan_dt = downtimes.events[0]

    # Zumbi: run dono encerrado, estado + parada ainda abertos.
    repo.set_run_status(run_a["id"], status="completed")
    owner_ended = repo.runs[run_a["id"]]["ended_at"]

    run_b = {
        "id": "run-b",
        "branch": "01",
        "work_center": "CT01",
        "production_order": "OP2",
        "operation_code": "10",
        "pieces_total": 0,
        "status": "running",
    }
    dt = service._mes.record_automatic_stopped(run_b, conn=None, at=clock.now)
    assert dt is not None and dt["run_id"] == "run-b"
    assert orphan_state["ended_at"] == owner_ended
    assert orphan_dt["ended_at"] == owner_ended
