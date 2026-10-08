"""Repositório Postgres — materiais estruturados do Operator Feedback (C5).

Leitura e transições da fila urgente do Alimentador de Linha. A criação é
atômica junto ao feedback (PostgresOperatorFeedbackRepository.create).

Regras embutidas no SQL:
  * transições são UPDATEs condicionais (WHERE status = esperado) — dois
    alimentadores não se atropelam;
  * a transição exige o feedback pai ainda ativo (open|acknowledged):
    impedimento resolvido não gera separação nova;
  * a fila ativa exclui materiais de feedback resolved sem apagar histórico.
"""

from __future__ import annotations

from typing import Any

from production_control_app.domain.operator_feedback import ACTIVE_STATUSES
from production_control_app.domain.operator_feedback_material import (
    ACTIVE_MATERIAL_STATUSES,
    OperatorFeedbackMaterialStatus,
)
from production_control_app.domain.ports.operator_feedback_material_repository import (  # noqa: E501
    OperatorFeedbackMaterialRepositoryPort,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
    PC_SCHEMA_NAME,
    get_connection,
)

_MATERIALS = f"{PC_SCHEMA_NAME}.operator_feedback_materials"
_FEEDBACKS = f"{PC_SCHEMA_NAME}.operator_feedbacks"

_FEEDBACK_ACTIVE = "', '".join(sorted(str(s) for s in ACTIVE_STATUSES))
_MATERIAL_ACTIVE = "', '".join(sorted(str(s) for s in ACTIVE_MATERIAL_STATUSES))

_COLUMNS = """
    m.id::text AS id,
    m.feedback_id::text AS feedback_id,
    m.product_code,
    m.description,
    m.unit,
    m.original_qty,
    m.open_qty,
    m.consumed_qty,
    m.commitment_count,
    m.status,
    m.created_at,
    m.picked_at,
    m.picked_by,
    m.delivered_at,
    m.delivered_by
"""

#: Contexto do feedback pai — autorização por filial, regra de fila ativa e
#: payload mínimo do realtime. Sem note/operador para não vazar pelo socket.
_FEEDBACK_JOIN = """
    f.branch AS feedback_branch,
    f.production_order AS feedback_production_order,
    f.operation_code AS feedback_operation_code,
    f.reported_work_center AS feedback_reported_work_center,
    f.status AS feedback_status,
    f.operator_code AS feedback_operator_code,
    f.operator_name AS feedback_operator_name,
    f.note AS feedback_note,
    f.created_at AS feedback_created_at
"""


class PostgresOperatorFeedbackMaterialRepository(
    OperatorFeedbackMaterialRepositoryPort
):
    def list_for_feedbacks(
        self, feedback_ids: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        if not feedback_ids:
            return {}
        columns = _COLUMNS.replace("m.", "")
        query = f"""
            SELECT {columns}
            FROM {_MATERIALS}
            WHERE feedback_id = ANY(%s)
            ORDER BY product_code
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (list(feedback_ids),))
                rows = cursor.fetchall()
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(str(row["feedback_id"]), []).append(dict(row))
        return grouped

    def get_material(self, material_id: str) -> dict[str, Any] | None:
        query = f"""
            SELECT {_COLUMNS}, {_FEEDBACK_JOIN}
            FROM {_MATERIALS} m
            JOIN {_FEEDBACKS} f ON f.id = m.feedback_id
            WHERE m.id = %s
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (material_id,))
                row = cursor.fetchone()
        return dict(row) if row else None

    def list_active_requests(self, *, branch: str) -> list[dict[str, Any]]:
        query = f"""
            SELECT {_COLUMNS}, {_FEEDBACK_JOIN}
            FROM {_MATERIALS} m
            JOIN {_FEEDBACKS} f ON f.id = m.feedback_id
            WHERE f.branch = %s
              AND f.status IN ('{_FEEDBACK_ACTIVE}')
              AND m.status IN ('{_MATERIAL_ACTIVE}')
            ORDER BY CASE m.status WHEN 'pending' THEN 0 ELSE 1 END, f.created_at, m.product_code
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (branch,))
                rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def mark_picked(
        self, material_id: str, *, picked_by: str
    ) -> dict[str, Any] | None:
        return self._transition(
            material_id,
            from_status=OperatorFeedbackMaterialStatus.PENDING.value,
            to_status=OperatorFeedbackMaterialStatus.PICKED.value,
            actor=picked_by,
            stamp_columns="picked_at = NOW(), picked_by = %s",
        )

    def mark_delivered(
        self, material_id: str, *, delivered_by: str
    ) -> dict[str, Any] | None:
        return self._transition(
            material_id,
            from_status=OperatorFeedbackMaterialStatus.PICKED.value,
            to_status=OperatorFeedbackMaterialStatus.DELIVERED.value,
            actor=delivered_by,
            stamp_columns="delivered_at = NOW(), delivered_by = %s",
        )

    @staticmethod
    def _transition(
        material_id: str,
        *,
        from_status: str,
        to_status: str,
        actor: str,
        stamp_columns: str,
    ) -> dict[str, Any] | None:
        query = f"""
            UPDATE {_MATERIALS} m
            SET status = %s, {stamp_columns}
            WHERE m.id = %s
              AND m.status = %s
              AND EXISTS (
                  SELECT 1 FROM {_FEEDBACKS} f
                  WHERE f.id = m.feedback_id
                    AND f.status IN ('{_FEEDBACK_ACTIVE}')
              )
            RETURNING {_COLUMNS}
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (to_status, actor, material_id, from_status))
                row = cursor.fetchone()
        return dict(row) if row else None
