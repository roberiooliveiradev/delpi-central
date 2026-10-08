"""Repositório Postgres — Operator Feedback (impedimentos do operador ao PCP).

Tabela própria e histórica (V016): nenhuma query toca machine_load_* e o
run_id é contexto opcional. A unicidade do impedimento ativo é garantida pelo
índice parcial uq_pc_operator_feedbacks_active — o INSERT confia nela e o
repositório traduz UniqueViolation para o erro de domínio, nunca expondo SQL.

Transições de lifecycle são UPDATEs condicionais atômicos
(WHERE id = ? AND status = esperado): dois analistas do PCP não correm entre
si — só um UPDATE casa a condição.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from psycopg.errors import UniqueViolation

from production_control_app.domain.errors import OperatorFeedbackConflict
from production_control_app.domain.operator_feedback import (
    ACTIVE_STATUSES,
    OperatorFeedbackStatus,
)
from production_control_app.domain.ports.operator_feedback_repository import (
    OperatorFeedbackRepositoryPort,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_TABLE = f"{PC_SCHEMA_NAME}.operator_feedbacks"

_ACTIVE = "', '".join(sorted(str(s) for s in ACTIVE_STATUSES))

_COLUMNS = """
    id::text AS id,
    branch,
    production_order,
    operation_code,
    reported_work_center,
    feedback_type,
    reason_code,
    note,
    operator_code,
    operator_name,
    bench_session_id::text AS bench_session_id,
    run_id::text AS run_id,
    status,
    product_code,
    product_description,
    pa_product_code,
    due_date,
    created_at,
    acknowledged_at,
    acknowledged_by,
    resolved_at,
    resolved_by,
    resolution_note
"""


class PostgresOperatorFeedbackRepository(OperatorFeedbackRepositoryPort):
    def create(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
        reported_work_center: str,
        feedback_type: str,
        reason_code: str,
        operator_code: str,
        operator_name: str,
        note: str | None = None,
        bench_session_id: str | None = None,
        run_id: str | None = None,
        product_code: str | None = None,
        product_description: str | None = None,
        pa_product_code: str | None = None,
        due_date: date | str | None = None,
        materials: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        query = f"""
            INSERT INTO {_TABLE} (
                branch, production_order, operation_code, reported_work_center,
                feedback_type, reason_code, note,
                operator_code, operator_name, bench_session_id, run_id,
                status, product_code, product_description, pa_product_code,
                due_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {_COLUMNS}
        """
        params = (
            branch,
            production_order,
            operation_code,
            reported_work_center,
            feedback_type,
            reason_code,
            note,
            operator_code,
            operator_name,
            bench_session_id,
            run_id,
            OperatorFeedbackStatus.OPEN.value,
            product_code,
            product_description,
            pa_product_code,
            due_date,
        )
        try:
            with get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    row = cursor.fetchone()
                    stored_materials = self._insert_materials(
                        cursor, feedback_id=row["id"], materials=materials or []
                    )
                connection.commit()
        except UniqueViolation as exc:
            raise OperatorFeedbackConflict(
                "Já existe impedimento ativo igual para esta operação."
            ) from exc
        return {**dict(row), "materials": stored_materials}

    @staticmethod
    def _insert_materials(
        cursor: Any,
        *,
        feedback_id: str,
        materials: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filhos do feedback na mesma transação (V017) — snapshots SD4 já
        validados; UniqueViolation propaga e derruba o feedback junto."""
        if not materials:
            return []
        table = f"{PC_SCHEMA_NAME}.operator_feedback_materials"
        stored: list[dict[str, Any]] = []
        insert = f"""
            INSERT INTO {table} (
                feedback_id, product_code, description, unit,
                original_qty, open_qty, consumed_qty, commitment_count, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id::text AS id, feedback_id::text AS feedback_id,
                product_code, description, unit, original_qty, open_qty,
                consumed_qty, commitment_count, status, created_at,
                picked_at, picked_by, delivered_at, delivered_by
        """
        for material in materials:
            cursor.execute(
                insert,
                (
                    feedback_id,
                    material.get("product_code"),
                    material.get("description") or "",
                    material.get("unit") or "",
                    material.get("original_qty") or 0,
                    material.get("open_qty") or 0,
                    material.get("consumed_qty") or 0,
                    int(material.get("commitment_count") or 0),
                    "pending",
                ),
            )
            stored.append(dict(cursor.fetchone()))
        return stored

    def get(self, feedback_id: str) -> dict[str, Any] | None:
        query = f"""
            SELECT {_COLUMNS}
            FROM {_TABLE}
            WHERE id = %s
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (feedback_id,))
                row = cursor.fetchone()
        return dict(row) if row else None

    def get_active(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
        feedback_type: str,
        reason_code: str,
    ) -> dict[str, Any] | None:
        query = f"""
            SELECT {_COLUMNS}
            FROM {_TABLE}
            WHERE branch = %s
              AND production_order = %s
              AND operation_code = %s
              AND feedback_type = %s
              AND reason_code = %s
              AND status IN ('{_ACTIVE}')
            ORDER BY created_at DESC
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    query,
                    (branch, production_order, operation_code, feedback_type, reason_code),
                )
                row = cursor.fetchone()
        return dict(row) if row else None

    def list_active(
        self,
        *,
        branch: str,
        reported_work_center: str | None = None,
    ) -> list[dict[str, Any]]:
        scope = "AND reported_work_center = %s" if reported_work_center else ""
        params = (branch, reported_work_center) if reported_work_center else (branch,)
        query = f"""
            SELECT {_COLUMNS}
            FROM {_TABLE}
            WHERE branch = %s
              {scope}
              AND status IN ('{_ACTIVE}')
            ORDER BY CASE status WHEN 'open' THEN 0 ELSE 1 END, created_at
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def list_active_for_operation(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT {_COLUMNS}
            FROM {_TABLE}
            WHERE branch = %s
              AND production_order = %s
              AND operation_code = %s
              AND status IN ('{_ACTIVE}')
            ORDER BY created_at
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (branch, production_order, operation_code))
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def acknowledge(
        self, feedback_id: str, *, acknowledged_by: str
    ) -> dict[str, Any] | None:
        query = f"""
            UPDATE {_TABLE}
            SET status = %s,
                acknowledged_at = NOW(),
                acknowledged_by = %s
            WHERE id = %s
              AND status = %s
            RETURNING {_COLUMNS}
        """
        params = (
            OperatorFeedbackStatus.ACKNOWLEDGED.value,
            acknowledged_by,
            feedback_id,
            OperatorFeedbackStatus.OPEN.value,
        )
        return self._transition(query, params)

    def resolve(
        self,
        feedback_id: str,
        *,
        resolved_by: str,
        resolution_note: str | None = None,
    ) -> dict[str, Any] | None:
        query = f"""
            UPDATE {_TABLE}
            SET status = %s,
                resolved_at = NOW(),
                resolved_by = %s,
                resolution_note = %s
            WHERE id = %s
              AND status IN ('{_ACTIVE}')
            RETURNING {_COLUMNS}
        """
        params = (
            OperatorFeedbackStatus.RESOLVED.value,
            resolved_by,
            resolution_note,
            feedback_id,
        )
        return self._transition(query, params)

    @staticmethod
    def _transition(query: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
        return dict(row) if row else None
