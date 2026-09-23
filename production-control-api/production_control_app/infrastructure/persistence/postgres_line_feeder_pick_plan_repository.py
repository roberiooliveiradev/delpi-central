"""Repositório Postgres — listas de coleta do alimentador de linha.

Toda leitura e escrita é filtrada por `branch`, inclusive quando o `plan_id` já
identifica a linha: id de outra filial não deve ser legível nem editável, mesmo
que alguém o descubra.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from production_control_app.domain.ports.line_feeder_pick_plan_repository import (
    LineFeederPickPlanRepositoryPort,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_PLANS = f"{PC_SCHEMA_NAME}.line_feeder_pick_plans"
_ITEMS = f"{PC_SCHEMA_NAME}.line_feeder_pick_items"

_PLAN_COLUMNS = """
    id::text AS id,
    branch,
    cutoff_at,
    work_center,
    status,
    created_at,
    created_by,
    updated_at,
    updated_by
"""

_ITEM_COLUMNS = """
    id::text AS id,
    plan_id::text AS plan_id,
    work_center,
    production_order,
    operation_code,
    product_code,
    description,
    unit,
    pickup_location,
    required_qty,
    point_of_use_qty,
    to_deliver_qty,
    status,
    updated_at,
    updated_by
"""

_ITEM_FIELDS = (
    "product_code",
    "description",
    "unit",
    "pickup_location",
    "required_qty",
    "point_of_use_qty",
    "to_deliver_qty",
)


class PostgresLineFeederPickPlanRepository(LineFeederPickPlanRepositoryPort):
    def create_plan(
        self,
        *,
        branch: str,
        cutoff_at: datetime,
        work_center: str | None,
        created_by: str | None,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Grava plano e itens na mesma transação: plano sem item não serve de nada."""
        insert_plan = f"""
            INSERT INTO {_PLANS} (branch, cutoff_at, work_center, created_by, updated_by)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING {_PLAN_COLUMNS}
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    insert_plan,
                    (branch, cutoff_at, work_center or None, created_by, created_by),
                )
                plan = cursor.fetchone()
                if plan is None:
                    raise RuntimeError("Falha ao criar a lista de coleta.")
                stored_items = self._insert_items(
                    cursor,
                    plan_id=plan["id"],
                    items=items,
                    updated_by=created_by,
                )
            connection.commit()
        return {**dict(plan), "items": stored_items}

    @staticmethod
    def _insert_items(
        cursor: Any,
        *,
        plan_id: str,
        items: list[dict[str, Any]],
        updated_by: str | None,
    ) -> list[dict[str, Any]]:
        if not items:
            return []

        columns = ", ".join(("plan_id", *_ITEM_FIELDS, "updated_by"))
        placeholders = ", ".join(["%s"] * (len(_ITEM_FIELDS) + 2))
        values_clause = ", ".join([f"({placeholders})"] * len(items))
        params: list[Any] = []
        for item in items:
            params.append(plan_id)
            params.extend(item.get(field) for field in _ITEM_FIELDS)
            params.append(updated_by)

        query = f"""
            INSERT INTO {_ITEMS} ({columns})
            VALUES {values_clause}
            ON CONFLICT (plan_id, product_code)
            DO NOTHING
            RETURNING {_ITEM_COLUMNS}
        """
        cursor.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def get_plan(self, *, plan_id: str, branch: str) -> dict[str, Any] | None:
        plan_query = f"""
            SELECT {_PLAN_COLUMNS}
            FROM {_PLANS}
            WHERE id = %s AND branch = %s
            LIMIT 1
        """
        items_query = f"""
            SELECT {_ITEM_COLUMNS}
            FROM {_ITEMS}
            WHERE plan_id = %s
            ORDER BY product_code ASC
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(plan_query, (plan_id, branch))
                plan = cursor.fetchone()
                if plan is None:
                    return None
                cursor.execute(items_query, (plan_id,))
                items = [dict(row) for row in cursor.fetchall()]
        return {**dict(plan), "items": items}

    def list_plans(
        self,
        *,
        branch: str,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Planos da filial com o contador de itens por status, sem carregar os itens."""
        filters = ["p.branch = %s"]
        params: list[Any] = [branch]
        if status:
            filters.append("p.status = %s")
            params.append(status)
        params.append(max(1, min(int(limit or 50), 200)))

        query = f"""
            SELECT
                p.id::text AS id,
                p.branch,
                p.cutoff_at,
                p.work_center,
                p.status,
                p.created_at,
                p.created_by,
                p.updated_at,
                p.updated_by,
                COUNT(i.id) AS item_count,
                COALESCE(SUM(i.to_deliver_qty), 0) AS to_deliver_qty,
                COUNT(i.id) FILTER (WHERE i.status = 'pending') AS pending_count,
                COUNT(i.id) FILTER (WHERE i.status = 'picked') AS picked_count,
                COUNT(i.id) FILTER (WHERE i.status = 'delivered') AS delivered_count
            FROM {_PLANS} p
            LEFT JOIN {_ITEMS} i ON i.plan_id = p.id
            WHERE {" AND ".join(filters)}
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT %s
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, tuple(params))
                return [dict(row) for row in cursor.fetchall()]

    def update_item_status(
        self,
        *,
        plan_id: str,
        item_id: str,
        branch: str,
        status: str,
        updated_by: str | None,
    ) -> dict[str, Any] | None:
        """O `EXISTS` na filial evita que um id vazado mude item de outra filial."""
        query = f"""
            UPDATE {_ITEMS} AS i
            SET status = %s, updated_at = NOW(), updated_by = %s
            WHERE i.id = %s
              AND i.plan_id = %s
              AND EXISTS (
                  SELECT 1 FROM {_PLANS} p
                  WHERE p.id = i.plan_id AND p.branch = %s
              )
            RETURNING {_ITEM_COLUMNS}
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (status, updated_by, item_id, plan_id, branch))
                row = cursor.fetchone()
                if row is None:
                    connection.rollback()
                    return None
                self._touch_plan(cursor, plan_id=plan_id, updated_by=updated_by)
            connection.commit()
        return dict(row)

    @staticmethod
    def _touch_plan(cursor: Any, *, plan_id: str, updated_by: str | None) -> None:
        cursor.execute(
            f"UPDATE {_PLANS} SET updated_at = NOW(), updated_by = %s WHERE id = %s",
            (updated_by, plan_id),
        )

    def close_plan(
        self,
        *,
        plan_id: str,
        branch: str,
        updated_by: str | None,
    ) -> dict[str, Any] | None:
        query = f"""
            UPDATE {_PLANS}
            SET status = 'closed', updated_at = NOW(), updated_by = %s
            WHERE id = %s AND branch = %s
            RETURNING {_PLAN_COLUMNS}
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (updated_by, plan_id, branch))
                row = cursor.fetchone()
                if row is None:
                    connection.rollback()
                    return None
            connection.commit()
        return dict(row)
