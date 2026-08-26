from __future__ import annotations

from typing import Any

from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

JOB_KEY_PURCHASE_ORDER_LINKED = "purchase_order_linked"


class PurchaseOrderNotificationCursorRepository:
    def get_last_recno(self, job_key: str) -> int | None:
        sql = """
        SELECT last_recno
        FROM purchase_requests.notification_cursors
        WHERE job_key = %s
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (job_key,))
                row = cur.fetchone()
        if not row:
            return None
        return int(row.get("last_recno") or 0)

    def upsert_last_recno(self, job_key: str, last_recno: int) -> dict[str, Any]:
        sql = """
        INSERT INTO purchase_requests.notification_cursors (job_key, last_recno)
        VALUES (%s, %s)
        ON CONFLICT (job_key) DO UPDATE SET
            last_recno = EXCLUDED.last_recno,
            updated_at = NOW()
        RETURNING job_key, last_recno, updated_at
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (job_key, int(last_recno)))
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else {"job_key": job_key, "last_recno": last_recno}
