from __future__ import annotations

from datetime import date, datetime
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
           n.customer_name,
           n.launch_date,
           n.last_revision_date,
           n.executed_by,
           n.released_by,
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


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _normalize_products(products: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    if not products:
        return []
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for raw in products:
        if not isinstance(raw, dict):
            continue
        code = str(raw.get("product_code") or raw.get("code") or "").strip().upper()
        if not code or code in seen:
            continue
        seen.add(code)
        description = str(
            raw.get("product_description") or raw.get("description") or ""
        ).strip()
        out.append(
            {
                "product_code": code,
                "product_description": description[:255] if description else "",
            }
        )
    return out


class PostgresLmpNonconformityRepository(PluginBaseRepository):
    """Persistência de NCs LMP (schema ``engineering``) — domínio engenharia."""

    def list_records(
        self,
        *,
        status: str | None = None,
        sale_number: str | None = None,
        customer_name: str | None = None,
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
        if sale_number:
            filters.append("n.sale_number ILIKE %s")
            params.append(f"%{sale_number.strip()}%")
        if customer_name:
            filters.append("n.customer_name ILIKE %s")
            params.append(f"%{customer_name.strip()}%")
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
        status: str = "open",
        sale_number: str | None = None,
        customer_name: str | None = None,
        launch_date: str | None = None,
        last_revision_date: str | None = None,
        executed_by: str | None = None,
        released_by: str | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        products: list[dict[str, Any]] | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        status_norm = (status or "open").strip().lower()
        if status_norm not in _STATUS_VALUES:
            raise PluginsRepositoryError(f"Status inválido: {status}")

        lines = _normalize_products(products)
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO engineering.lmp_nonconformities (
                        registered_at, sale_number, customer_name,
                        launch_date, last_revision_date,
                        executed_by, released_by, status,
                        defect_description, corrective_actions, technical_opinion,
                        created_by, updated_by
                    ) VALUES (
                        NOW(), %s, %s,
                        %s::date, %s::date,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s
                    )
                    RETURNING id
                    """,
                    (
                        _blank_to_none(sale_number),
                        _blank_to_none(customer_name),
                        _blank_to_none(launch_date),
                        _blank_to_none(last_revision_date),
                        _blank_to_none(executed_by),
                        _blank_to_none(released_by),
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
                self._replace_products(cursor, record_id, lines)
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
        status: str,
        sale_number: str | None = None,
        customer_name: str | None = None,
        launch_date: str | None = None,
        last_revision_date: str | None = None,
        executed_by: str | None = None,
        released_by: str | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        products: list[dict[str, Any]] | None = None,
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

        lines = _normalize_products(products)

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE engineering.lmp_nonconformities
                       SET sale_number = %s,
                           customer_name = %s,
                           launch_date = %s::date,
                           last_revision_date = %s::date,
                           executed_by = %s,
                           released_by = %s,
                           status = %s,
                           defect_description = %s,
                           corrective_actions = %s,
                           technical_opinion = %s,
                           updated_by = %s,
                           updated_at = NOW()
                     WHERE id = %s
                    """,
                    (
                        _blank_to_none(sale_number),
                        _blank_to_none(customer_name),
                        _blank_to_none(launch_date),
                        _blank_to_none(last_revision_date),
                        _blank_to_none(executed_by),
                        _blank_to_none(released_by),
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
                self._replace_products(cursor, record_id, lines)
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

    def list_occurrence_dates(self) -> list:
        """Datas distintas de registro de NC (para streak sem NC)."""
        from datetime import date as date_cls

        rows = self.fetch_all(
            """
            SELECT DISTINCT registered_at::date AS occurrence_date
              FROM engineering.lmp_nonconformities
             ORDER BY occurrence_date ASC
            """,
            (),
        )
        out: list = []
        for row in rows:
            value = row.get("occurrence_date")
            if isinstance(value, date_cls):
                out.append(value)
            elif value is not None:
                text = str(value)[:10]
                try:
                    out.append(date_cls.fromisoformat(text))
                except ValueError:
                    continue
        return out

    @staticmethod
    def _replace_products(cursor: Any, record_id: str, lines: list[dict[str, str]]) -> None:
        if not lines:
            return
        cursor.executemany(
            """
            INSERT INTO engineering.lmp_nonconformity_products (
                nonconformity_id, product_code, product_description
            ) VALUES (%s, %s, %s)
            """,
            [
                (
                    record_id,
                    line["product_code"],
                    _blank_to_none(line.get("product_description")),
                )
                for line in lines
            ],
        )

    def _list_products(self, record_id: str) -> list[dict[str, str | None]]:
        rows = self.fetch_all(
            """
            SELECT product_code, product_description
              FROM engineering.lmp_nonconformity_products
             WHERE nonconformity_id = %s
             ORDER BY product_code ASC
            """,
            (record_id,),
        )
        return [
            {
                "product_code": str(r["product_code"]),
                "product_description": r.get("product_description"),
            }
            for r in rows
        ]

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
            "customer_name": row.get("customer_name"),
            "launch_date": _iso(row.get("launch_date")),
            "last_revision_date": _iso(row.get("last_revision_date")),
            "executed_by": row.get("executed_by"),
            "released_by": row.get("released_by"),
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
            products = self._list_products(record_id)
            payload["products"] = products
            payload["product_codes"] = [p["product_code"] for p in products]
        return payload
