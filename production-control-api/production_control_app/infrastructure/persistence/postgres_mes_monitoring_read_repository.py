from __future__ import annotations

from datetime import datetime
from typing import Any

from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_RUNS = f"{PC_SCHEMA_NAME}.production_runs"
_STATES = f"{PC_SCHEMA_NAME}.work_center_state_events"
_DOWNTIMES = f"{PC_SCHEMA_NAME}.downtime_events"
_REASONS = f"{PC_SCHEMA_NAME}.downtime_reason_catalog"


class PostgresMesMonitoringReadRepository:
    def list_live_work_centers(self, *, branch: str) -> list[dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT r.id::text AS run_id, r.branch, r.work_center, r.status AS run_status,
                       r.production_order, r.operation_code, r.operator_code, r.operator_name,
                       r.pieces_total, r.target_pieces_snapshot AS target_pieces,
                       r.last_count_activity_at,
                       r.started_at AS run_started_at, r.ended_at AS run_ended_at,
                       r.ideal_cycle_seconds_snapshot,
                       r.standard_time_source, r.standard_time_data_quality_snapshot,
                       s.id::text AS state_id, s.state AS operational_state,
                       s.started_at AS state_started_at, s.source AS state_source,
                       d.id::text AS downtime_id, d.started_at AS downtime_started_at,
                       d.source AS downtime_source, d.reason_code, d.confirmed, d.note,
                       reason.label AS reason_label, reason.category
                  FROM {_RUNS} r
             LEFT JOIN {_STATES} s
                    ON s.run_id = r.id AND s.ended_at IS NULL
             LEFT JOIN {_DOWNTIMES} d
                    ON d.run_id = r.id AND d.ended_at IS NULL
             LEFT JOIN {_REASONS} reason ON reason.code = d.reason_code
                 WHERE r.branch = %s AND r.status IN ('running', 'paused')
              ORDER BY r.work_center, r.started_at
                """,
                (branch,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id::text AS id, branch, work_center, status, started_at, ended_at,
                       pieces_total, planned_qty_snapshot, target_pieces_snapshot,
                       ideal_cycle_seconds_snapshot, setup_seconds_snapshot,
                       standard_time_source, standard_time_data_quality_snapshot,
                       workstation_type_snapshot, pieces_per_pulse_snapshot,
                       last_count_activity_at
                  FROM {_RUNS}
                 WHERE id = %s::uuid
                 LIMIT 1
                """,
                (run_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def list_timeline_facts(self, run_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT s.id::text AS id, s.state, s.started_at, s.ended_at, s.source,
                       d.id::text AS downtime_id, d.reason_code, reason.label AS reason_label,
                       reason.category, d.confirmed, d.note, d.source AS downtime_source
                  FROM {_STATES} s
             LEFT JOIN {_DOWNTIMES} d ON d.state_event_id = s.id
             LEFT JOIN {_REASONS} reason ON reason.code = d.reason_code
                 WHERE s.run_id = %s::uuid
              ORDER BY s.started_at
                """,
                (run_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_timeline_facts_for_runs(
        self, run_ids: list[str]
    ) -> list[dict[str, Any]]:
        if not run_ids:
            return []
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT s.id::text AS id, s.run_id::text AS run_id,
                       s.state, s.started_at, s.ended_at, s.source,
                       d.id::text AS downtime_id, d.reason_code,
                       reason.label AS reason_label,
                       reason.category, d.confirmed, d.note,
                       d.source AS downtime_source
                  FROM {_STATES} s
             LEFT JOIN {_DOWNTIMES} d ON d.state_event_id = s.id
             LEFT JOIN {_REASONS} reason ON reason.code = d.reason_code
                 WHERE s.run_id = ANY(%s::uuid[])
              ORDER BY s.run_id, s.started_at, s.id
                """,
                (list(run_ids),),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_work_center_timeline_facts(
        self,
        *,
        branch: str,
        work_center: str,
        period_from: datetime,
        period_to: datetime,
    ) -> list[dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT s.id::text AS id, s.branch, s.work_center,
                       s.run_id::text AS run_id, s.state,
                       s.started_at, s.ended_at, s.source,
                       r.production_order, r.operation_code,
                       d.id::text AS downtime_id, d.reason_code,
                       reason.label AS reason_label, reason.category,
                       d.confirmed, d.note, d.source AS downtime_source
                  FROM {_STATES} s
             LEFT JOIN {_RUNS} r ON r.id = s.run_id
             LEFT JOIN {_DOWNTIMES} d ON d.state_event_id = s.id
             LEFT JOIN {_REASONS} reason ON reason.code = d.reason_code
                 WHERE s.branch = %s AND s.work_center = %s
                   AND s.started_at < %s
                   AND (s.ended_at IS NULL OR s.ended_at >= %s)
              ORDER BY s.started_at, s.id
                """,
                (branch, work_center, period_to, period_from),
            )
            return [dict(row) for row in cur.fetchall()]

    def list_downtimes(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime | None,
        period_to: datetime | None,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses = ["d.branch = %s"]
        params: list[Any] = [branch]
        if work_center:
            clauses.append("d.work_center = %s")
            params.append(work_center)
        if period_to is not None:
            clauses.append("d.started_at < %s")
            params.append(period_to)
        if period_from is not None:
            clauses.append("(d.ended_at IS NULL OR d.ended_at >= %s)")
            params.append(period_from)
        where = " AND ".join(clauses)
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM {_DOWNTIMES} d WHERE {where}", params)
            total = int(cur.fetchone()["total"])
            cur.execute(
                f"""
                SELECT d.id::text AS id, d.run_id::text AS run_id, d.branch,
                       d.work_center, d.production_order, d.operation_code,
                       d.started_at, d.ended_at, d.source, d.reason_code,
                       reason.label AS reason_label, reason.category,
                       d.confirmed, d.note
                  FROM {_DOWNTIMES} d
             LEFT JOIN {_REASONS} reason ON reason.code = d.reason_code
                 WHERE {where}
              ORDER BY d.started_at DESC, d.id DESC
                 LIMIT %s OFFSET %s
                """,
                [*params, page_size, (page - 1) * page_size],
            )
            rows = [dict(row) for row in cur.fetchall()]
        return rows, total
