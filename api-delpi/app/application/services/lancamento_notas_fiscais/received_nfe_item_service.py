"""Orquestra o XML da NF-e com a tradução Produto x Fornecedor.

A financial-api entrega os itens. Esta camada valida o CNPJ do fornecedor na SA2
e consulta SA5/SB1 em lote. A filial não entra na tradução.
"""

from __future__ import annotations

import re
from typing import Any

from app.core.exceptions import DatabaseConnectionError
from app.domain.services.lancamento_notas_fiscais.exceptions import InvoicePostingErpQueryError
from app.domain.services.lancamento_notas_fiscais.supplier_product_mapping_service import (
    SupplierProductResolution,
    resolve_supplier_product_codes,
)
from app.infrastructure.gateways.financial_received_invoice_gateway import (
    FinancialReceivedInvoiceGateway,
)
from app.infrastructure.persistence.totvs.invoice_posting_repositories.totvs_supplier_product_mapping_repository import (
    TotvsSupplierProductMappingRepository,
)
from app.infrastructure.persistence.totvs.supplier_repositories.totvs_supplier_repository import (
    TotvsSupplierRepository,
)
from app.utils.logger import log_error


class ReceivedNfeItemService:
    def __init__(
        self,
        *,
        gateway: FinancialReceivedInvoiceGateway,
        suppliers: TotvsSupplierRepository,
        mappings: TotvsSupplierProductMappingRepository,
    ) -> None:
        self._gateway = gateway
        self._suppliers = suppliers
        self._mappings = mappings

    def execute(
        self,
        *,
        authorization: str,
        document_id: str,
        provider_entity_id: str,
        access_key: str,
        branch: str,
        supplier_code: str,
        supplier_store: str,
    ) -> dict[str, Any]:
        code = (supplier_code or "").strip()
        store = (supplier_store or "").strip()
        if not code or not store:
            return _supplier_required(
                document_id=document_id,
                provider_entity_id=provider_entity_id,
                access_key=access_key,
                branch=branch,
            )

        detail = self._gateway.get_nfe_detail(
            authorization=authorization,
            document_id=document_id,
            provider_entity_id=provider_entity_id,
            access_key=access_key,
            branch=branch,
        )
        issuer_cnpj = _digits(_issuer_cnpj(detail))
        supplier = self._suppliers.get_supplier(supplier_code=code, supplier_store=store)
        supplier_cnpj = _digits(str((supplier or {}).get("tax_id") or ""))
        items = _xml_items(detail)
        if not supplier or not issuer_cnpj or supplier_cnpj != issuer_cnpj:
            return _with_items(
                detail,
                items=_without_internal_codes(items),
                state="issuer_mismatch",
            )

        distinct = _distinct_codes(items)
        try:
            rows = self._mappings.list_mappings(
                supplier_code=code,
                supplier_store=store,
                supplier_product_codes=distinct,
            )
        except DatabaseConnectionError as exc:
            log_error(f"Falha ao consultar Produto x Fornecedor: {type(exc).__name__}")
            raise InvoicePostingErpQueryError(
                "Não foi possível consultar a relação Produto x Fornecedor."
            ) from exc

        resolutions = resolve_supplier_product_codes(distinct, rows)
        unmapped = SupplierProductResolution("unmapped", None, None)
        enriched = []
        for item in items:
            code = str(item.get("supplierProductCode") or "")
            resolution = resolutions.get(code, unmapped)
            enriched.append(
                {
                    **item,
                    "internalProductCode": resolution.internal_product_code,
                    "internalProductDescription": resolution.internal_product_description,
                    "mappingStatus": resolution.mapping_status,
                }
            )
        return _with_items(detail, items=enriched, state="ready")


def _supplier_required(
    *,
    document_id: str,
    provider_entity_id: str,
    access_key: str,
    branch: str,
) -> dict[str, Any]:
    return {
        "documentType": "nfe",
        "documentId": document_id,
        "providerEntityId": provider_entity_id,
        "branchCode": branch,
        "accessKey": access_key,
        "productMapping": {"state": "supplier_required"},
        "items": [],
        "summary": _summary([]),
    }


def _with_items(detail: dict[str, Any], *, items: list[dict[str, Any]], state: str) -> dict[str, Any]:
    payload = dict(detail)
    payload["documentType"] = "nfe"
    payload["productMapping"] = {"state": state}
    payload["items"] = items
    payload["summary"] = _summary(items)
    return payload


def _without_internal_codes(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hidden = []
    for item in items:
        hidden.append(
            {
                **item,
                "internalProductCode": None,
                "internalProductDescription": None,
                "mappingStatus": None,
            }
        )
    return hidden


def _xml_items(detail: dict[str, Any]) -> list[dict[str, Any]]:
    raw = detail.get("items")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _distinct_codes(items: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    codes: list[str] = []
    for item in items:
        code = str(item.get("supplierProductCode") or "")
        if not code or code in seen:
            continue
        seen.add(code)
        codes.append(code)
    return codes


def _issuer_cnpj(detail: dict[str, Any]) -> str:
    issuer = detail.get("issuer")
    if not isinstance(issuer, dict):
        return ""
    return str(issuer.get("cnpj") or "")


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _summary(items: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"items": len(items), "mapped": 0, "unmapped": 0, "ambiguous": 0}
    for item in items:
        status = item.get("mappingStatus")
        if status in {"mapped", "unmapped", "ambiguous"}:
            summary[status] += 1
    return summary
