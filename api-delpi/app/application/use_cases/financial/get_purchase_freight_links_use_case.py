from __future__ import annotations

from typing import Any

from app.application.dto.financial.purchase_freight_links_request import (
    PurchaseFreightLinksRequest,
)
from app.application.services.financial.purchase_freight_cache import (
    get_cached_purchase_freight_links,
    purchase_freight_links_cache_key,
    set_cached_purchase_freight_links,
)
from app.domain.ports.financial.purchase_freight_repository_port import (
    PurchaseFreightRepositoryPort,
)

DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT = 20000


class GetPurchaseFreightLinksUseCase:
    """Lista vínculos NF de compra x CT-e (SF8010) com os valores de cada documento.

    Entrega contrato puro: quem consome calcula rateio, percentual e limite.
    ``in_filter`` distingue a linha pedida pelo filtro das linhas trazidas apenas
    para fechar a base de rateio do CT-e.
    """

    def __init__(self, repository: PurchaseFreightRepositoryPort):
        self._repository = repository

    def execute(
        self,
        request: PurchaseFreightLinksRequest,
        *,
        limit: int | None = None,
    ) -> dict:
        resolved_limit = self._resolve_limit(limit)
        cache_key = purchase_freight_links_cache_key(request, limit=resolved_limit)
        cached = get_cached_purchase_freight_links(cache_key)
        if cached is not None:
            return cached

        rows = self._repository.list_purchase_freight_links(
            request, limit=resolved_limit
        )
        truncated = len(rows) > resolved_limit
        items = [self._map_row(row) for row in rows[:resolved_limit]]
        result = {
            "branch": request.branch or "consolidated",
            "items": items,
            "pagination": {
                "limit": resolved_limit,
                "offset": 0,
                "returned": len(items),
                "is_complete": not truncated,
            },
            "summary": self._build_summary(items, request),
        }

        set_cached_purchase_freight_links(cache_key, result)
        return result

    @staticmethod
    def _resolve_limit(raw: int | None) -> int:
        try:
            value = (
                int(raw) if raw is not None else DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT
            )
        except (TypeError, ValueError):
            value = DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT
        return min(max(value, 1), DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT)

    @staticmethod
    def _build_summary(
        items: list[dict[str, Any]],
        request: PurchaseFreightLinksRequest,
    ) -> dict[str, Any]:
        return {
            "total_records": len(items),
            "in_filter_records": sum(1 for item in items if item["in_filter"]),
            "branch": request.branch,
            "branch_filter_applied": request.branch is not None,
            "issue_start": request.issue_start or "",
            "issue_end": request.issue_end or "",
            "entry_start": request.entry_start or "",
            "entry_end": request.entry_end or "",
        }

    @classmethod
    def _map_row(cls, row: dict[str, Any]) -> dict[str, Any]:
        invoice_found = cls._as_bool(row.get("invoice_found"))
        freight_found = cls._as_bool(row.get("freight_found"))
        return {
            "branch": cls._as_text(row.get("branch")),
            "in_filter": cls._as_bool(row.get("in_filter")),
            "link_entry_date": cls._iso_date(row.get("link_entry_date")),
            "invoice_found": invoice_found,
            "invoice_document": cls._as_text(row.get("invoice_document")),
            "invoice_series": cls._as_text(row.get("invoice_series")),
            "supplier_code": cls._as_text(row.get("supplier_code")),
            "supplier_store": cls._as_text(row.get("supplier_store")),
            "supplier_name": cls._as_text(row.get("supplier_name")),
            "invoice_goods_value": cls._as_optional_float(
                row.get("invoice_goods_value") if invoice_found else None
            ),
            "invoice_issue_date": cls._iso_date(row.get("invoice_issue_date")),
            "invoice_entry_date": cls._iso_date(row.get("invoice_entry_date")),
            "freight_found": freight_found,
            "freight_document": cls._as_text(row.get("freight_document")),
            "freight_series": cls._as_text(row.get("freight_series")),
            "carrier_code": cls._as_text(row.get("carrier_code")),
            "carrier_store": cls._as_text(row.get("carrier_store")),
            "carrier_name": cls._as_text(row.get("carrier_name")),
            "freight_gross_value": cls._as_optional_float(
                row.get("freight_gross_value") if freight_found else None
            ),
            "freight_issue_date": cls._iso_date(row.get("freight_issue_date")),
            "freight_access_key": cls._as_text(row.get("freight_access_key")),
            "freight_document_type": cls._as_text(row.get("freight_document_type")),
            "freight_document_kind": cls._as_text(row.get("freight_document_kind")),
        }

    @staticmethod
    def _as_text(value: Any) -> str:
        return str(value or "").strip()

    @staticmethod
    def _as_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        try:
            return int(value) == 1
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _as_optional_float(value: Any) -> float | None:
        """``None`` significa documento não localizado — nunca vira zero silencioso."""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _iso_date(raw: Any) -> str:
        text = str(raw or "").strip()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return text[:10]
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) >= 8:
            return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
        return ""
