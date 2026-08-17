"""Persistência Postgres — solicitações de emissão de NF."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

SCHEMA = "invoice_issuance"

_REQUEST_COLUMNS = """
    id, branch_code, party_type, party_code, party_store, party_name, tax_id,
    invoice_type, invoice_type_other, freight_mode, carrier_code, carrier_name,
    carrier_legal_name, carrier_tax_id, carrier_address, carrier_phone, weight_kg,
    volume_count, purchase_order_number, observation, status, return_reason,
    checklist, created_by_user_id, created_by_name, assignee_user_id, assignee_name,
    cancelled_at, cancelled_by_user_id, cancelled_by_name, cancel_justification,
    issued_at, created_at, updated_at
"""


def _iso(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return value


def _serialize_request(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key in ("id",):
        if isinstance(out.get(key), UUID):
            out[key] = str(out[key])
    for key in ("cancelled_at", "issued_at", "created_at", "updated_at"):
        out[key] = _iso(out.get(key))
    for key in ("weight_kg",):
        if isinstance(out.get(key), Decimal):
            out[key] = float(out[key])
    checklist = out.get("checklist") or {}
    if not isinstance(checklist, dict):
        checklist = {}
    out["checklist"] = checklist
    return out


def _serialize_item(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key in ("id", "request_id"):
        if isinstance(out.get(key), UUID):
            out[key] = str(out[key])
    for key in ("quantity", "unit_price"):
        if isinstance(out.get(key), Decimal):
            out[key] = float(out[key])
    return out


def _serialize_attachment(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key in ("id", "request_id"):
        if isinstance(out.get(key), UUID):
            out[key] = str(out[key])
    out["created_at"] = _iso(out.get("created_at"))
    out.pop("stored_name", None)
    return out


def _serialize_history(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key in ("id", "request_id"):
        if isinstance(out.get(key), UUID):
            out[key] = str(out[key])
    out["created_at"] = _iso(out.get("created_at"))
    return out


class PostgresInvoiceIssuanceRepository(PluginBaseRepository):
    def _list_items(self, request_id: str) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            f"""
            SELECT id, request_id, line_number, product_code, product_description,
                   quantity, unit_price, stock_write_off, sales_order, sales_order_item,
                   customer_order_number, created_at
              FROM {SCHEMA}.invoice_issuance_request_items
             WHERE request_id = %s::uuid
             ORDER BY line_number ASC
            """,
            (request_id,),
        )
        return [_serialize_item(r) for r in rows]

    def _list_attachments(self, request_id: str) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            f"""
            SELECT id, request_id, stored_name, original_name, mime_type, size_bytes,
                   created_by_user_id, created_at
              FROM {SCHEMA}.invoice_issuance_attachments
             WHERE request_id = %s::uuid
             ORDER BY created_at ASC
            """,
            (request_id,),
        )
        return [_serialize_attachment(r) for r in rows]

    def _hydrate(self, row: dict[str, Any]) -> dict[str, Any]:
        out = _serialize_request(row)
        rid = str(out["id"])
        items = self._list_items(rid)
        out["items"] = items
        out["attachments"] = self._list_attachments(rid)
        out["items_count"] = len(items)
        out["total_amount"] = round(
            sum(float(i["quantity"]) * float(i["unit_price"]) for i in items),
            2,
        )
        return out

    def create_request_with_history(
        self,
        *,
        request_fields: dict[str, Any],
        items: list[dict[str, Any]],
        history_fields: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            row = self.execute_returning_one(
                f"""
                INSERT INTO {SCHEMA}.invoice_issuance_requests (
                    branch_code, party_type, party_code, party_store, party_name, tax_id,
                    invoice_type, invoice_type_other, freight_mode, carrier_code, carrier_name,
                    carrier_legal_name, carrier_tax_id, carrier_address, carrier_phone,
                    weight_kg, volume_count, purchase_order_number, observation,
                    status, checklist, created_by_user_id, created_by_name
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                RETURNING {_REQUEST_COLUMNS}
                """,
                (
                    request_fields["branch_code"],
                    request_fields["party_type"],
                    request_fields["party_code"],
                    request_fields["party_store"],
                    request_fields["party_name"],
                    request_fields.get("tax_id"),
                    request_fields["invoice_type"],
                    request_fields.get("invoice_type_other"),
                    request_fields["freight_mode"],
                    request_fields.get("carrier_code"),
                    request_fields.get("carrier_name"),
                    request_fields.get("carrier_legal_name"),
                    request_fields.get("carrier_tax_id"),
                    request_fields.get("carrier_address"),
                    request_fields.get("carrier_phone"),
                    request_fields["weight_kg"],
                    request_fields["volume_count"],
                    request_fields.get("purchase_order_number"),
                    request_fields.get("observation"),
                    request_fields["status"],
                    Jsonb(request_fields["checklist"]),
                    request_fields["created_by_user_id"],
                    request_fields["created_by_name"],
                ),
                auto_commit=False,
            )
            assert row is not None
            request_id = str(row["id"])
            self._replace_items(request_id, items, auto_commit=False)
            self._insert_history({**history_fields, "request_id": request_id}, auto_commit=False)
            self.commit()
            return self.get_request(request_id) or _serialize_request(row)
        except Exception:
            self.rollback()
            raise

    def _replace_items(
        self,
        request_id: str,
        items: list[dict[str, Any]],
        *,
        auto_commit: bool,
    ) -> None:
        self.execute(
            f"DELETE FROM {SCHEMA}.invoice_issuance_request_items WHERE request_id = %s::uuid",
            (request_id,),
            auto_commit=False,
        )
        for index, item in enumerate(items, start=1):
            self.execute(
                f"""
                INSERT INTO {SCHEMA}.invoice_issuance_request_items (
                    request_id, line_number, product_code, product_description,
                    quantity, unit_price, stock_write_off,
                    sales_order, sales_order_item, customer_order_number
                ) VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    request_id,
                    index,
                    item["product_code"],
                    item["product_description"],
                    item["quantity"],
                    item["unit_price"],
                    item["stock_write_off"],
                    item.get("sales_order"),
                    item.get("sales_order_item"),
                    item.get("customer_order_number"),
                ),
                auto_commit=False,
            )
        if auto_commit:
            self.commit()

    def _insert_history(self, fields: dict[str, Any], *, auto_commit: bool) -> None:
        self.execute(
            f"""
            INSERT INTO {SCHEMA}.invoice_issuance_history (
                request_id, event_type, actor_origin, actor_user_id, actor_name,
                from_status, to_status, changes, justification
            ) VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                fields["request_id"],
                fields["event_type"],
                fields.get("actor_origin") or "user",
                fields.get("actor_user_id"),
                fields.get("actor_name"),
                fields.get("from_status"),
                fields.get("to_status"),
                Jsonb(fields.get("changes") or {}),
                fields.get("justification"),
            ),
            auto_commit=auto_commit,
        )

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            f"SELECT {_REQUEST_COLUMNS} FROM {SCHEMA}.invoice_issuance_requests WHERE id = %s::uuid",
            (request_id,),
        )
        return self._hydrate(row) if row else None

    def list_history(self, request_id: str) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            f"""
            SELECT id, request_id, event_type, actor_origin, actor_user_id, actor_name,
                   from_status, to_status, changes, justification, created_at
              FROM {SCHEMA}.invoice_issuance_history
             WHERE request_id = %s::uuid
             ORDER BY created_at ASC, id ASC
            """,
            (request_id,),
        )
        return [_serialize_history(r) for r in rows]

    def list_requests(
        self,
        *,
        filters: dict[str, Any],
        created_by_user_id: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        where = ["TRUE"]
        params: list[Any] = []
        if created_by_user_id:
            where.append("created_by_user_id = %s")
            params.append(created_by_user_id)
        if filters.get("branch"):
            where.append("branch_code = %s")
            params.append(filters["branch"])
        status = str(filters.get("status") or "").strip()
        if status == "open":
            where.append("status IN ('pending', 'in_progress', 'returned')")
        elif status:
            where.append("status = %s")
            params.append(status)
        if filters.get("invoice_type"):
            where.append("invoice_type = %s")
            params.append(filters["invoice_type"])
        q = str(filters.get("q") or "").strip()
        if q:
            where.append("(party_name ILIKE %s OR party_code ILIKE %s)")
            params.extend([f"%{q}%", f"{q}%"])
        where_sql = " AND ".join(where)
        count_row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM {SCHEMA}.invoice_issuance_requests WHERE {where_sql}",
            tuple(params),
        )
        total = int(count_row["total"]) if count_row else 0
        page = max(1, int(page))
        page_size = max(1, min(int(page_size), 100))
        offset = (page - 1) * page_size
        rows = self.fetch_all(
            f"""
            SELECT {_REQUEST_COLUMNS}
              FROM {SCHEMA}.invoice_issuance_requests
             WHERE {where_sql}
             ORDER BY created_at ASC
             OFFSET %s LIMIT %s
            """,
            tuple(params + [offset, page_size]),
        )
        items = [self._hydrate(r) for r in rows]
        total_pages = (total + page_size - 1) // page_size if page_size else 0
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def update_returned_request(
        self,
        *,
        request_id: str,
        request_fields: dict[str, Any],
        items: list[dict[str, Any]],
        history_fields: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            self.execute(
                f"""
                UPDATE {SCHEMA}.invoice_issuance_requests
                   SET party_type = %s,
                       party_code = %s,
                       party_store = %s,
                       party_name = %s,
                       tax_id = %s,
                       invoice_type = %s,
                       invoice_type_other = %s,
                       freight_mode = %s,
                       carrier_code = %s,
                       carrier_name = %s,
                       carrier_legal_name = %s,
                       carrier_tax_id = %s,
                       carrier_address = %s,
                       carrier_phone = %s,
                       weight_kg = %s,
                       volume_count = %s,
                       purchase_order_number = %s,
                       observation = %s,
                       checklist = %s,
                       return_reason = NULL,
                       updated_at = NOW()
                 WHERE id = %s::uuid
                """,
                (
                    request_fields["party_type"],
                    request_fields["party_code"],
                    request_fields["party_store"],
                    request_fields["party_name"],
                    request_fields.get("tax_id"),
                    request_fields["invoice_type"],
                    request_fields.get("invoice_type_other"),
                    request_fields["freight_mode"],
                    request_fields.get("carrier_code"),
                    request_fields.get("carrier_name"),
                    request_fields.get("carrier_legal_name"),
                    request_fields.get("carrier_tax_id"),
                    request_fields.get("carrier_address"),
                    request_fields.get("carrier_phone"),
                    request_fields["weight_kg"],
                    request_fields["volume_count"],
                    request_fields.get("purchase_order_number"),
                    request_fields.get("observation"),
                    Jsonb(request_fields["checklist"]),
                    request_id,
                ),
                auto_commit=False,
            )
            self._replace_items(request_id, items, auto_commit=False)
            self._insert_history({**history_fields, "request_id": request_id}, auto_commit=False)
            self.commit()
            return self.get_request(request_id) or {}
        except Exception:
            self.rollback()
            raise

    def update_status(
        self,
        *,
        request_id: str,
        status: str,
        extra: dict[str, Any] | None = None,
        history_fields: dict[str, Any],
    ) -> dict[str, Any]:
        extra = extra or {}
        return_reason = extra.get("return_reason")
        if extra.get("clear_return_reason"):
            return_reason = None
            return_reason_sql = "%s"
        elif "return_reason" in extra:
            return_reason_sql = "%s"
        else:
            return_reason_sql = "return_reason"
        try:
            params: list[Any] = [status]
            if return_reason_sql == "%s":
                params.append(return_reason)
            params.extend(
                [
                    extra.get("assignee_user_id"),
                    extra.get("assignee_name"),
                    extra.get("cancelled_at"),
                    extra.get("cancelled_by_user_id"),
                    extra.get("cancelled_by_name"),
                    extra.get("cancel_justification"),
                    extra.get("issued_at"),
                    request_id,
                ]
            )
            self.execute(
                f"""
                UPDATE {SCHEMA}.invoice_issuance_requests
                   SET status = %s,
                       return_reason = {return_reason_sql},
                       assignee_user_id = COALESCE(%s, assignee_user_id),
                       assignee_name = COALESCE(%s, assignee_name),
                       cancelled_at = COALESCE(%s, cancelled_at),
                       cancelled_by_user_id = COALESCE(%s, cancelled_by_user_id),
                       cancelled_by_name = COALESCE(%s, cancelled_by_name),
                       cancel_justification = COALESCE(%s, cancel_justification),
                       issued_at = COALESCE(%s, issued_at),
                       updated_at = NOW()
                 WHERE id = %s::uuid
                """,
                tuple(params),
                auto_commit=False,
            )
            self._insert_history({**history_fields, "request_id": request_id}, auto_commit=False)
            self.commit()
            return self.get_request(request_id) or {}
        except Exception:
            self.rollback()
            raise

    def add_attachment(
        self,
        *,
        request_id: str,
        stored_name: str,
        original_name: str,
        mime_type: str,
        size_bytes: int,
        created_by_user_id: str,
    ) -> dict[str, Any]:
        self.execute(
            f"""
            INSERT INTO {SCHEMA}.invoice_issuance_attachments (
                request_id, stored_name, original_name, mime_type, size_bytes, created_by_user_id
            ) VALUES (%s::uuid, %s, %s, %s, %s, %s)
            """,
            (request_id, stored_name, original_name, mime_type, size_bytes, created_by_user_id),
        )
        return self.get_request(request_id) or {}
