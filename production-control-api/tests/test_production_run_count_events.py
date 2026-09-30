"""Fase 2.3 — trilha append-only de mudanças de contagem do Production Run.

Invariante: toda alteração persistida de production_runs.pieces_total
depois da criação do run gera exatamente um production_run_count_event
na mesma transação. Polling sem mudança não persiste nada.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from production_control_app.domain.errors import PulseGatewayError
from production_control_app.domain.services.production_run_counting import (
    build_count_change,
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


# ---------------------------------------------------------------------------
# Domínio puro — build_count_change
# ---------------------------------------------------------------------------


def test_count_change_production_single():
    change = build_count_change(previous_total=100, observed_total=101)
    assert change is not None
    assert change.delta_pieces == 1
    assert change.event_type == "production"
    assert change.pieces_total == 101


def test_count_change_production_jump_aggregated():
    change = build_count_change(previous_total=100, observed_total=105)
    assert change is not None
    assert change.delta_pieces == 5
    assert change.event_type == "production"
    assert change.pieces_total == 105


def test_count_change_correction():
    change = build_count_change(previous_total=105, observed_total=103)
    assert change is not None
    assert change.delta_pieces == -2
    assert change.event_type == "correction"
    assert change.pieces_total == 103


def test_count_change_no_change_returns_none():
    assert build_count_change(previous_total=100, observed_total=100) is None


def test_count_change_never_zero_or_negative_totals():
    change = build_count_change(previous_total=0, observed_total=0)
    assert change is None


# ---------------------------------------------------------------------------
# Helpers de cenário
# ---------------------------------------------------------------------------


def _setup(
    counter: int = 100,
    epoch: int = 1,
    *,
    mes=None,
    auto_downtime_seconds: int = 0,
):
    repo = FakeRepo()
    session = service_session(repo)
    device = {
        "deviceId": "dev-1",
        "counter": counter,
        "counterEpoch": epoch,
        "online": True,
        "name": "Pad",
    }
    pulse = FakePulse(devices=[device], device_by_id={"dev-1": device})
    kwargs = {"auto_downtime_seconds": auto_downtime_seconds}
    if mes is not None:
        kwargs["mes_lifecycle"] = mes
    service = make_service(repo, pulse, **kwargs)
    run = service.start_run(
        branch="01",
        work_center="CT01",
        production_order="OP1",
        operation_code="10",
        session_token=session,
    )
    return service, repo, pulse, session, run["id"]


def _set_counter(pulse: FakePulse, counter: int, epoch: int = 1) -> None:
    pulse.device_by_id["dev-1"] = {
        "deviceId": "dev-1",
        "counter": counter,
        "counterEpoch": epoch,
        "online": True,
    }


def _events(repo: FakeRepo, run_id: str):
    return repo.list_count_events(run_id)


# ---------------------------------------------------------------------------
# Polling — sem evento sem mudança; salto agregado; correction
# ---------------------------------------------------------------------------


def test_idle_polling_persists_no_count_events():
    service, repo, pulse, _session, run_id = _setup()
    for _ in range(500):
        service.tick_running_runs()
    assert _events(repo, run_id) == []
    assert repo.runs[run_id]["pieces_total"] == 0

    _set_counter(pulse, 101)
    service.tick_running_runs()
    events = _events(repo, run_id)
    assert len(events) == 1
    assert events[0]["delta_pieces"] == 1
    assert events[0]["event_type"] == "production"
    assert events[0]["pieces_total"] == 1


def test_counter_jump_produces_single_aggregated_event():
    service, repo, pulse, _s, run_id = _setup()
    _set_counter(pulse, 105)
    service.tick_running_runs()
    events = _events(repo, run_id)
    assert len(events) == 1
    assert events[0]["delta_pieces"] == 5
    assert events[0]["event_type"] == "production"
    assert events[0]["pieces_total"] == 5
    assert repo.runs[run_id]["pieces_total"] == 5


def test_repeated_observation_is_idempotent():
    service, repo, pulse, _s, run_id = _setup()
    _set_counter(pulse, 105)
    service.tick_running_runs()
    service.tick_running_runs()
    service.tick_running_runs()
    assert len(_events(repo, run_id)) == 1


def test_counter_drop_persists_correction_without_activity():
    service, repo, pulse, _s, run_id = _setup()
    _set_counter(pulse, 105)
    service.tick_running_runs()
    activity_before = repo.runs[run_id]["last_count_activity_at"]

    _set_counter(pulse, 103)
    service.tick_running_runs()

    events = _events(repo, run_id)
    assert len(events) == 2
    last = events[-1]
    assert last["event_type"] == "correction"
    assert last["delta_pieces"] == -2
    assert last["pieces_total"] == 3
    assert repo.runs[run_id]["pieces_total"] == 3
    # correction não conta como golpe de produção
    assert repo.runs[run_id]["last_count_activity_at"] == activity_before


# ---------------------------------------------------------------------------
# Auto-downtime — produção resume, correction não resume
# ---------------------------------------------------------------------------


def _setup_with_auto_downtime():
    mes, states, downtimes = make_mes()
    service, repo, pulse, session, run_id = _setup(
        mes=mes, auto_downtime_seconds=60
    )
    return service, repo, pulse, session, run_id, downtimes


def _force_auto_downtime(repo: FakeRepo, run_id: str) -> None:
    repo.runs[run_id]["last_count_activity_at"] = datetime.now(
        timezone.utc
    ) - timedelta(seconds=3600)


def test_production_event_auto_resumes_open_downtime():
    service, repo, pulse, _s, run_id, downtimes = _setup_with_auto_downtime()
    _force_auto_downtime(repo, run_id)
    service.tick_running_runs()
    assert downtimes.list_for_run(run_id)  # parada aberta

    _set_counter(pulse, 101)
    service.tick_running_runs()

    events = _events(repo, run_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "production"
    # parada automática encerrada
    assert all(dt.get("ended_at") is not None for dt in downtimes.list_for_run(run_id))


def test_correction_does_not_auto_resume_downtime():
    service, repo, pulse, _s, run_id, downtimes = _setup_with_auto_downtime()
    _set_counter(pulse, 102)
    service.tick_running_runs()
    _force_auto_downtime(repo, run_id)
    service.tick_running_runs()
    assert downtimes.list_for_run(run_id)

    _set_counter(pulse, 101)  # drop 2 -> 1: correction
    service.tick_running_runs()

    events = _events(repo, run_id)
    assert events[-1]["event_type"] == "correction"
    open_dts = [dt for dt in downtimes.list_for_run(run_id) if dt.get("ended_at") is None]
    assert open_dts, "correction não pode encerrar parada automática"


# ---------------------------------------------------------------------------
# get_active — respeita a trilha
# ---------------------------------------------------------------------------


def test_get_active_without_change_writes_no_event():
    service, repo, pulse, _s, run_id = _setup()
    service.get_active(branch="01", work_center="CT01")
    assert _events(repo, run_id) == []


def test_get_active_observing_change_persists_event():
    service, repo, pulse, _s, run_id = _setup()
    _set_counter(pulse, 101)
    active = service.get_active(branch="01", work_center="CT01")
    assert active["piecesTotal"] == 1
    events = _events(repo, run_id)
    assert len(events) == 1
    assert events[0]["delta_pieces"] == 1

    # segunda leitura idempotente
    service.get_active(branch="01", work_center="CT01")
    assert len(_events(repo, run_id)) == 1


# ---------------------------------------------------------------------------
# Pause / Stop consolidam contagem + evento na mesma transição
# ---------------------------------------------------------------------------


def test_pause_persists_observed_pieces_and_event():
    service, repo, pulse, session, run_id = _setup()
    _set_counter(pulse, 102)
    payload = service.pause_run(run_id, session_token=session)
    assert payload["status"] == "paused"
    assert payload["piecesTotal"] == 2
    events = _events(repo, run_id)
    assert len(events) == 1
    assert events[0]["delta_pieces"] == 2
    assert events[0]["event_type"] == "production"


def test_stop_persists_observed_pieces_and_event():
    service, repo, pulse, session, run_id = _setup()
    _set_counter(pulse, 103)
    payload = service.stop_run(run_id, session_token=session)
    assert payload["status"] == "completed"
    events = _events(repo, run_id)
    assert len(events) == 1
    assert events[0]["delta_pieces"] == 3
    assert repo.runs[run_id]["pieces_total"] == 3


def test_pause_with_pulse_down_keeps_pieces_and_no_event(monkeypatch):
    service, repo, pulse, session, run_id = _setup()
    monkeypatch.setattr(
        pulse,
        "fetch_device_snapshot",
        lambda *a, **k: (_ for _ in ()).throw(PulseGatewayError("down")),
    )
    payload = service.pause_run(run_id, session_token=session)
    assert payload["status"] == "paused"
    assert repo.runs[run_id]["pieces_total"] == 0
    assert _events(repo, run_id) == []


def test_stop_with_pulse_down_keeps_pieces_and_no_event(monkeypatch):
    service, repo, pulse, session, run_id = _setup()
    monkeypatch.setattr(
        pulse,
        "fetch_device_snapshot",
        lambda *a, **k: (_ for _ in ()).throw(PulseGatewayError("down")),
    )
    payload = service.stop_run(run_id, session_token=session)
    assert payload["status"] == "completed"
    assert repo.runs[run_id]["pieces_total"] == 0
    assert _events(repo, run_id) == []


# ---------------------------------------------------------------------------
# Epoch rollover — sem delta líquido não gera evento
# ---------------------------------------------------------------------------


def test_epoch_rollover_without_net_change_emits_no_event():
    service, repo, pulse, _s, run_id = _setup(counter=100, epoch=1)
    _set_counter(pulse, 105, epoch=1)
    service.tick_running_runs()
    assert repo.runs[run_id]["pieces_total"] == 5

    # epoch bump: segmento rola preservando o total conhecido
    _set_counter(pulse, 40, epoch=2)
    service.tick_running_runs()

    events = _events(repo, run_id)
    assert len(events) == 1  # só o +5 de produção
    assert events[0]["event_type"] == "production"
    assert repo.runs[run_id]["pieces_total"] == 5
    segs = repo.segments[run_id]
    assert segs[0]["end_reason"] == "epoch_change"
    assert segs[-1]["anchor_epoch"] == 2


# ---------------------------------------------------------------------------
# Concorrência — observação stale não vira correction falsa
# ---------------------------------------------------------------------------


def test_stale_observation_is_ignored(monkeypatch):
    service, repo, pulse, _s, run_id = _setup()
    _set_counter(pulse, 101)  # writer A observa +1 a partir do baseline 0

    # writer B grava 2 primeiro (simula outra transação entre observação e lock)
    real_lock = repo.lock_run
    bumped = {"done": False}

    def racy_lock(rid, *, conn=None):
        if not bumped["done"]:
            bumped["done"] = True
            repo.runs[rid]["pieces_total"] = 2
        return real_lock(rid, conn=conn)

    monkeypatch.setattr(repo, "lock_run", racy_lock)
    service.tick_running_runs()

    assert repo.runs[run_id]["pieces_total"] == 2
    assert _events(repo, run_id) == []  # observação stale ignorada, sem correction


def test_stale_observation_reconciles_on_next_tick(monkeypatch):
    service, repo, pulse, _s, run_id = _setup()
    _set_counter(pulse, 103)

    real_lock = repo.lock_run
    bumped = {"done": False}

    def racy_lock(rid, *, conn=None):
        if not bumped["done"]:
            bumped["done"] = True
            repo.runs[rid]["pieces_total"] = 2
        return real_lock(rid, conn=conn)

    monkeypatch.setattr(repo, "lock_run", racy_lock)
    service.tick_running_runs()
    assert _events(repo, run_id) == []

    monkeypatch.setattr(repo, "lock_run", real_lock)
    service.tick_running_runs()
    events = _events(repo, run_id)
    assert len(events) == 1
    assert events[0]["delta_pieces"] == 1  # 2 -> 3
    assert repo.runs[run_id]["pieces_total"] == 3


# ---------------------------------------------------------------------------
# Atomicidade — falha no evento faz rollback do update do run
# ---------------------------------------------------------------------------


def test_count_event_failure_rolls_back_pieces_update():
    service, repo, pulse, _s, run_id = _setup()
    _set_counter(pulse, 105)
    repo.fail_next_count_event = True
    run = repo.get_run(run_id)
    with pytest.raises(RuntimeError):
        service._tick_run(run)
    assert repo.runs[run_id]["pieces_total"] == 0
    assert _events(repo, run_id) == []


# ---------------------------------------------------------------------------
# Integração Postgres — PC_TEST_MES_DB=1
# ---------------------------------------------------------------------------

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestCountEventsPostgres:
    @pytest.fixture()
    def repo(self):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )
        from production_control_app.infrastructure.persistence.postgres_production_run_repository import (  # noqa: E501
            PostgresProductionRunRepository,
        )

        wc = "ZZ-TEST-COUNT"
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {PC_SCHEMA_NAME}.production_runs WHERE work_center = %s",
                    (wc,),
                )
            conn.commit()
        yield PostgresProductionRunRepository()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {PC_SCHEMA_NAME}.production_runs WHERE work_center = %s",
                    (wc,),
                )
            conn.commit()

    def _create_run(self, repo):
        return repo.create_run_with_segment(
            branch="01",
            work_center="ZZ-TEST-COUNT",
            production_order="OPCOUNT",
            operation_code="10",
            device_id="00000000-0000-4000-8000-0000000000b1",
            operator_code="USR01",
            operator_name=None,
            bench_session_id=None,
            planned_qty_snapshot=1.0,
            target_pieces_snapshot=100,
            anchor_counter=0,
            anchor_epoch=0,
        )

    def test_append_and_list_chronological(self, repo):
        run = self._create_run(repo)
        at1 = datetime.now(timezone.utc)
        at2 = at1 + timedelta(seconds=1)
        with repo.transaction() as conn:
            repo.append_count_event(
                run_id=run["id"],
                pieces_total=5,
                delta_pieces=5,
                event_type="production",
                occurred_at=at1,
                conn=conn,
            )
            repo.append_count_event(
                run_id=run["id"],
                pieces_total=4,
                delta_pieces=-1,
                event_type="correction",
                occurred_at=at2,
                conn=conn,
            )
        events = repo.list_count_events(run["id"])
        assert [e["event_type"] for e in events] == ["production", "correction"]
        assert events[0]["delta_pieces"] == 5
        assert events[1]["delta_pieces"] == -1
        assert set(events[0].keys()) == {
            "id",
            "run_id",
            "pieces_total",
            "delta_pieces",
            "event_type",
            "occurred_at",
            "created_at",
        }

    def test_append_requires_conn(self, repo):
        run = self._create_run(repo)
        with pytest.raises(ValueError):
            repo.append_count_event(
                run_id=run["id"],
                pieces_total=1,
                delta_pieces=1,
                event_type="production",
                occurred_at=datetime.now(timezone.utc),
                conn=None,
            )

    def test_constraints_reject_invalid_events(self, repo):
        import psycopg

        run = self._create_run(repo)
        at = datetime.now(timezone.utc)
        with pytest.raises(psycopg.errors.CheckViolation):
            with repo.transaction() as conn:
                repo.append_count_event(
                    run_id=run["id"],
                    pieces_total=0,
                    delta_pieces=0,
                    event_type="production",
                    occurred_at=at,
                    conn=conn,
                )
        with pytest.raises(psycopg.errors.CheckViolation):
            with repo.transaction() as conn:
                repo.append_count_event(
                    run_id=run["id"],
                    pieces_total=-1,
                    delta_pieces=-2,
                    event_type="correction",
                    occurred_at=at,
                    conn=conn,
                )
        with pytest.raises(psycopg.errors.CheckViolation):
            with repo.transaction() as conn:
                repo.append_count_event(
                    run_id=run["id"],
                    pieces_total=1,
                    delta_pieces=1,
                    event_type="baseline",
                    occurred_at=at,
                    conn=conn,
                )

    def test_update_and_event_rollback_together(self, repo):
        import psycopg

        run = self._create_run(repo)
        at = datetime.now(timezone.utc)
        with pytest.raises(psycopg.errors.CheckViolation):
            with repo.transaction() as conn:
                repo.update_run_pieces(
                    run["id"],
                    pieces_total=7,
                    open_segment_pieces=7,
                    conn=conn,
                )
                repo.append_count_event(
                    run_id=run["id"],
                    pieces_total=7,
                    delta_pieces=0,  # viola CHECK — rollback de ambos
                    event_type="production",
                    occurred_at=at,
                    conn=conn,
                )
        assert repo.get_run(run["id"])["pieces_total"] == 0
        assert repo.list_count_events(run["id"]) == []

    def test_event_rollback_when_run_update_fails(self, repo):
        import psycopg

        run = self._create_run(repo)
        at = datetime.now(timezone.utc)
        with pytest.raises(psycopg.Error):
            with repo.transaction() as conn:
                repo.append_count_event(
                    run_id=run["id"],
                    pieces_total=3,
                    delta_pieces=3,
                    event_type="production",
                    occurred_at=at,
                    conn=conn,
                )
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM tabela_inexistente")
        assert repo.list_count_events(run["id"]) == []

    def test_cascade_deletes_events_with_run(self, repo):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        run = self._create_run(repo)
        with repo.transaction() as conn:
            repo.append_count_event(
                run_id=run["id"],
                pieces_total=1,
                delta_pieces=1,
                event_type="production",
                occurred_at=datetime.now(timezone.utc),
                conn=conn,
            )
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {PC_SCHEMA_NAME}.production_runs WHERE id = %s::uuid",
                    (run["id"],),
                )
            conn.commit()
        assert repo.list_count_events(run["id"]) == []
