from __future__ import annotations

from typing import Any

from app.application.services.quality_labels.quality_labels_certificate_storage import (
    QualityLabelsCertificateStorage,
)
from app.application.use_cases.production.get_order_customer_by_op_use_case import (
    GetOrderCustomerByOpUseCase,
)
from app.infrastructure.pdf.quality_labels.quality_certificate_pdf_renderer import (
    QualityCertificatePdfRenderer,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_audit_repository import (
    PostgresQualityLabelsAuditRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_certificate_repository import (
    PostgresQualityLabelsCertificateRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_checklist_template_repository import (
    PostgresQualityLabelsChecklistTemplateRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_inspector_repository import (
    PostgresQualityLabelsInspectorRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_repository import (
    PostgresQualityLabelsRepository,
    unit_name,
)
from app.utils.logger import log_error

DEFAULT_DOC_REF = "RQ-032 – Rev.00 – 21/01/2021"
DEFAULT_NOTE = "Nota: Inspeção realizada através do desenho."

_SAMPLE_TYPES = {"amostra", "lote_piloto", "fornecimento"}
_STATUSES = {"A", "R", "NA"}

EVENT_CERT_SAVED = "certificate_saved"
EVENT_CERT_ISSUED = "certificate_issued"


class QualityLabelsCertificateError(Exception):
    """Erro de regra de negócio do certificado de qualidade."""


class QualityLabelsCertificateService:
    def __init__(
        self,
        *,
        certificate_repository: PostgresQualityLabelsCertificateRepository,
        label_repository: PostgresQualityLabelsRepository,
        template_repository: PostgresQualityLabelsChecklistTemplateRepository,
        inspector_repository: PostgresQualityLabelsInspectorRepository,
        signature_storage,
        certificate_storage: QualityLabelsCertificateStorage,
        pdf_renderer: QualityCertificatePdfRenderer,
        order_customer_use_case: GetOrderCustomerByOpUseCase,
        audit_repository: PostgresQualityLabelsAuditRepository,
    ) -> None:
        self._certificate_repository = certificate_repository
        self._label_repository = label_repository
        self._template_repository = template_repository
        self._inspector_repository = inspector_repository
        self._signature_storage = signature_storage
        self._certificate_storage = certificate_storage
        self._pdf_renderer = pdf_renderer
        self._order_customer_use_case = order_customer_use_case
        self._audit_repository = audit_repository

    # ------------------------------------------------------------------ read

    def get_or_init(self, *, label_id: str) -> dict[str, Any]:
        label = self._label_repository.get_by_id(label_id)
        if label is None:
            raise QualityLabelsCertificateError("Etiqueta não encontrada.")

        existing = self._certificate_repository.get_by_label(label_id)
        if existing is not None:
            items = self._certificate_repository.list_items(str(existing["id"]))
            payload = self._certificate_repository.to_payload(existing, items)
            payload.update(self._label_context(label))
            return payload

        return self._build_draft(label)

    # ----------------------------------------------------------------- write

    def save(
        self,
        *,
        label_id: str,
        data: dict[str, Any],
        issue: bool,
        actor_user_id: str,
        actor_name: str,
    ) -> dict[str, Any]:
        label = self._label_repository.get_by_id(label_id)
        if label is None:
            raise QualityLabelsCertificateError("Etiqueta não encontrada.")

        sample_type = str(data.get("sampleType") or "fornecimento").strip().lower()
        if sample_type not in _SAMPLE_TYPES:
            sample_type = "fornecimento"

        customer_source = str(data.get("customerSource") or "manual").strip().lower()
        if customer_source not in {"manual", "totvs"}:
            customer_source = "manual"

        row = self._certificate_repository.upsert(
            label_id=label_id,
            doc_ref=str(data.get("docRef") or DEFAULT_DOC_REF).strip() or DEFAULT_DOC_REF,
            sample_type=sample_type,
            quantity=self._clean(data.get("quantity")),
            sample_quantity=self._clean(data.get("sampleQuantity")),
            customer_code=self._clean(data.get("customerCode")),
            customer_store=self._clean(data.get("customerStore")),
            customer_name=self._clean(data.get("customerName")),
            customer_item=self._clean(data.get("customerItem")),
            customer_item_rev=self._clean(data.get("customerItemRev")),
            customer_source=customer_source,
            delpi_notes=self._clean(data.get("delpiNotes")),
            customer_notes=self._clean(data.get("customerNotes")),
            inspector_user_id=actor_user_id,
            inspector_name=actor_name,
            status="issued" if issue else "draft",
        )
        certificate_id = str(row["id"])

        items = self._normalize_items(data.get("items"))
        self._certificate_repository.replace_items(
            certificate_id=certificate_id, items=items
        )

        if issue:
            pdf_bytes = self._render_pdf(certificate_row=row, label=label, items=items)
            stored = self._certificate_storage.save(
                certificate_id=certificate_id, content=pdf_bytes
            )
            issued = self._certificate_repository.set_issued(
                certificate_id=certificate_id, pdf_filename=stored
            )
            row = issued or row

        self._record_event(
            EVENT_CERT_ISSUED if issue else EVENT_CERT_SAVED,
            label=label,
            actor_user_id=actor_user_id,
            actor_name=actor_name,
        )

        stored_items = self._certificate_repository.list_items(certificate_id)
        payload = self._certificate_repository.to_payload(row, stored_items)
        payload.update(self._label_context(label))
        return payload

    def read_pdf(self, *, label_id: str) -> bytes | None:
        label = self._label_repository.get_by_id(label_id)
        if label is None:
            return None
        row = self._certificate_repository.get_by_label(label_id)
        if row is None:
            return None
        if row.get("pdf_filename"):
            stored = self._certificate_storage.read(row["pdf_filename"])
            if stored:
                return stored
        # Sem PDF emitido: gera preview on-the-fly a partir do estado atual.
        items = self._certificate_repository.list_items(str(row["id"]))
        return self._render_pdf(certificate_row=row, label=label, items=items)

    # --------------------------------------------------------------- helpers

    def _build_draft(self, label: dict[str, Any]) -> dict[str, Any]:
        customer = self._order_customer_use_case.execute(
            production_order=str(label.get("production_order") or ""),
            branch=label.get("branch"),
        )
        inspected_qty = label.get("inspected_quantity")
        sample_quantity = f"{inspected_qty} peças" if inspected_qty else None

        template = self._template_repository.list_active()
        items = [
            {
                "position": item.get("position"),
                "description": item.get("description"),
                "status": "A",
                "isCustom": False,
            }
            for item in template
        ]
        draft: dict[str, Any] = {
            "id": None,
            "labelId": str(label.get("id")),
            "docRef": DEFAULT_DOC_REF,
            "sampleType": "fornecimento",
            "quantity": None,
            "sampleQuantity": sample_quantity,
            "customerCode": (customer or {}).get("customer_code"),
            "customerStore": (customer or {}).get("customer_store"),
            "customerName": (customer or {}).get("customer_name"),
            "customerItem": None,
            "customerItemRev": None,
            "customerSource": "totvs" if customer else "manual",
            "delpiNotes": None,
            "customerNotes": None,
            "inspectorName": label.get("inspector_name"),
            "status": "draft",
            "hasPdf": False,
            "issuedAt": None,
            "updatedAt": None,
            "items": items,
        }
        draft.update(self._label_context(label))
        return draft

    @staticmethod
    def _label_context(label: dict[str, Any]) -> dict[str, Any]:
        return {
            "productionOrder": label.get("production_order"),
            "productCode": label.get("product_code"),
            "productDescription": label.get("product_description"),
            "productUnit": label.get("product_unit"),
            "branch": label.get("branch"),
            "branchName": unit_name(label.get("branch")),
        }

    def _normalize_items(self, raw: Any) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        if not isinstance(raw, list):
            return items
        for index, entry in enumerate(raw):
            if not isinstance(entry, dict):
                continue
            description = str(entry.get("description") or "").strip()
            if not description:
                continue
            status = str(entry.get("status") or "A").strip().upper()
            if status not in _STATUSES:
                status = "A"
            items.append(
                {
                    "position": entry.get("position") or index + 1,
                    "description": description,
                    "status": status,
                    "is_custom": bool(entry.get("isCustom", False)),
                }
            )
        return items

    def _render_pdf(
        self,
        *,
        certificate_row: dict[str, Any],
        label: dict[str, Any],
        items: list[dict[str, Any]],
    ) -> bytes:
        signature_png = None
        try:
            inspector = self._inspector_repository.get_by_user(
                str(certificate_row.get("inspector_user_id") or "")
            )
            if inspector and inspector.get("signature_filename"):
                signature_png = self._signature_storage.read(
                    inspector["signature_filename"]
                )
        except Exception as exc:  # noqa: BLE001 - assinatura é opcional
            log_error(f"Falha ao carregar assinatura do inspetor: {exc}")

        data = {
            "doc_ref": certificate_row.get("doc_ref") or DEFAULT_DOC_REF,
            "sample_type": certificate_row.get("sample_type"),
            "customer_name": certificate_row.get("customer_name"),
            "customer_item": certificate_row.get("customer_item"),
            "customer_item_rev": certificate_row.get("customer_item_rev"),
            "product_code": label.get("product_code"),
            "production_order": label.get("production_order"),
            "quantity": certificate_row.get("quantity"),
            "sample_quantity": certificate_row.get("sample_quantity"),
            "items": [
                {
                    "position": item.get("position"),
                    "description": item.get("description"),
                    "status": item.get("status"),
                }
                for item in items
            ],
            "note": DEFAULT_NOTE,
            "delpi_notes": certificate_row.get("delpi_notes"),
            "customer_notes": certificate_row.get("customer_notes"),
            "inspector_name": certificate_row.get("inspector_name"),
            "signature_png": signature_png,
        }
        return self._pdf_renderer.render(data)

    def _record_event(
        self,
        event_type: str,
        *,
        label: dict[str, Any],
        actor_user_id: str | None,
        actor_name: str | None,
    ) -> None:
        try:
            self._audit_repository.insert_event(
                event_type=event_type,
                label_id=str(label["id"]) if label.get("id") else None,
                production_order=label.get("production_order"),
                product_code=label.get("product_code"),
                branch=label.get("branch"),
                result=label.get("result"),
                actor_user_id=actor_user_id,
                actor_name=actor_name,
            )
        except Exception as exc:  # noqa: BLE001 - auditoria é best-effort
            log_error(f"Falha ao registrar evento de certificado ({event_type}): {exc}")

    @staticmethod
    def _clean(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
