from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from production_control_app.config import settings
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_SESSIONS = f"{PC_SCHEMA_NAME}.operator_bench_sessions"
_RUNS = f"{PC_SCHEMA_NAME}.production_runs"
_SEGMENTS = f"{PC_SCHEMA_NAME}.production_run_segments"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_session_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


class PostgresProductionRunRepository:
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
                           planned_qty_snapshot, created_at, updated_at
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
                           planned_qty_snapshot, created_at, updated_at
                    FROM {_RUNS}
                    WHERE id = %s::uuid
                    LIMIT 1
                    """,
                    (run_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def list_open_running_runs(self) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id::text AS id, branch, work_center, production_order,
                           operation_code, device_id::text AS device_id,
                           operator_code, operator_name, status, started_at,
                           pieces_total, planned_qty_snapshot
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
        anchor_counter: int,
        anchor_epoch: int,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_RUNS} (
                        branch, work_center, production_order, operation_code,
                        device_id, operator_code, operator_name, bench_session_id,
                        status, planned_qty_snapshot
                    )
                    VALUES (%s, %s, %s, %s, %s::uuid, %s, %s, %s::uuid, 'running', %s)
                    RETURNING id::text AS id, branch, work_center, production_order,
                              operation_code, device_id::text AS device_id,
                              operator_code, operator_name,
                              bench_session_id::text AS bench_session_id,
                              status, started_at, ended_at, pieces_total,
                              planned_qty_snapshot, created_at, updated_at
                    """,
                    (
                        branch,
                        work_center,
                        production_order,
                        operation_code,
                        device_id,
                        operator_code,
                        operator_name,
                        bench_session_id,
                        planned_qty_snapshot,
                    ),
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
                    (run["id"], device_id, int(anchor_counter), int(anchor_epoch)),
                )
                segment = dict(cur.fetchone())
            conn.commit()
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
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_SEGMENTS}
                       SET ended_at = NOW(),
                           pieces = %s,
                           end_reason = %s
                     WHERE id = %s::uuid AND ended_at IS NULL
                    """,
                    (int(pieces), end_reason, segment_id),
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
                    (run_id, device_id, int(anchor_counter), int(anchor_epoch)),
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
                    (int(pieces_total), run_id),
                )
                run = dict(cur.fetchone())
            conn.commit()
        run["open_segment"] = segment
        return run

    def update_run_pieces(self, run_id: str, *, pieces_total: int, open_segment_pieces: int) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_RUNS}
                       SET pieces_total = %s,
                           updated_at = NOW()
                     WHERE id = %s::uuid
                    """,
                    (int(pieces_total), run_id),
                )
                cur.execute(
                    f"""
                    UPDATE {_SEGMENTS}
                       SET pieces = %s
                     WHERE run_id = %s::uuid AND ended_at IS NULL
                    """,
                    (int(open_segment_pieces), run_id),
                )
            conn.commit()

    def set_run_status(
        self,
        run_id: str,
        *,
        status: str,
        pieces_total: int | None = None,
        close_open_segment: bool = False,
        open_segment_pieces: int = 0,
        end_reason: str | None = None,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if close_open_segment:
                    cur.execute(
                        f"""
                        UPDATE {_SEGMENTS}
                           SET ended_at = NOW(),
                               pieces = %s,
                               end_reason = %s
                         WHERE run_id = %s::uuid AND ended_at IS NULL
                        """,
                        (int(open_segment_pieces), end_reason, run_id),
                    )
                sets = ["status = %s", "updated_at = NOW()"]
                params: list[Any] = [status]
                if status in {"completed", "aborted"}:
                    sets.append("ended_at = NOW()")
                if pieces_total is not None:
                    sets.append("pieces_total = %s")
                    params.append(int(pieces_total))
                params.append(run_id)
                cur.execute(
                    f"""
                    UPDATE {_RUNS}
                       SET {", ".join(sets)}
                     WHERE id = %s::uuid
                    RETURNING id::text AS id, branch, work_center, production_order,
                              operation_code, device_id::text AS device_id,
                              operator_code, operator_name, status, started_at,
                              ended_at, pieces_total, planned_qty_snapshot
                    """,
                    params,
                )
                row = dict(cur.fetchone())
            conn.commit()
        return row

    def reopen_segment_on_resume(
        self,
        *,
        run_id: str,
        device_id: str,
        anchor_counter: int,
        anchor_epoch: int,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_RUNS}
                       SET status = 'running',
                           updated_at = NOW()
                     WHERE id = %s::uuid
                    RETURNING id::text AS id, status, pieces_total
                    """,
                    (run_id,),
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
                    (run_id, device_id, int(anchor_counter), int(anchor_epoch)),
                )
                segment = dict(cur.fetchone())
            conn.commit()
        run["open_segment"] = segment
        return run
