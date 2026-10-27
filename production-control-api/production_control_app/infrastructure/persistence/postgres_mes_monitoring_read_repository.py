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
_TREATMENTS = f"{PC_SCHEMA_NAME}.mes_downtime_treatments"


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
            rows = [dict(row) for row in cur.fetchall()]

            # PC-MES-CT-AUTONOMOUS-DOWNTIME: CTs com fato MES aberto e SEM
            # run ativo (monitoramento autônomo) — linhas com run_id NULL
            # mantêm o mesmo shape; consumidores distinguem por
            # run_id/monitored.
            cur.execute(
                f"""
                SELECT NULL::text AS run_id, s.branch, s.work_center,
                       NULL AS run_status,
                       NULL AS production_order, NULL AS operation_code,
                       NULL AS operator_code, NULL AS operator_name,
                       NULL AS pieces_total, NULL AS target_pieces,
                       NULL AS last_count_activity_at,
                       NULL AS run_started_at, NULL AS run_ended_at,
                       NULL AS ideal_cycle_seconds_snapshot,
                       NULL AS standard_time_source,
                       NULL AS standard_time_data_quality_snapshot,
                       s.id::text AS state_id, s.state AS operational_state,
                       s.started_at AS state_started_at, s.source AS state_source,
                       d.id::text AS downtime_id, d.started_at AS downtime_started_at,
                       d.source AS downtime_source, d.reason_code, d.confirmed, d.note,
                       reason.label AS reason_label, reason.category,
                       TRUE AS autonomous_monitoring
                  FROM {_STATES} s
             LEFT JOIN {_DOWNTIMES} d ON d.state_event_id = s.id AND d.ended_at IS NULL
             LEFT JOIN {_REASONS} reason ON reason.code = d.reason_code
                 WHERE s.branch = %s AND s.ended_at IS NULL AND s.run_id IS NULL
              ORDER BY s.work_center, s.started_at
                """,
                (branch,),
            )
            rows.extend(dict(row) for row in cur.fetchall())
            for row in rows:
                row.setdefault("autonomous_monitoring", False)
            return rows

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

    def has_activity_in_period(
        self,
        *,
        branch: str,
        work_center: str,
        period_from: datetime,
        period_to: datetime,
    ) -> bool:
        """Existe algum fato MES do posto sobrepondo o período?

        Verificação de existência (sem montar timeline): cobre vínculo
        removido no meio do dia — run/evento criado antes do desvínculo
        continua provando que o posto é sensorizado naquele dia civil.
        """
        params = (branch, work_center, period_to, period_from)
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT EXISTS (
                         SELECT 1 FROM {_STATES} s
                          WHERE s.branch = %s AND s.work_center = %s
                            AND s.started_at < %s
                            AND (s.ended_at IS NULL OR s.ended_at >= %s)
                       )
                    OR EXISTS (
                         SELECT 1 FROM {_DOWNTIMES} d
                          WHERE d.branch = %s AND d.work_center = %s
                            AND d.started_at < %s
                            AND (d.ended_at IS NULL OR d.ended_at >= %s)
                       )
                    OR EXISTS (
                         SELECT 1 FROM {_RUNS} r
                          WHERE r.branch = %s AND r.work_center = %s
                            AND r.started_at < %s
                            AND (r.ended_at IS NULL OR r.ended_at >= %s)
                       ) AS has_activity
                """,
                [*params, *params, *params],
            )
            return bool(cur.fetchone()["has_activity"])

    def list_downtimes(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime | None,
        period_to: datetime | None,
        reason_code: str | None = None,
        source: str | None = None,
        classification: str | None = None,
        status: str | None = None,
        sort: str | None = None,
        downtime_id: str | None = None,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        where, params = self._downtime_filter_clauses(
            branch=branch,
            work_center=work_center,
            period_from=period_from,
            period_to=period_to,
            reason_code=reason_code,
            source=source,
            classification=classification,
            status=status,
            downtime_id=downtime_id,
        )
        # Ordenação por whitelist — valores do contrato nunca viram SQL livre.
        order = (
            "d.started_at ASC, d.id ASC"
            if sort == "oldest"
            else "d.started_at DESC, d.id DESC"
        )
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total FROM {_DOWNTIMES} d WHERE {where}", params)
            total = int(cur.fetchone()["total"])
            cur.execute(
                f"""
                SELECT d.id::text AS id, d.run_id::text AS run_id, d.branch,
                       d.work_center, d.production_order, d.operation_code,
                       d.started_at, d.ended_at, d.source, d.reason_code,
                       reason.label AS reason_label, reason.category,
                       d.confirmed, d.confirmed_at, d.confirmed_by_type,
                       d.confirmed_by_ref, d.note, d.updated_at
                  FROM {_DOWNTIMES} d
             LEFT JOIN {_REASONS} reason ON reason.code = d.reason_code
                 WHERE {where}
              ORDER BY {order}
                 LIMIT %s OFFSET %s
                """,
                [*params, page_size, (page - 1) * page_size],
            )
            rows = [dict(row) for row in cur.fetchall()]
        return rows, total

    @staticmethod
    def _downtime_filter_clauses(
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime | None,
        period_to: datetime | None,
        reason_code: str | None,
        source: str | None,
        classification: str | None,
        status: str | None = None,
        downtime_id: str | None = None,
    ) -> tuple[str, list[Any]]:
        # Seleção temporal e de filtros compartilhada entre listagem e
        # analytics — o mesmo universo elegível, sem divergência.
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
        if reason_code:
            clauses.append("d.reason_code = %s")
            params.append(reason_code)
        if source:
            clauses.append("d.source = %s")
            params.append(source)
        if classification == "confirmed":
            clauses.append("d.confirmed IS TRUE")
        elif classification == "pending":
            clauses.append("d.confirmed IS NOT TRUE")
        if status == "open":
            clauses.append("d.ended_at IS NULL")
        elif status == "closed":
            clauses.append("d.ended_at IS NOT NULL")
        if downtime_id:
            clauses.append("d.id = %s")
            params.append(downtime_id)
        return " AND ".join(clauses), params

    def list_downtime_analytics_facts(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime,
        period_to: datetime,
        reason_code: str | None = None,
        source: str | None = None,
        classification: str | None = None,
        status: str | None = None,
        max_facts: int = 20000,
    ) -> dict[str, Any]:
        # Fatos completos da janela para agregação gerencial: mesmo WHERE
        # da listagem (sem paginação/sort), só as colunas necessárias ao
        # agregador. O fetch de max_facts + 1 permite detectar leitura
        # truncada e sinalizar partial em quality.
        where, params = self._downtime_filter_clauses(
            branch=branch,
            work_center=work_center,
            period_from=period_from,
            period_to=period_to,
            reason_code=reason_code,
            source=source,
            classification=classification,
            status=status,
        )
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT d.id::text AS id, d.work_center, d.started_at,
                       d.ended_at, d.source, d.reason_code,
                       reason.label AS reason_label, reason.category,
                       d.confirmed
                  FROM {_DOWNTIMES} d
             LEFT JOIN {_REASONS} reason ON reason.code = d.reason_code
                 WHERE {where}
              ORDER BY d.started_at ASC, d.id ASC
                 LIMIT %s
                """,
                [*params, max_facts + 1],
            )
            rows = [dict(row) for row in cur.fetchall()]
        capped = len(rows) > max_facts
        return {"facts": rows[:max_facts], "capped": capped}

    def list_downtime_export(
        self,
        *,
        branch: str,
        work_center: str | None,
        period_from: datetime | None,
        period_to: datetime | None,
        reason_code: str | None = None,
        source: str | None = None,
        classification: str | None = None,
        status: str | None = None,
        pendency: bool = False,
        max_facts: int,
    ) -> dict[str, Any]:
        """Universo completo da exportação (Etapa 5): mesmo WHERE da
        listagem/analytics — nunca a página atual da tela. O LEFT JOIN com
        o tratamento gerencial projeta status/vínculo sem duplicar o fato;
        pendency restringe ao relatório de pendências (sem classificação
        confirmada OU tratamento aberto). Cap de fatos sinaliza capped
        para o consumidor marcar o arquivo como parcial."""
        where, params = self._downtime_filter_clauses(
            branch=branch,
            work_center=work_center,
            period_from=period_from,
            period_to=period_to,
            reason_code=reason_code,
            source=source,
            classification=classification,
            status=status,
        )
        if pendency:
            where += (
                " AND (d.confirmed IS NOT TRUE"
                " OR t.status IN ('pending', 'referred'))"
            )
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                  FROM {_DOWNTIMES} d
             LEFT JOIN {_TREATMENTS} t ON t.downtime_id = d.id
                 WHERE {where}
                """,
                params,
            )
            total = int(cur.fetchone()["total"])
            cur.execute(
                f"""
                SELECT d.id::text AS id, d.run_id::text AS run_id,
                       d.work_center, d.production_order, d.operation_code,
                       d.started_at, d.ended_at, d.source, d.reason_code,
                       reason.label AS reason_label, reason.category,
                       d.confirmed, d.confirmed_at, d.confirmed_by_type,
                       d.confirmed_by_ref, d.note, d.updated_at,
                       t.status AS treatment_status,
                       t.request_id::text AS treatment_request_id,
                       t.request_type_code AS treatment_request_type,
                       t.concluded_at AS treatment_concluded_at
                  FROM {_DOWNTIMES} d
             LEFT JOIN {_REASONS} reason ON reason.code = d.reason_code
             LEFT JOIN {_TREATMENTS} t ON t.downtime_id = d.id
                 WHERE {where}
              ORDER BY d.started_at ASC, d.id ASC
                 LIMIT %s
                """,
                [*params, max_facts + 1],
            )
            rows = [dict(row) for row in cur.fetchall()]
        capped = len(rows) > max_facts
        return {"items": rows[:max_facts], "total": total, "capped": capped}
