from __future__ import annotations

import hashlib
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from psycopg.errors import UniqueViolation

from production_control_app.config import settings
from production_control_app.domain.errors import ProductionRunConflict
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_SESSIONS = f"{PC_SCHEMA_NAME}.operator_bench_sessions"
_RUNS = f"{PC_SCHEMA_NAME}.production_runs"
_SEGMENTS = f"{PC_SCHEMA_NAME}.production_run_segments"
_COUNT_EVENTS = f"{PC_SCHEMA_NAME}.production_run_count_events"

# Snapshots de Performance congelados no Play (V013) — imutáveis após criados.
_RUN_SNAPSHOT_COLUMNS = (
    "ideal_cycle_seconds_snapshot, setup_seconds_snapshot, "
    "standard_time_source, standard_time_data_quality_snapshot, "
    "workstation_type_snapshot, pieces_per_pulse_snapshot"
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_session_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


class PostgresProductionRunRepository:
    @contextmanager
    def transaction(self) -> Iterator[Any]:
        """Uma conexão/transação compartilhada: commit ao sair, rollback em erro.

        Permite que transições do run (pause/resume/stop) gravem run, segmentos
        e fatos MES atomicamente. Nunca mantenha chamada HTTP ao Pulse dentro.
        """
        conn = get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def lock_run(self, run_id: str, *, conn: Any) -> dict[str, Any] | None:
        """SELECT FOR UPDATE: serializa transições concorrentes do mesmo run."""
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id::text AS id, branch, work_center, production_order,
                       operation_code, device_id::text AS device_id,
                       operator_code, operator_name, last_count_activity_at,
                       bench_session_id::text AS bench_session_id,
                       status, started_at, ended_at, pieces_total,
                       planned_qty_snapshot, target_pieces_snapshot,
                       {_RUN_SNAPSHOT_COLUMNS},
                       created_at, updated_at
                FROM {_RUNS}
                WHERE id = %s::uuid
                FOR UPDATE
                """,
                (run_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def create_bench_session(
        self,
        *,
        branch: str,
        work_center: str,
        operator_code: str,
        operator_name: str | None,
        raw_token: str,
        ttl_hours: int | None = None,
    ) -> dict[str, Any]:
        hours = ttl_hours if ttl_hours is not None else settings.PC_BENCH_SESSION_TTL_HOURS
        expires_at = _utc_now() + timedelta(hours=max(1, int(hours)))
        token_hash = hash_session_token(raw_token)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_SESSIONS} (
                        branch, work_center, operator_code, operator_name,
                        session_token_hash, expires_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id::text AS id, branch, work_center, operator_code,
                              operator_name, expires_at, created_at
                    """,
                    (
                        branch,
                        work_center,
                        operator_code,
                        operator_name,
                        token_hash,
                        expires_at,
                    ),
                )
                row = dict(cur.fetchone())
            conn.commit()
        return row

    def get_bench_session_by_token(self, raw_token: str) -> dict[str, Any] | None:
        token_hash = hash_session_token(raw_token)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id::text AS id, branch, work_center, operator_code,
                           operator_name, expires_at, created_at, ended_at
                    FROM {_SESSIONS}
                    WHERE session_token_hash = %s
                    LIMIT 1
                    """,
                    (token_hash,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def end_bench_session(self, session_id: str) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_SESSIONS}
                       SET ended_at = NOW()
                     WHERE id = %s::uuid AND ended_at IS NULL
                    """,
                    (session_id,),
                )
            conn.commit()

    def get_active_run(self, *, branch: str, work_center: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id::text AS id, branch, work_center, production_order,
                           operation_code, device_id::text AS device_id,
                           operator_code, operator_name,
                           bench_session_id::text AS bench_session_id,
                           status, started_at, ended_at, pieces_total,
                           planned_qty_snapshot, target_pieces_snapshot,
                           {_RUN_SNAPSHOT_COLUMNS},
                           last_count_activity_at, created_at, updated_at
                    FROM {_RUNS}
                    WHERE branch = %s
                      AND work_center = %s
                      AND status IN ('running', 'paused')
                    LIMIT 1
                    """,
                    (branch, work_center),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id::text AS id, branch, work_center, production_order,
                           operation_code, device_id::text AS device_id,
                           operator_code, operator_name,
                           bench_session_id::text AS bench_session_id,
                           status, started_at, ended_at, pieces_total,
                           planned_qty_snapshot, target_pieces_snapshot,
                           {_RUN_SNAPSHOT_COLUMNS},
                           last_count_activity_at, created_at, updated_at
                    FROM {_RUNS}
                    WHERE id = %s::uuid
                    LIMIT 1
                    """,
                    (run_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def list_open_runs_by_branch(self, *, branch: str) -> list[dict[str, Any]]:
        """Runs abertos (running/paused) da filial — fonte do «em produção» do cockpit."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id::text AS id, branch, work_center, production_order,
                           operation_code, operator_code, operator_name, status,
                           started_at
                    FROM {_RUNS}
                    WHERE branch = %s
                      AND status IN ('running', 'paused')
                    """
                    ,
                    (branch,),
                )
                return [dict(row) for row in cur.fetchall()]

    def list_open_running_runs(self) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id::text AS id, branch, work_center, production_order,
                           operation_code, device_id::text AS device_id,
                           operator_code, operator_name, status, started_at,
                           pieces_total, planned_qty_snapshot, target_pieces_snapshot,
                           {_RUN_SNAPSHOT_COLUMNS},
                           last_count_activity_at
                    FROM {_RUNS}
                    WHERE status = 'running'
                    ORDER BY started_at
                    """
                )
                return [dict(row) for row in cur.fetchall()]

    def create_run_with_segment(
        self,
        *,
        branch: str,
        work_center: str,
        production_order: str,
        operation_code: str,
        device_id: str,
        operator_code: str,
        operator_name: str | None,
        bench_session_id: str | None,
        planned_qty_snapshot: float | None,
        target_pieces_snapshot: int | None,
        anchor_counter: int,
        anchor_epoch: int,
        ideal_cycle_seconds_snapshot: float | None = None,
        setup_seconds_snapshot: float | None = None,
        standard_time_source: str | None = None,
        standard_time_data_quality_snapshot: str | None = None,
        workstation_type_snapshot: str | None = None,
        pieces_per_pulse_snapshot: float | None = None,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        if conn is not None:
            return self._create_run_with_segment(
                conn,
                branch=branch,
                work_center=work_center,
                production_order=production_order,
                operation_code=operation_code,
                device_id=device_id,
                operator_code=operator_code,
                operator_name=operator_name,
                bench_session_id=bench_session_id,
                planned_qty_snapshot=planned_qty_snapshot,
                target_pieces_snapshot=target_pieces_snapshot,
                anchor_counter=anchor_counter,
                anchor_epoch=anchor_epoch,
                ideal_cycle_seconds_snapshot=ideal_cycle_seconds_snapshot,
                setup_seconds_snapshot=setup_seconds_snapshot,
                standard_time_source=standard_time_source,
                standard_time_data_quality_snapshot=standard_time_data_quality_snapshot,
                workstation_type_snapshot=workstation_type_snapshot,
                pieces_per_pulse_snapshot=pieces_per_pulse_snapshot,
            )
        with get_connection() as own:
            row = self._create_run_with_segment(
                own,
                branch=branch,
                work_center=work_center,
                production_order=production_order,
                operation_code=operation_code,
                device_id=device_id,
                operator_code=operator_code,
                operator_name=operator_name,
                bench_session_id=bench_session_id,
                planned_qty_snapshot=planned_qty_snapshot,
                target_pieces_snapshot=target_pieces_snapshot,
                anchor_counter=anchor_counter,
                anchor_epoch=anchor_epoch,
                ideal_cycle_seconds_snapshot=ideal_cycle_seconds_snapshot,
                setup_seconds_snapshot=setup_seconds_snapshot,
                standard_time_source=standard_time_source,
                standard_time_data_quality_snapshot=standard_time_data_quality_snapshot,
                workstation_type_snapshot=workstation_type_snapshot,
                pieces_per_pulse_snapshot=pieces_per_pulse_snapshot,
            )
            own.commit()
            return row

    def _create_run_with_segment(self, conn: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_RUNS} (
                        branch, work_center, production_order, operation_code,
                        device_id, operator_code, operator_name, bench_session_id,
                        status, planned_qty_snapshot, target_pieces_snapshot,
                        ideal_cycle_seconds_snapshot, setup_seconds_snapshot,
                        standard_time_source, standard_time_data_quality_snapshot,
                        workstation_type_snapshot, pieces_per_pulse_snapshot,
                        last_count_activity_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s::uuid, %s, %s, %s::uuid,
                        'running', %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        NOW()
                    )
                    RETURNING id::text AS id, branch, work_center, production_order,
                              operation_code, device_id::text AS device_id,
                              operator_code, operator_name,
                              bench_session_id::text AS bench_session_id,
                              status, started_at, ended_at, pieces_total,
                              planned_qty_snapshot, target_pieces_snapshot,
                              {_RUN_SNAPSHOT_COLUMNS},
                              last_count_activity_at, created_at, updated_at
                    """,
                    (
                        kwargs["branch"],
                        kwargs["work_center"],
                        kwargs["production_order"],
                        kwargs["operation_code"],
                        kwargs["device_id"],
                        kwargs["operator_code"],
                        kwargs["operator_name"],
                        kwargs["bench_session_id"],
                        kwargs["planned_qty_snapshot"],
                        kwargs["target_pieces_snapshot"],
                        kwargs["ideal_cycle_seconds_snapshot"],
                        kwargs["setup_seconds_snapshot"],
                        kwargs["standard_time_source"],
                        kwargs["standard_time_data_quality_snapshot"],
                        kwargs["workstation_type_snapshot"],
                        kwargs["pieces_per_pulse_snapshot"],
                    ),
                )
                run = dict(cur.fetchone())
        except UniqueViolation as exc:
            raise ProductionRunConflict(
                "Já existe produção em andamento neste posto."
            ) from exc
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_SEGMENTS} (
                    run_id, device_id, anchor_counter, anchor_epoch
                )
                VALUES (%s::uuid, %s::uuid, %s, %s)
                RETURNING id::text AS id, run_id::text AS run_id,
                          device_id::text AS device_id,
                          anchor_counter, anchor_epoch, started_at,
                          ended_at, pieces, end_reason
                """,
                (run["id"], kwargs["device_id"], int(kwargs["anchor_counter"]), int(kwargs["anchor_epoch"])),
            )
            segment = dict(cur.fetchone())
        run["open_segment"] = segment
        return run

    def get_open_segment(self, run_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id::text AS id, run_id::text AS run_id,
                           device_id::text AS device_id,
                           anchor_counter, anchor_epoch, started_at,
                           ended_at, pieces, end_reason
                    FROM {_SEGMENTS}
                    WHERE run_id = %s::uuid AND ended_at IS NULL
                    LIMIT 1
                    """,
                    (run_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def list_segments(self, run_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id::text AS id, run_id::text AS run_id,
                           device_id::text AS device_id,
                           anchor_counter, anchor_epoch, started_at,
                           ended_at, pieces, end_reason
                    FROM {_SEGMENTS}
                    WHERE run_id = %s::uuid
                    ORDER BY started_at
                    """,
                    (run_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    def close_segment_open_new(
        self,
        *,
        run_id: str,
        segment_id: str,
        pieces: int,
        end_reason: str,
        device_id: str,
        anchor_counter: int,
        anchor_epoch: int,
        pieces_total: int,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        if conn is not None:
            return self._close_segment_open_new(
                conn,
                run_id=run_id,
                segment_id=segment_id,
                pieces=pieces,
                end_reason=end_reason,
                device_id=device_id,
                anchor_counter=anchor_counter,
                anchor_epoch=anchor_epoch,
                pieces_total=pieces_total,
            )
        with get_connection() as own:
            row = self._close_segment_open_new(
                own,
                run_id=run_id,
                segment_id=segment_id,
                pieces=pieces,
                end_reason=end_reason,
                device_id=device_id,
                anchor_counter=anchor_counter,
                anchor_epoch=anchor_epoch,
                pieces_total=pieces_total,
            )
            own.commit()
            return row

    def _close_segment_open_new(self, conn: Any, **kwargs: Any) -> dict[str, Any]:
        with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_SEGMENTS}
                       SET ended_at = NOW(),
                           pieces = %s,
                           end_reason = %s
                     WHERE id = %s::uuid AND ended_at IS NULL
                    """,
                    (int(kwargs["pieces"]), kwargs["end_reason"], kwargs["segment_id"]),
                )
                cur.execute(
                    f"""
                    INSERT INTO {_SEGMENTS} (
                        run_id, device_id, anchor_counter, anchor_epoch
                    )
                    VALUES (%s::uuid, %s::uuid, %s, %s)
                    RETURNING id::text AS id, run_id::text AS run_id,
                              device_id::text AS device_id,
                              anchor_counter, anchor_epoch, started_at,
                              ended_at, pieces, end_reason
                    """,
                    (
                        kwargs["run_id"],
                        kwargs["device_id"],
                        int(kwargs["anchor_counter"]),
                        int(kwargs["anchor_epoch"]),
                    ),
                )
                segment = dict(cur.fetchone())
                cur.execute(
                    f"""
                    UPDATE {_RUNS}
                       SET pieces_total = %s,
                           updated_at = NOW()
                     WHERE id = %s::uuid
                    RETURNING id::text AS id, pieces_total, status
                    """,
                    (int(kwargs["pieces_total"]), kwargs["run_id"]),
                )
                run = dict(cur.fetchone())
        run["open_segment"] = segment
        return run

    def update_run_pieces(
        self,
        run_id: str,
        *,
        pieces_total: int,
        open_segment_pieces: int,
        activity_at: datetime | None = None,
        conn: Any | None = None,
    ) -> None:
        if conn is not None:
            self._update_run_pieces(
                conn,
                run_id,
                pieces_total=pieces_total,
                open_segment_pieces=open_segment_pieces,
                activity_at=activity_at,
            )
            return
        with get_connection() as own:
            self._update_run_pieces(
                own,
                run_id,
                pieces_total=pieces_total,
                open_segment_pieces=open_segment_pieces,
                activity_at=activity_at,
            )
            own.commit()

    def init_count_activity(
        self, run_id: str, *, at: datetime, conn: Any | None = None
    ) -> None:
        """Baseline de runs legados (NULL): só grava se ainda não houver."""
        sql = (
            f"UPDATE {_RUNS} SET last_count_activity_at = %s "
            "WHERE id = %s::uuid AND last_count_activity_at IS NULL"
        )
        if conn is not None:
            with conn.cursor() as cur:
                cur.execute(sql, (at, run_id))
            return
        with get_connection() as own:
            with own.cursor() as cur:
                cur.execute(sql, (at, run_id))
            own.commit()

    def _update_run_pieces(self, conn: Any, run_id: str, **kwargs: Any) -> None:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {_RUNS}
                   SET pieces_total = %s,
                       last_count_activity_at = COALESCE(%s, last_count_activity_at),
                       updated_at = NOW()
                 WHERE id = %s::uuid AND status = 'running'
                """,
                (int(kwargs["pieces_total"]), kwargs.get("activity_at"), run_id),
            )
            cur.execute(
                f"""
                UPDATE {_SEGMENTS}
                   SET pieces = %s
                 WHERE run_id = %s::uuid AND ended_at IS NULL
                """,
                (int(kwargs["open_segment_pieces"]), run_id),
            )

    def set_run_status(
        self,
        run_id: str,
        *,
        status: str,
        pieces_total: int | None = None,
        close_open_segment: bool = False,
        open_segment_pieces: int = 0,
        end_reason: str | None = None,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        if conn is not None:
            return self._set_run_status(
                conn,
                run_id,
                status=status,
                pieces_total=pieces_total,
                close_open_segment=close_open_segment,
                open_segment_pieces=open_segment_pieces,
                end_reason=end_reason,
            )
        with get_connection() as own:
            row = self._set_run_status(
                own,
                run_id,
                status=status,
                pieces_total=pieces_total,
                close_open_segment=close_open_segment,
                open_segment_pieces=open_segment_pieces,
                end_reason=end_reason,
            )
            own.commit()
            return row

    def _set_run_status(self, conn: Any, run_id: str, **kwargs: Any) -> dict[str, Any]:
        with conn.cursor() as cur:
            if kwargs["close_open_segment"]:
                cur.execute(
                    f"""
                    UPDATE {_SEGMENTS}
                       SET ended_at = NOW(),
                           pieces = %s,
                           end_reason = %s
                     WHERE run_id = %s::uuid AND ended_at IS NULL
                    """,
                    (int(kwargs["open_segment_pieces"]), kwargs["end_reason"], run_id),
                )
            sets = ["status = %s", "updated_at = NOW()"]
            params: list[Any] = [kwargs["status"]]
            if kwargs["status"] in {"completed", "aborted"}:
                sets.append("ended_at = NOW()")
            if kwargs["pieces_total"] is not None:
                sets.append("pieces_total = %s")
                params.append(int(kwargs["pieces_total"]))
            params.append(run_id)
            cur.execute(
                f"""
                UPDATE {_RUNS}
                   SET {", ".join(sets)}
                 WHERE id = %s::uuid
                RETURNING id::text AS id, branch, work_center, production_order,
                          operation_code, device_id::text AS device_id,
                          operator_code, operator_name, status, started_at,
                          ended_at, pieces_total, planned_qty_snapshot,
                          target_pieces_snapshot, {_RUN_SNAPSHOT_COLUMNS},
                          last_count_activity_at
                """,
                params,
            )
            row = dict(cur.fetchone())
        return row

    def reopen_segment_on_resume(
        self,
        *,
        run_id: str,
        device_id: str,
        anchor_counter: int,
        anchor_epoch: int,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        if conn is not None:
            return self._reopen_segment_on_resume(
                conn,
                run_id=run_id,
                device_id=device_id,
                anchor_counter=anchor_counter,
                anchor_epoch=anchor_epoch,
            )
        with get_connection() as own:
            row = self._reopen_segment_on_resume(
                own,
                run_id=run_id,
                device_id=device_id,
                anchor_counter=anchor_counter,
                anchor_epoch=anchor_epoch,
            )
            own.commit()
            return row

    def _reopen_segment_on_resume(self, conn: Any, **kwargs: Any) -> dict[str, Any]:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {_RUNS}
                   SET status = 'running',
                       updated_at = NOW()
                 WHERE id = %s::uuid
                RETURNING id::text AS id, status, pieces_total
                """,
                (kwargs["run_id"],),
            )
            run = dict(cur.fetchone())
            cur.execute(
                f"""
                INSERT INTO {_SEGMENTS} (
                    run_id, device_id, anchor_counter, anchor_epoch
                )
                VALUES (%s::uuid, %s::uuid, %s, %s)
                RETURNING id::text AS id, run_id::text AS run_id,
                          device_id::text AS device_id,
                          anchor_counter, anchor_epoch, started_at,
                          ended_at, pieces, end_reason
                """,
                (
                    kwargs["run_id"],
                    kwargs["device_id"],
                    int(kwargs["anchor_counter"]),
                    int(kwargs["anchor_epoch"]),
                ),
            )
            segment = dict(cur.fetchone())
        run["open_segment"] = segment
        return run

    # ------------------------------------------------------------------
    # Count events (V014) — trilha append-only de mudanças de pieces_total.
    # ------------------------------------------------------------------

    def append_count_event(
        self,
        *,
        run_id: str,
        pieces_total: int,
        delta_pieces: int,
        event_type: str,
        occurred_at: datetime,
        conn: Any,
    ) -> dict[str, Any]:
        """Append de um fato de contagem na MESMA transação do run.

        conn é obrigatório por design: o evento nunca pode fazer commit
        independente da alteração de production_runs.pieces_total — ou
        ambos persistem, ou nenhum persiste.
        """
        if conn is None:
            raise ValueError(
                "append_count_event exige conn da transação que altera o run."
            )
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_COUNT_EVENTS} (
                    run_id, pieces_total, delta_pieces, event_type, occurred_at
                )
                VALUES (%s::uuid, %s, %s, %s, %s)
                RETURNING id, run_id::text AS run_id, pieces_total,
                          delta_pieces, event_type, occurred_at, created_at
                """,
                (
                    run_id,
                    int(pieces_total),
                    int(delta_pieces),
                    event_type,
                    occurred_at,
                ),
            )
            return dict(cur.fetchone())

    def list_count_events(self, run_id: str) -> list[dict[str, Any]]:
        """Trilha cronológica do run: occurred_at ASC, id ASC (interna)."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, run_id::text AS run_id, pieces_total,
                           delta_pieces, event_type, occurred_at, created_at
                      FROM {_COUNT_EVENTS}
                     WHERE run_id = %s::uuid
                     ORDER BY occurred_at ASC, id ASC
                    """,
                    (run_id,),
                )
                return [dict(row) for row in cur.fetchall()]
