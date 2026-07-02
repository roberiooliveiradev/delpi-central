from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_COLUMNS = (
    "id, public_token, production_order, branch, product_code, product_description, "
    "product_unit, order_number, inspected_at, inspector_user_id, inspector_name, "
    "result, notes, qr_filename, view_count, is_active, created_at, updated_at"
)


class PostgresQualityLabelsRepository(PluginBaseRepository):
    def insert_label(
        self,
        *,
        public_token: str,
        production_order: str,
        branch: str | None,
        product_code: str,
        product_description: str,
        product_unit: str | None,
        order_number: str | None,
        inspector_user_id: str,
        inspector_name: str,
        result: str,
        notes: str | None,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO quality_labels.inspection_labels (
                public_token, production_order, branch, product_code,
                product_description, product_unit, order_number,
                inspector_user_id, inspector_name, result, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {_COLUMNS}
            """,
            (
                public_token,
                production_order,
                branch,
                product_code,
                product_description,
                product_unit,
                order_number,
                inspector_user_id,
                inspector_name,
                result,
                notes,
            ),
        )
        if row is None:
            raise RuntimeError("Falha ao inserir a etiqueta de qualidade.")
        return row

    def set_qr_filename(self, *, label_id: str, qr_filename: str) -> dict[str, Any] | None:
        return self.execute_returning_one(
            f"""
            UPDATE quality_labels.inspection_labels
               SET qr_filename = %s,
                   updated_at = NOW()
             WHERE id = %s
            RETURNING {_COLUMNS}
            """,
            (qr_filename, label_id),
        )

    def update_label(
        self,
        *,
        label_id: str,
        notes: str | None,
        result: str | None,
    ) -> dict[str, Any] | None:
        return self.execute_returning_one(
            f"""
            UPDATE quality_labels.inspection_labels
               SET notes = COALESCE(%s, notes),
                   result = COALESCE(%s, result),
                   updated_at = NOW()
             WHERE id = %s
            RETURNING {_COLUMNS}
            """,
            (notes, result, label_id),
        )

    def set_active(self, *, label_id: str, is_active: bool) -> dict[str, Any] | None:
        return self.execute_returning_one(
            f"""
            UPDATE quality_labels.inspection_labels
               SET is_active = %s,
                   updated_at = NOW()
             WHERE id = %s
            RETURNING {_COLUMNS}
            """,
            (is_active, label_id),
        )

    def get_by_id(self, label_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"SELECT {_COLUMNS} FROM quality_labels.inspection_labels WHERE id = %s",
            (label_id,),
        )

    def get_by_token(self, token: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"SELECT {_COLUMNS} FROM quality_labels.inspection_labels WHERE public_token = %s",
            (token,),
        )

    def increment_view_count(self, token: str) -> None:
        self.execute(
            """
            UPDATE quality_labels.inspection_labels
               SET view_count = view_count + 1
             WHERE public_token = %s
            """,
            (token,),
        )

    def list_labels(
        self,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        where = ""
        params: list[Any] = []
        if search:
            where = (
                " WHERE production_order ILIKE %s OR product_code ILIKE %s "
                "OR product_description ILIKE %s OR inspector_name ILIKE %s"
            )
            like = f"%{search}%"
            params = [like, like, like, like]

        total_row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM quality_labels.inspection_labels{where}",
            tuple(params),
        )
        total = int(total_row["total"]) if total_row else 0

        rows = self.fetch_all(
            f"""
            SELECT {_COLUMNS}
              FROM quality_labels.inspection_labels{where}
             ORDER BY inspected_at DESC
             LIMIT %s OFFSET %s
            """,
            tuple(params + [limit, offset]),
        )
        return rows, total

    @staticmethod
    def _iso(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    @classmethod
    def to_admin_payload(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row.get("id")),
            "publicToken": row.get("public_token"),
            "productionOrder": row.get("production_order"),
            "branch": row.get("branch"),
            "productCode": row.get("product_code"),
            "productDescription": row.get("product_description"),
            "productUnit": row.get("product_unit"),
            "orderNumber": row.get("order_number"),
            "inspectedAt": cls._iso(row.get("inspected_at")),
            "inspectorName": row.get("inspector_name"),
            "result": row.get("result"),
            "notes": row.get("notes"),
            "viewCount": row.get("view_count", 0),
            "isActive": row.get("is_active", True),
            "createdAt": cls._iso(row.get("created_at")),
        }

    @classmethod
    def to_public_payload(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "productCode": row.get("product_code"),
            "productDescription": row.get("product_description"),
            "productUnit": row.get("product_unit"),
            "productionOrder": row.get("production_order"),
            "branch": row.get("branch"),
            "inspectedAt": cls._iso(row.get("inspected_at")),
            "inspectorName": row.get("inspector_name"),
            "result": row.get("result"),
            "companyName": "Delpi Conexões Elétricas",
        }
