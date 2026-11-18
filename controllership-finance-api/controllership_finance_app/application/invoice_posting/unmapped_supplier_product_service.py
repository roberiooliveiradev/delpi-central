"""Histórico de produtos da NF-e sem código Delpi reconhecido.

A observação acontece depois que a solicitação já existe. Falha da consulta,
da gravação ou da notificação não desfaz o cadastro.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from controllership_finance_app.application.invoice_posting.received_nfe_item_service import (
    ReceivedNfeItemService,
)
from controllership_finance_app.application.invoice_posting.lnf_portal_notification_service import (
    notify_unmapped_supplier_products,
)
from controllership_finance_app.application.invoice_posting.logging_util import log_error

_OBSERVED_STATUSES = frozenset({"unmapped", "ambiguous"})


def unmapped_product_rows(
    detail: dict[str, Any],
    *,
    request_id: str,
    branch_code: str,
    supplier_code: str,
    supplier_store: str,
    supplier_name: str,
    document_number: str,
    series: str,
) -> list[dict[str, Any]]:
    """Itens `ready` sem um código Delpi reconhecido. Código em branco não entra."""
    mapping = detail.get("productMapping")
    if not isinstance(mapping, dict) or mapping.get("state") != "ready":
        return []
    raw_items = detail.get("items")
    if not isinstance(raw_items, list):
        return []

    rows: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        status = str(item.get("mappingStatus") or "")
        code = str(item.get("supplierProductCode") or "").strip()
        if status not in _OBSERVED_STATUSES or not code:
            continue
        rows.append(
            {
                "request_id": request_id,
                "branch_code": branch_code,
                "supplier_code": supplier_code,
                "supplier_store": supplier_store,
                "supplier_name": supplier_name,
                "supplier_product_code": code[:60],
                "supplier_product_description": _clip(
                    item.get("supplierProductDescription"), 120
                ),
                "quantity": _quantity(item.get("quantity")),
                "unit": _clip(item.get("unit"), 6),
                "mapping_status": status,
                "document_number": document_number,
                "series": series,
            }
        )
    return rows


def indexed_nfe_product_rows(detail: dict[str, Any], *, request_id: str) -> list[dict[str, Any]]:
    """Indexa códigos de itens da NF-e somente quando SA2/emitente validaram.

    Sem estado ready, não inferimos código Delpi do pedido ou do fornecedor.
    """
    mapping = detail.get("productMapping")
    if not isinstance(mapping, dict) or mapping.get("state") != "ready":
        return []
    items = detail.get("items")
    if not isinstance(items, list):
        return []
    indexed: list[dict[str, Any]] = []
    for position, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        state = str(item.get("mappingStatus") or "").strip()
        if state not in {"mapped", "unmapped", "ambiguous"}:
            continue
        supplier_code = str(item.get("supplierProductCode") or "").strip()[:60] or None
        internal_code = (
            str(item.get("internalProductCode") or "").strip()[:40] or None
            if state == "mapped"
            else None
        )
        indexed.append(
            {
                "request_id": request_id,
                "item_position": position,
                "supplier_product_code": supplier_code,
                "internal_product_code": internal_code,
                "mapping_status": state,
            }
        )
    return indexed


class UnmappedSupplierProductRecorder:
    def __init__(self, *, items: ReceivedNfeItemService, requests: Any) -> None:
        self._items = items
        self._requests = requests

    def record(
        self,
        *,
        authorization: str,
        document_id: str,
        provider_entity_id: str,
        access_key: str,
        branch: str,
        supplier_code: str,
        supplier_store: str,
        supplier_name: str,
        document_number: str,
        series: str,
        request_id: str,
    ) -> None:
        try:
            detail = self._items.execute(
                authorization=authorization,
                document_id=document_id,
                provider_entity_id=provider_entity_id,
                access_key=access_key,
                branch=branch,
                supplier_code=supplier_code,
                supplier_store=supplier_store,
            )
            indexed_rows = indexed_nfe_product_rows(detail, request_id=request_id)
            rows = unmapped_product_rows(
                detail,
                request_id=request_id,
                branch_code=branch,
                supplier_code=supplier_code,
                supplier_store=supplier_store,
                supplier_name=supplier_name,
                document_number=document_number,
                series=series,
            )
        except Exception:
            log_error(
                "Falha ao observar produtos sem código Delpi "
                f"na solicitação {request_id}."
            )
            return
        if indexed_rows:
            try:
                self._requests.replace_indexed_nfe_product_rows(indexed_rows)
            except Exception:
                # A falha no índice auxiliar nunca cancela a NF-e já cadastrada.
                log_error(
                    "Falha ao indexar itens da NF-e "
                    f"na solicitação {request_id}."
                )
        if not rows:
            return
        try:
            inserted = self._requests.insert_unmapped_supplier_products(rows)
        except Exception:
            log_error(
                "Falha ao gravar produtos sem código Delpi "
                f"na solicitação {request_id}."
            )
            return
        if inserted:
            from controllership_finance_app.application.invoice_posting.change_notifier import (
                get_invoice_posting_change_notifier,
            )

            get_invoice_posting_change_notifier().unmapped_products_changed()
        notify_unmapped_supplier_products(
            request_id=request_id,
            branch_code=branch,
            document_number=document_number,
            series=series,
            supplier_name=supplier_name,
            product_count=len(rows),
        )


class ListUnmappedSupplierProductsUseCase:
    def __init__(self, requests: Any) -> None:
        self._requests = requests

    def execute(
        self,
        *,
        filters: dict[str, Any],
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        return self._requests.list_unmapped_supplier_products(
            filters=filters,
            page=page,
            page_size=page_size,
        )


def _clip(value: Any, limit: int) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text[:limit]


def _quantity(value: Any) -> Decimal | None:
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None
