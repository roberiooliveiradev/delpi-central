from __future__ import annotations

from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)


class DispatchedPurchaseReceiptEventRepository:
    def exists(
        self,
        *,
        branch: str,
        invoice_number: str,
        invoice_series: str,
        invoice_item: str,
    ) -> bool:
        sql = """
        SELECT 1
        FROM purchase_requests.dispatched_purchase_receipt_events
        WHERE branch = %s
          AND invoice_number = %s
          AND invoice_series = %s
          AND invoice_item = %s
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (branch, invoice_number, invoice_series, invoice_item),
                )
                row = cur.fetchone()
        return row is not None

    def mark_dispatched(
        self,
        *,
        branch: str,
        invoice_number: str,
        invoice_series: str,
        invoice_item: str,
        request_number: str | None = None,
        order_number: str | None = None,
        recno: int | None = None,
    ) -> bool:
        sql = """
        INSERT INTO purchase_requests.dispatched_purchase_receipt_events
            (branch, invoice_number, invoice_series, invoice_item,
             request_number, order_number, recno)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (branch, invoice_number, invoice_series, invoice_item)
        DO NOTHING
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        branch,
                        invoice_number,
                        invoice_series,
                        invoice_item,
                        request_number,
                        order_number,
                        recno,
                    ),
                )
                inserted = cur.rowcount == 1
            conn.commit()
        return inserted
