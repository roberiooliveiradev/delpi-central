from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_COLUMNS = (
    "id, label_id, doc_ref, sample_type, quantity, sample_quantity, "
    "customer_code, customer_store, customer_name, customer_item, customer_item_rev, "
    "customer_source, delpi_notes, customer_notes, inspector_user_id, inspector_name, "
    "status, pdf_filename, issued_at, created_at, updated_at"
)


class PostgresQualityLabelsCertificateRepository(PluginBaseRepository):
    """Certificado de Qualidade (1:1 com a etiqueta) + itens do checklist."""

    def get_by_label(self, label_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"SELECT {_COLUMNS} FROM quality_labels.certificates WHERE label_id = %s",
            (label_id,),
        )

    def get_by_id(self, certificate_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"SELECT {_COLUMNS} FROM quality_labels.certificates WHERE id = %s",
            (certificate_id,),
        )

    def list_items(self, certificate_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT id, position, description, status, is_custom
              FROM quality_labels.certificate_items
             WHERE certificate_id = %s
             ORDER BY position ASC
            """,
            (certificate_id,),
        )

    def upsert(
        self,
        *,
        label_id: str,
        doc_ref: str,
        sample_type: str,
        quantity: str | None,
        sample_quantity: str | None,
        customer_code: str | None,
        customer_store: str | None,
        customer_name: str | None,
        customer_item: str | None,
        customer_item_rev: str | None,
        customer_source: str,
        delpi_notes: str | None,
        customer_notes: str | None,
        inspector_user_id: str,
        inspector_name: str,
        status: str,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO quality_labels.certificates (
                label_id, doc_ref, sample_type, quantity, sample_quantity,
                customer_code, customer_store, customer_name, customer_item,
                customer_item_rev, customer_source, delpi_notes, customer_notes,
                inspector_user_id, inspector_name, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (label_id) DO UPDATE SET
                doc_ref = EXCLUDED.doc_ref,
                sample_type = EXCLUDED.sample_type,
                quantity = EXCLUDED.quantity,
                sample_quantity = EXCLUDED.sample_quantity,
                customer_code = EXCLUDED.customer_code,
                customer_store = EXCLUDED.customer_store,
                customer_name = EXCLUDED.customer_name,
                customer_item = EXCLUDED.customer_item,
                customer_item_rev = EXCLUDED.customer_item_rev,
                customer_source = EXCLUDED.customer_source,
                delpi_notes = EXCLUDED.delpi_notes,
                customer_notes = EXCLUDED.customer_notes,
                inspector_user_id = EXCLUDED.inspector_user_id,
                inspector_name = EXCLUDED.inspector_name,
                status = EXCLUDED.status,
                updated_at = NOW()
            RETURNING {_COLUMNS}
            """,
            (
                label_id,
                doc_ref,
                sample_type,
                quantity,
                sample_quantity,
                customer_code,
                customer_store,
                customer_name,
                customer_item,
                customer_item_rev,
                customer_source,
                delpi_notes,
                customer_notes,
                inspector_user_id,
                inspector_name,
                status,
            ),
        )
        if row is None:
            raise RuntimeError("Falha ao salvar o certificado de qualidade.")
        return row

    def replace_items(
        self,
        *,
        certificate_id: str,
        items: list[dict[str, Any]],
    ) -> None:
        self.execute(
            "DELETE FROM quality_labels.certificate_items WHERE certificate_id = %s",
            (certificate_id,),
            auto_commit=False,
        )
        if items:
            self.execute_many(
                """
                INSERT INTO quality_labels.certificate_items (
                    certificate_id, position, description, status, is_custom
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                [
                    (
                        certificate_id,
                        int(item.get("position") or index + 1),
                        str(item.get("description") or "").strip(),
                        str(item.get("status") or "A").upper(),
                        bool(item.get("is_custom", False)),
                    )
                    for index, item in enumerate(items)
                ],
                auto_commit=False,
            )
        self.commit()

    def set_issued(
        self,
        *,
        certificate_id: str,
        pdf_filename: str,
    ) -> dict[str, Any] | None:
        return self.execute_returning_one(
            f"""
            UPDATE quality_labels.certificates
               SET status = 'issued',
                   pdf_filename = %s,
                   issued_at = NOW(),
                   updated_at = NOW()
             WHERE id = %s
            RETURNING {_COLUMNS}
            """,
            (pdf_filename, certificate_id),
        )

    @staticmethod
    def _iso(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    @classmethod
    def to_payload(
        cls,
        row: dict[str, Any],
        items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "id": str(row.get("id")),
            "labelId": str(row.get("label_id")),
            "docRef": row.get("doc_ref"),
            "sampleType": row.get("sample_type"),
            "quantity": row.get("quantity"),
            "sampleQuantity": row.get("sample_quantity"),
            "customerCode": row.get("customer_code"),
            "customerStore": row.get("customer_store"),
            "customerName": row.get("customer_name"),
            "customerItem": row.get("customer_item"),
            "customerItemRev": row.get("customer_item_rev"),
            "customerSource": row.get("customer_source"),
            "delpiNotes": row.get("delpi_notes"),
            "customerNotes": row.get("customer_notes"),
            "inspectorName": row.get("inspector_name"),
            "status": row.get("status"),
            "hasPdf": bool(row.get("pdf_filename")),
            "issuedAt": cls._iso(row.get("issued_at")),
            "updatedAt": cls._iso(row.get("updated_at")),
            "items": [cls.item_payload(item) for item in (items or [])],
        }

    @staticmethod
    def item_payload(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "position": row.get("position"),
            "description": row.get("description"),
            "status": row.get("status"),
            "isCustom": bool(row.get("is_custom", False)),
        }
