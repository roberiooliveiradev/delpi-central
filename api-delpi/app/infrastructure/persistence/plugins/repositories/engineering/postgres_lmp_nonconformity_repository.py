from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

_STATUS_VALUES = frozenset({"open", "in_progress", "done"})

_NC_SELECT = """
    SELECT n.id,
           n.registered_at,
           n.sale_number,
           n.branch_code,
           n.material_code,
           n.supplier_name,
           n.purchase_order,
           n.invoice_number,
           n.qty_received,
           n.qty_accepted,
           n.qty_rejected,
           n.status,
           n.defect_description,
           n.corrective_actions,
           n.technical_opinion,
           n.created_by,
           n.updated_by,
           n.created_at,
           n.updated_at
      FROM engineering.lmp_nonconformities n
"""


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return None
    return str(value)


def _num(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _normalize_product_codes(codes: list[str] | None) -> list[str]:
    if not codes:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for raw in codes:
        code = str(raw or "").strip().upper()
        if not code or code in seen:
            continue
        seen.add(code)
        out.append(code)
    return out


class PostgresLmpNonconformityRepository(PluginBaseRepository):
    """Persistência de NCs LMP (schema ``engineering``)."""

    def list_records(
        self,
        *,
        status: str | None = None,
        branch_code: str | None = None,
        sale_number: str | None = None,
        material_code: str | None = None,
        product_code: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        filters = ["TRUE"]
        params: list[Any] = []

        if status:
            filters.append("n.status = %s")
            params.append(status)
        if branch_code:
            filters.append("n.branch_code = %s")
            params.append(branch_code)
        if sale_number:
            filters.append("n.sale_number ILIKE %s")
            params.append(f"%{sale_number.strip()}%")
        if material_code:
            filters.append("n.material_code ILIKE %s")
            params.append(f"%{material_code.strip()}%")
        if product_code:
            filters.append(
                """
                EXISTS (
                    SELECT 1
                      FROM engineering.lmp_nonconformity_products p
                     WHERE p.nonconformity_id = n.id
                       AND p.product_code ILIKE %s
                )
                """
            )
            params.append(f"%{product_code.strip()}%")
        if date_start:
            filters.append("n.registered_at::date >= %s::date")
            params.append(date_start)
        if date_end:
            filters.append("n.registered_at::date <= %s::date")
            params.append(date_end)

        where_sql = " AND ".join(filters)
        page = max(1, int(page))
        page_size = max(1, min(int(page_size), 200))
        offset = (page - 1) * page_size

        count_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS total
              FROM engineering.lmp_nonconformities n
             WHERE {where_sql}
            """,
            tuple(params),
        )
        total = int(count_row["total"]) if count_row else 0

        rows = self.fetch_all(
            f"""
            {_NC_SELECT}
             WHERE {where_sql}
             ORDER BY n.registered_at DESC, n.created_at DESC
             LIMIT %s OFFSET %s
            """,
            tuple([*params, page_size, offset]),
        )

        items = [self._to_payload(row, include_products=True) for row in rows]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            f"""
            {_NC_SELECT}
             WHERE n.id = %s
            """,
            (record_id,),
        )
        if row is None:
            return None
        return self._to_payload(row, include_products=True)

    def create_record(
        self,
        *,
        registered_at: str,
        status: str = "open",
        sale_number: str | None = None,
        branch_code: str | None = None,
        material_code: str | None = None,
        supplier_name: str | None = None,
        purchase_order: str | None = None,
        invoice_number: str | None = None,
        qty_received: float | None = None,
        qty_accepted: float | None = None,
        qty_rejected: float | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        product_codes: list[str] | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        status_norm = (status or "open").strip().lower()
        if status_norm not in _STATUS_VALUES:
            raise PluginsRepositoryError(f"Status inválido: {status}")

        codes = _normalize_product_codes(product_codes)
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO engineering.lmp_nonconformities (
                        registered_at, sale_number, branch_code, material_code,
                        supplier_name, purchase_order, invoice_number,
                        qty_received, qty_accepted, qty_rejected, status,
                        defect_description, corrective_actions, technical_opinion,
                        created_by, updated_by
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s
                    )
                    RETURNING id, registered_at, sale_number, branch_code, material_code,
                              supplier_name, purchase_order, invoice_number,
                              qty_received, qty_accepted, qty_rejected, status,
                              defect_description, corrective_actions, technical_opinion,
                              created_by, updated_by, created_at, updated_at
                    """,
                    (
                        registered_at,
                        _blank_to_none(sale_number),
                        _blank_to_none(branch_code),
                        _blank_to_none(material_code),
                        _blank_to_none(supplier_name),
                        _blank_to_none(purchase_order),
                        _blank_to_none(invoice_number),
                        qty_received,
                        qty_accepted,
                        qty_rejected,
                        status_norm,
                        _blank_to_none(defect_description),
                        _blank_to_none(corrective_actions),
                        _blank_to_none(technical_opinion),
                        created_by,
                        created_by,
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    raise PluginsRepositoryError("Falha ao criar não conformidade LMP.")
                record_id = str(dict(row)["id"])
                if codes:
                    cursor.executemany(
                        """
                        INSERT INTO engineering.lmp_nonconformity_products (
                            nonconformity_id, product_code
                        ) VALUES (%s, %s)
                        """,
                        [(record_id, code) for code in codes],
                    )
            self.commit()
        except PluginsRepositoryError:
            self.rollback()
            raise
        except Exception as exc:
            self.rollback()
            raise PluginsRepositoryError(
                "Falha ao criar não conformidade LMP."
            ) from exc

        created = self.get_record(record_id)
        if created is None:
            raise PluginsRepositoryError("NC criada mas não encontrada após insert.")
        return created

    def update_record(
        self,
        *,
        record_id: str,
        registered_at: str,
        status: str,
        sale_number: str | None = None,
        branch_code: str | None = None,
        material_code: str | None = None,
        supplier_name: str | None = None,
        purchase_order: str | None = None,
        invoice_number: str | None = None,
        qty_received: float | None = None,
        qty_accepted: float | None = None,
        qty_rejected: float | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        product_codes: list[str] | None = None,
        updated_by: str | None = None,
    ) -> dict[str, Any] | None:
        current = self.fetch_one(
            f"""
            {_NC_SELECT}
             WHERE n.id = %s
            """,
            (record_id,),
        )
        if current is None:
            return None

        status_norm = (status or "").strip().lower()
        if status_norm not in _STATUS_VALUES:
            raise PluginsRepositoryError(f"Status inválido: {status}")

        codes = _normalize_product_codes(product_codes)

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE engineering.lmp_nonconformities
                       SET registered_at = %s,
                           sale_number = %s,
                           branch_code = %s,
                           material_code = %s,
                           supplier_name = %s,
                           purchase_order = %s,
                           invoice_number = %s,
                           qty_received = %s,
                           qty_accepted = %s,
                           qty_rejected = %s,
                           status = %s,
                           defect_description = %s,
                           corrective_actions = %s,
                           technical_opinion = %s,
                           updated_by = %s,
                           updated_at = NOW()
                     WHERE id = %s
                    """,
                    (
                        registered_at,
                        _blank_to_none(sale_number),
                        _blank_to_none(branch_code),
                        _blank_to_none(material_code),
                        _blank_to_none(supplier_name),
                        _blank_to_none(purchase_order),
                        _blank_to_none(invoice_number),
                        qty_received,
                        qty_accepted,
                        qty_rejected,
                        status_norm,
                        _blank_to_none(defect_description),
                        _blank_to_none(corrective_actions),
                        _blank_to_none(technical_opinion),
                        updated_by,
                        record_id,
                    ),
                )
                cursor.execute(
                    """
                    DELETE FROM engineering.lmp_nonconformity_products
                     WHERE nonconformity_id = %s
                    """,
                    (record_id,),
                )
                if codes:
                    cursor.executemany(
                        """
                        INSERT INTO engineering.lmp_nonconformity_products (
                            nonconformity_id, product_code
                        ) VALUES (%s, %s)
                        """,
                        [(record_id, code) for code in codes],
                    )
            self.commit()
        except PluginsRepositoryError:
            self.rollback()
            raise
        except Exception as exc:
            self.rollback()
            raise PluginsRepositoryError(
                "Falha ao atualizar não conformidade LMP."
            ) from exc

        return self.get_record(record_id)

    def delete_record(self, record_id: str) -> bool:
        row = self.execute_returning_one(
            """
            DELETE FROM engineering.lmp_nonconformities
             WHERE id = %s
         RETURNING id
            """,
            (record_id,),
        )
        return row is not None

    def _list_product_codes(self, record_id: str) -> list[str]:
        rows = self.fetch_all(
            """
            SELECT product_code
              FROM engineering.lmp_nonconformity_products
             WHERE nonconformity_id = %s
             ORDER BY product_code ASC
            """,
            (record_id,),
        )
        return [str(r["product_code"]) for r in rows]

    def _to_payload(
        self,
        row: dict[str, Any],
        *,
        include_products: bool = False,
    ) -> dict[str, Any]:
        record_id = str(row["id"])
        payload: dict[str, Any] = {
            "id": record_id,
            "registered_at": _iso(row.get("registered_at")),
            "sale_number": row.get("sale_number"),
            "branch_code": row.get("branch_code"),
            "material_code": row.get("material_code"),
            "supplier_name": row.get("supplier_name"),
            "purchase_order": row.get("purchase_order"),
            "invoice_number": row.get("invoice_number"),
            "qty_received": _num(row.get("qty_received")),
            "qty_accepted": _num(row.get("qty_accepted")),
            "qty_rejected": _num(row.get("qty_rejected")),
            "status": row.get("status"),
            "defect_description": row.get("defect_description"),
            "corrective_actions": row.get("corrective_actions"),
            "technical_opinion": row.get("technical_opinion"),
            "created_by": row.get("created_by"),
            "updated_by": row.get("updated_by"),
            "created_at": _iso(row.get("created_at")),
            "updated_at": _iso(row.get("updated_at")),
        }
        if include_products:
            payload["product_codes"] = self._list_product_codes(record_id)
        return payload
