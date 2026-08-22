from __future__ import annotations

from datetime import date
from typing import Any

import json

from travel_expenses_app.core.serialize import json_safe
from travel_expenses_app.infrastructure.persistence.migrations_runner import get_connection

SCHEMA = "travel_expenses"


def _map_report(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "number": row["number"],
        "unitCode": row["unit_code"],
        "ownerUserId": row["owner_user_id"],
        "createdByName": row.get("created_by_name"),
        "createdByEmail": row.get("created_by_email"),
        "destination": row.get("destination") or "",
        "purpose": row.get("purpose") or "",
        "periodStart": row.get("period_start"),
        "periodEnd": row.get("period_end"),
        "costCenterCode": row.get("cost_center_code"),
        "costCenterLabel": row.get("cost_center_label"),
        "status": row["status"],
        "totalAmountBrl": float(row.get("total_amount_brl") or 0),
        "pixKeyType": row.get("pix_key_type"),
        "pixKeyValue": row.get("pix_key_value"),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
        "expenseCount": int(row.get("expense_count") or 0),
        "missingReceiptCount": int(row.get("missing_receipt_count") or 0),
    }


def _map_receipt(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "expenseId": str(row["expense_id"]),
        "storedName": row["stored_name"],
        "originalName": row["original_name"],
        "mimeType": row["mime_type"],
        "sizeBytes": int(row["size_bytes"]),
        "createdAt": row.get("created_at"),
    }


def _map_expense(row: dict[str, Any], receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "reportId": str(row["report_id"]),
        "expenseDate": row["expense_date"],
        "categoryId": row["category_id"],
        "merchant": row.get("merchant") or "",
        "amountBrl": float(row.get("amount_brl") or 0),
        "notes": row.get("notes") or "",
        "sortOrder": int(row.get("sort_order") or 0),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
        "receipts": receipts or [],
    }


class PostgresTravelReportRepository:
    def list_categories(self) -> list[dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, label, sort_order, active
                FROM {SCHEMA}.categories
                WHERE active = TRUE
                ORDER BY sort_order, label
                """
            )
            return [
                {
                    "id": row["id"],
                    "label": row["label"],
                    "sortOrder": row["sort_order"],
                    "active": row["active"],
                }
                for row in cur.fetchall()
            ]

    def next_report_number(self, *, unit_code: str, year: int) -> str:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {SCHEMA}.report_sequences (unit_code, year, last_n)
                VALUES (%s, %s, 1)
                ON CONFLICT (unit_code, year)
                DO UPDATE SET last_n = {SCHEMA}.report_sequences.last_n + 1
                RETURNING last_n
                """,
                (unit_code, year),
            )
            last_n = int(cur.fetchone()["last_n"])
            conn.commit()
        return f"TE-{year}-{last_n:04d}"

    def create_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {SCHEMA}.reports (
                    number, unit_code, owner_user_id, created_by_name, created_by_email,
                    destination, purpose, period_start, period_end,
                    cost_center_code, cost_center_label, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    payload["number"],
                    payload["unit_code"],
                    payload["owner_user_id"],
                    payload.get("created_by_name"),
                    payload.get("created_by_email"),
                    payload.get("destination") or "",
                    payload.get("purpose") or "",
                    payload.get("period_start"),
                    payload.get("period_end"),
                    payload.get("cost_center_code"),
                    payload.get("cost_center_label"),
                    payload.get("status") or "draft",
                ),
            )
            row = cur.fetchone()
            conn.commit()
        return _map_report(row)

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {SCHEMA}.reports WHERE id = %s", (report_id,))
            row = cur.fetchone()
        return _map_report(row) if row else None

    def list_reports(
        self,
        *,
        unit_codes: list[str],
        owner_user_id: str | None,
        query: str | None = None,
        period_from: date | None = None,
        period_to: date | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["r.unit_code = ANY(%s)"]
        params: list[Any] = [unit_codes]
        if owner_user_id:
            clauses.append("r.owner_user_id = %s")
            params.append(owner_user_id)
        if query:
            clauses.append(
                "(r.number ILIKE %s OR r.destination ILIKE %s OR COALESCE(r.created_by_name, '') ILIKE %s)"
            )
            like = f"%{query}%"
            params.extend([like, like, like])
        if period_from:
            clauses.append("(r.period_start IS NULL OR r.period_start >= %s)")
            params.append(period_from)
        if period_to:
            clauses.append("(r.period_end IS NULL OR r.period_end <= %s)")
            params.append(period_to)
        where = " AND ".join(clauses)
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT r.*,
                       COALESCE(stats.expense_count, 0) AS expense_count,
                       COALESCE(stats.missing_receipt_count, 0) AS missing_receipt_count
                FROM {SCHEMA}.reports r
                LEFT JOIN LATERAL (
                    SELECT
                        COUNT(*) AS expense_count,
                        COUNT(*) FILTER (
                            WHERE NOT EXISTS (
                                SELECT 1 FROM {SCHEMA}.receipts rec
                                WHERE rec.expense_id = e.id
                            )
                        ) AS missing_receipt_count
                    FROM {SCHEMA}.expenses e
                    WHERE e.report_id = r.id
                ) stats ON TRUE
                WHERE {where}
                ORDER BY r.updated_at DESC
                """,
                params,
            )
            return [_map_report(row) for row in cur.fetchall()]

    def update_report(self, report_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        allowed = {
            "destination": "destination",
            "purpose": "purpose",
            "period_start": "period_start",
            "period_end": "period_end",
            "cost_center_code": "cost_center_code",
            "cost_center_label": "cost_center_label",
            "status": "status",
            "total_amount_brl": "total_amount_brl",
            "pix_key_type": "pix_key_type",
            "pix_key_value": "pix_key_value",
        }
        sets = []
        params: list[Any] = []
        for key, column in allowed.items():
            if key in changes:
                sets.append(f"{column} = %s")
                params.append(changes[key])
        if not sets:
            return self.get_report(report_id)
        sets.append("updated_at = NOW()")
        params.append(report_id)
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"UPDATE {SCHEMA}.reports SET {', '.join(sets)} WHERE id = %s RETURNING *",
                params,
            )
            row = cur.fetchone()
            conn.commit()
        return _map_report(row) if row else None

    def delete_report(self, report_id: str) -> bool:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"DELETE FROM {SCHEMA}.reports WHERE id = %s", (report_id,))
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    def refresh_total(self, report_id: str) -> float:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {SCHEMA}.reports
                SET total_amount_brl = COALESCE((
                    SELECT SUM(amount_brl) FROM {SCHEMA}.expenses WHERE report_id = %s
                ), 0),
                    updated_at = NOW()
                WHERE id = %s
                RETURNING total_amount_brl
                """,
                (report_id, report_id),
            )
            row = cur.fetchone()
            conn.commit()
        return float(row["total_amount_brl"] if row else 0)

    def create_expense(self, payload: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {SCHEMA}.expenses (
                    report_id, expense_date, category_id, merchant, amount_brl, notes, sort_order
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    payload["report_id"],
                    payload["expense_date"],
                    payload["category_id"],
                    payload.get("merchant") or "",
                    payload["amount_brl"],
                    payload.get("notes") or "",
                    payload.get("sort_order") or 0,
                ),
            )
            row = cur.fetchone()
            conn.commit()
        self.refresh_total(payload["report_id"])
        return _map_expense(row, [])

    def get_expense(self, expense_id: str) -> dict[str, Any] | None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {SCHEMA}.expenses WHERE id = %s", (expense_id,))
            row = cur.fetchone()
            if not row:
                return None
            cur.execute(
                f"SELECT * FROM {SCHEMA}.receipts WHERE expense_id = %s ORDER BY created_at",
                (expense_id,),
            )
            receipts = [_map_receipt(item) for item in cur.fetchall()]
        return _map_expense(row, receipts)

    def list_expenses(self, report_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT * FROM {SCHEMA}.expenses
                WHERE report_id = %s
                ORDER BY expense_date, sort_order, created_at
                """,
                (report_id,),
            )
            expenses = cur.fetchall()
            cur.execute(
                f"""
                SELECT rec.*
                FROM {SCHEMA}.receipts rec
                JOIN {SCHEMA}.expenses e ON e.id = rec.expense_id
                WHERE e.report_id = %s
                ORDER BY rec.created_at
                """,
                (report_id,),
            )
            receipts_by_expense: dict[str, list[dict[str, Any]]] = {}
            for rec in cur.fetchall():
                receipts_by_expense.setdefault(str(rec["expense_id"]), []).append(_map_receipt(rec))
        return [_map_expense(row, receipts_by_expense.get(str(row["id"]), [])) for row in expenses]

    def update_expense(self, expense_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        allowed = {
            "expense_date": "expense_date",
            "category_id": "category_id",
            "merchant": "merchant",
            "amount_brl": "amount_brl",
            "notes": "notes",
        }
        sets = []
        params: list[Any] = []
        for key, column in allowed.items():
            if key in changes:
                sets.append(f"{column} = %s")
                params.append(changes[key])
        current = self.get_expense(expense_id)
        if not current:
            return None
        if sets:
            sets.append("updated_at = NOW()")
            params.append(expense_id)
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    f"UPDATE {SCHEMA}.expenses SET {', '.join(sets)} WHERE id = %s",
                    params,
                )
                conn.commit()
        self.refresh_total(current["reportId"])
        return self.get_expense(expense_id)

    def delete_expense(self, expense_id: str) -> bool:
        current = self.get_expense(expense_id)
        if not current:
            return False
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"DELETE FROM {SCHEMA}.expenses WHERE id = %s", (expense_id,))
            conn.commit()
        self.refresh_total(current["reportId"])
        return True

    def create_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {SCHEMA}.receipts (
                    expense_id, stored_name, original_name, mime_type, size_bytes
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    payload["expense_id"],
                    payload["stored_name"],
                    payload["original_name"],
                    payload["mime_type"],
                    payload["size_bytes"],
                ),
            )
            row = cur.fetchone()
            conn.commit()
        return _map_receipt(row)

    def get_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {SCHEMA}.receipts WHERE id = %s", (receipt_id,))
            row = cur.fetchone()
        return _map_receipt(row) if row else None

    def delete_receipt(self, receipt_id: str) -> bool:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"DELETE FROM {SCHEMA}.receipts WHERE id = %s", (receipt_id,))
            deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    def add_audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {SCHEMA}.audit_events (
                    report_id, event_type, from_status, to_status,
                    actor_user_id, actor_name, actor_email, payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING *
                """,
                (
                    payload["report_id"],
                    payload["event_type"],
                    payload.get("from_status"),
                    payload.get("to_status"),
                    payload.get("actor_user_id"),
                    payload.get("actor_name"),
                    payload.get("actor_email"),
                    json.dumps(json_safe(payload.get("payload") or {})),
                ),
            )
            row = cur.fetchone()
            conn.commit()
        return {
            "id": str(row["id"]),
            "reportId": str(row["report_id"]),
            "eventType": row["event_type"],
            "fromStatus": row.get("from_status"),
            "toStatus": row.get("to_status"),
            "actorUserId": row.get("actor_user_id"),
            "actorName": row.get("actor_name"),
            "actorEmail": row.get("actor_email"),
            "payload": row.get("payload") or {},
            "createdAt": row.get("created_at"),
        }

    def list_audit(self, report_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT * FROM {SCHEMA}.audit_events
                WHERE report_id = %s
                ORDER BY created_at DESC
                """,
                (report_id,),
            )
            return [
                {
                    "id": str(row["id"]),
                    "reportId": str(row["report_id"]),
                    "eventType": row["event_type"],
                    "fromStatus": row.get("from_status"),
                    "toStatus": row.get("to_status"),
                    "actorUserId": row.get("actor_user_id"),
                    "actorName": row.get("actor_name"),
                    "actorEmail": row.get("actor_email"),
                    "payload": row.get("payload") or {},
                    "createdAt": row.get("created_at"),
                }
                for row in cur.fetchall()
            ]
