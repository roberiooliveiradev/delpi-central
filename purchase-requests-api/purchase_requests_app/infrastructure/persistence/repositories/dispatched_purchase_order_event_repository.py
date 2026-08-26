from __future__ import annotations

from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)


class DispatchedPurchaseOrderEventRepository:
    def exists(
        self,
        *,
        branch: str,
        order_number: str,
        order_item: str,
    ) -> bool:
        sql = """
        SELECT 1
        FROM purchase_requests.dispatched_purchase_order_events
        WHERE branch = %s
          AND order_number = %s
          AND order_item = %s
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (branch, order_number, order_item))
                row = cur.fetchone()
        return row is not None

    def mark_dispatched(
        self,
        *,
        branch: str,
        order_number: str,
        order_item: str,
        request_number: str | None = None,
        recno: int | None = None,
    ) -> bool:
        sql = """
        INSERT INTO purchase_requests.dispatched_purchase_order_events
            (branch, order_number, order_item, request_number, recno)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (branch, order_number, order_item) DO NOTHING
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (branch, order_number, order_item, request_number, recno),
                )
                inserted = cur.rowcount == 1
            conn.commit()
        return inserted
