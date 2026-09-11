from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_COLUMNS = (
    "id, public_token, production_order, branch, product_code, product_description, "
    "product_unit, order_number, inspected_at, inspector_user_id, inspector_name, "
    "result, notes, inspected_quantity, qr_filename, view_count, is_active, "
    "audit_metadata, created_at, updated_at"
)

# Leitura admin: item do cliente vem do certificado 1:1 (não duplicar na etiqueta).
_ADMIN_COLUMNS = (
    "l.id, l.public_token, l.production_order, l.branch, l.product_code, "
    "l.product_description, l.product_unit, l.order_number, l.inspected_at, "
    "l.inspector_user_id, l.inspector_name, l.result, l.notes, "
    "l.inspected_quantity, l.qr_filename, l.view_count, l.is_active, "
    "l.audit_metadata, l.created_at, l.updated_at, "
    "c.customer_item, c.customer_item_rev, c.customer_name"
)
_ADMIN_FROM = """
              FROM quality_labels.inspection_labels AS l
              LEFT JOIN quality_labels.certificates AS c ON c.label_id = l.id
"""

# Unidades operacionais DELPI (filial TOTVS → nome legível).
_UNIT_NAMES = {"01": "Santa Catarina", "02": "Espírito Santo"}


def unit_name(code: str | None) -> str | None:
    if not code:
        return None
    return _UNIT_NAMES.get(str(code).strip(), str(code).strip())


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
        inspected_quantity: int | None = None,
        audit_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata_json = json.dumps(audit_metadata or {})
        row = self.execute_returning_one(
            f"""
            INSERT INTO quality_labels.inspection_labels (
                public_token, production_order, branch, product_code,
                product_description, product_unit, order_number,
                inspector_user_id, inspector_name, result, notes,
                inspected_quantity, audit_metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
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
                inspected_quantity,
                metadata_json,
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

    def delete_label(self, *, label_id: str) -> bool:
        row = self.execute_returning_one(
            """
            DELETE FROM quality_labels.inspection_labels
             WHERE id = %s
            RETURNING id
            """,
            (label_id,),
        )
        return row is not None

    def get_by_id(self, label_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"SELECT {_ADMIN_COLUMNS} {_ADMIN_FROM} WHERE l.id = %s",
            (label_id,),
        )

    def get_by_token(self, token: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"SELECT {_ADMIN_COLUMNS} {_ADMIN_FROM} WHERE l.public_token = %s",
            (token,),
        )

    def list_by_production_order(
        self,
        *,
        production_order: str,
        branch: str | None = None,
    ) -> list[dict[str, Any]]:
        where = "WHERE l.production_order = %s"
        params: list[Any] = [production_order]
        if branch:
            where += " AND l.branch = %s"
            params.append(branch)
        return self.fetch_all(
            f"""
            SELECT {_ADMIN_COLUMNS}
              {_ADMIN_FROM}
              {where}
             ORDER BY l.inspected_at DESC
            """,
            tuple(params),
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
        branches: list[str] | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        params: list[Any] = []
        if search:
            clauses.append(
                "(l.production_order ILIKE %s OR l.product_code ILIKE %s "
                "OR l.product_description ILIKE %s OR l.inspector_name ILIKE %s)"
            )
            like = f"%{search}%"
            params.extend([like, like, like, like])
        if branches:
            placeholders = ",".join(["%s"] * len(branches))
            clauses.append(f"l.branch IN ({placeholders})")
            params.extend(branches)

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""

        total_row = self.fetch_one(
            f"SELECT COUNT(*) AS total FROM quality_labels.inspection_labels AS l{where}",
            tuple(params),
        )
        total = int(total_row["total"]) if total_row else 0

        rows = self.fetch_all(
            f"""
            SELECT {_ADMIN_COLUMNS}
              {_ADMIN_FROM}
              {where}
             ORDER BY l.inspected_at DESC
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

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _audit_metadata(row: dict[str, Any]) -> dict[str, Any]:
        raw = row.get("audit_metadata")
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    @classmethod
    def to_admin_payload(
        cls,
        row: dict[str, Any],
        *,
        include_audit_metadata: bool = False,
    ) -> dict[str, Any]:
        payload = {
            "id": str(row.get("id")),
            "publicToken": row.get("public_token"),
            "productionOrder": row.get("production_order"),
            "branch": row.get("branch"),
            "branchName": unit_name(row.get("branch")),
            "productCode": row.get("product_code"),
            "productDescription": row.get("product_description"),
            "productUnit": row.get("product_unit"),
            "orderNumber": row.get("order_number"),
            "inspectedAt": cls._iso(row.get("inspected_at")),
            "inspectorName": row.get("inspector_name"),
            "result": row.get("result"),
            "notes": row.get("notes"),
            "inspectedQuantity": row.get("inspected_quantity"),
            "viewCount": row.get("view_count", 0),
            "isActive": row.get("is_active", True),
            "createdAt": cls._iso(row.get("created_at")),
            "customerItem": cls._optional_text(row.get("customer_item")),
            "customerItemRev": cls._optional_text(row.get("customer_item_rev")),
            "customerReference": cls.customer_reference_from_row(row),
            "customerName": cls.resolved_customer_name(row),
            "drawingCode": cls.drawing_code_from_row(row),
        }
        if include_audit_metadata:
            metadata = cls._audit_metadata(row)
            payload["auditMetadata"] = metadata
            payload["hasAuditMetadata"] = bool(metadata)
        return payload

    @classmethod
    def customer_reference_from_row(cls, row: dict[str, Any]) -> str | None:
        """SB1.B1_REFEREN capturado em audit_metadata.product.customerReference."""
        product = cls._audit_metadata(row).get("product")
        if not isinstance(product, dict):
            return None
        return cls._optional_text(
            product.get("customerReference") or product.get("customer_reference")
        )

    @classmethod
    def audit_captured_customer_reference(cls, row: dict[str, Any]) -> bool:
        """True quando o snapshot já tentou gravar B1_REFEREN (mesmo se vazio)."""
        product = cls._audit_metadata(row).get("product")
        return isinstance(product, dict) and (
            "customerReference" in product or "customer_reference" in product
        )

    @classmethod
    def drawing_code_from_row(cls, row: dict[str, Any]) -> str | None:
        """SB1.B1_CODDES capturado em audit_metadata.product.drawingCode."""
        product = cls._audit_metadata(row).get("product")
        if not isinstance(product, dict):
            return None
        return cls._optional_text(
            product.get("drawingCode") or product.get("drawing_code")
        )

    @classmethod
    def audit_captured_drawing_code(cls, row: dict[str, Any]) -> bool:
        """True quando o snapshot já tentou gravar B1_CODDES (mesmo se vazio)."""
        product = cls._audit_metadata(row).get("product")
        return isinstance(product, dict) and (
            "drawingCode" in product or "drawing_code" in product
        )

    @classmethod
    def resolved_customer_reference(cls, row: dict[str, Any]) -> str | None:
        """Item manual do certificado vence o snapshot do cadastro SB1."""
        return cls._optional_text(row.get("customer_item")) or cls.customer_reference_from_row(
            row
        )

    @classmethod
    def customer_name_from_row(cls, row: dict[str, Any]) -> str | None:
        customer = cls._audit_metadata(row).get("customer")
        if not isinstance(customer, dict):
            return None
        return cls._optional_text(customer.get("name"))

    @classmethod
    def audit_captured_customer_name(cls, row: dict[str, Any]) -> bool:
        return "customer" in cls._audit_metadata(row)

    @classmethod
    def resolved_customer_name(cls, row: dict[str, Any]) -> str | None:
        """Nome no certificado vence o snapshot (pedido ou última NF)."""
        return cls._optional_text(row.get("customer_name")) or cls.customer_name_from_row(row)

    @classmethod
    def to_public_payload(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "productCode": row.get("product_code"),
            "productDescription": row.get("product_description"),
            "productUnit": row.get("product_unit"),
            "productionOrder": row.get("production_order"),
            "branch": row.get("branch"),
            "branchName": unit_name(row.get("branch")),
            "inspectedAt": cls._iso(row.get("inspected_at")),
            "inspectorName": row.get("inspector_name"),
            "result": row.get("result"),
            "companyName": "Delpi Conexões Elétricas",
            "customerReference": cls.resolved_customer_reference(row),
            "customerName": cls.resolved_customer_name(row),
            "drawingCode": cls.drawing_code_from_row(row),
        }
