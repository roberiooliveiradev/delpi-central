"""Orquestra a análise de frete das compras: escopo, corte, rateio e paginação.

O rateio precisa do fecho da base de cada CT-e, então a api-delpi devolve o
conjunto inteiro de vínculos e a paginação acontece aqui, depois do cálculo.
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Iterable, Sequence

from financial_app.application.services.content_loader import load_content
from financial_app.application.services.payload_mapping import (
    as_int,
    as_str,
    clamp_page,
    clamp_page_size,
    unwrap_data,
)
from financial_app.application.services.response_cache import cached_fetch
from financial_app.core.security import FIN_FREIGHT_VIEW
from financial_app.domain.errors import FinancialError, InvalidPeriod
from financial_app.domain.ports.financial_data_gateway import FinancialDataGateway
from financial_app.domain.services.branch_access_service import BranchAccessService
from financial_app.domain.services.freight_allocation_service import (
    SITUATION_ABOVE_LIMIT,
    SITUATION_INCONSISTENT,
    FreightAllocationResult,
    FreightAllocationService,
    FreightInconsistency,
    FreightInvoice,
    FreightLink,
)

_ZERO = Decimal("0")
_CENTS = Decimal("0.01")
_SITUATION_ALL = "all"


class InvalidFreightQuery(FinancialError):
    """Filtro de frete fora do domínio aceito."""


def _settings() -> dict[str, Any]:
    return load_content("freight.json")


class FreightService:
    def __init__(
        self,
        gateway: FinancialDataGateway,
        *,
        branch_access: BranchAccessService | None = None,
        allocation: FreightAllocationService | None = None,
    ) -> None:
        self._gateway = gateway
        self._branch_access = branch_access or BranchAccessService()
        self._allocation = allocation or FreightAllocationService()

    # ------------------------------------------------------------- dashboard

    def dashboard(
        self,
        user: object | None,
        *,
        branch: str | None = None,
        issue_start: str | None = None,
        issue_end: str | None = None,
        entry_start: str | None = None,
        entry_end: str | None = None,
        supplier: str | None = None,
        invoice_document: str | None = None,
        freight_document: str | None = None,
        situation: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        cfg = _settings()
        scope = self._prepare(
            user,
            cfg,
            branch=branch,
            issue_start=issue_start,
            issue_end=issue_end,
            entry_start=entry_start,
            entry_end=entry_end,
        )
        resolved_situation = self._resolve_situation(cfg, situation)
        sort_field, direction = self._resolve_sort(cfg, "invoices", sort_by, sort_dir)
        page_n = clamp_page(page, as_int((cfg.get("pagination") or {}).get("defaultPage"), 1))
        size_n = self._resolve_page_size(cfg, page_size)

        result, is_complete = self._analyse(
            cfg,
            scope,
            supplier=supplier,
            invoice_document=invoice_document,
            freight_document=freight_document,
            refresh=refresh,
        )

        invoices = self._filter_invoices(result.invoices, resolved_situation)
        ordered = self._sort_invoices(invoices, sort_field, direction)
        window, pagination = self._paginate(ordered, page_n, size_n, is_complete)

        return {
            "period": {
                "issueStart": scope["issue_start"],
                "issueEnd": scope["issue_end"],
                "entryStart": scope["entry_start"],
                "entryEnd": scope["entry_end"],
            },
            "branch": scope["branch"],
            "situation": resolved_situation,
            "sort": {"sortBy": sort_field, "sortDir": direction},
            "pagination": pagination,
            "summary": self._summary(result.invoices, cfg),
            "limits": {
                code: str(limit)
                for code, limit in self._branch_limits(cfg).items()
            },
            "items": [self._map_invoice(invoice) for invoice in window],
        }

    # -------------------------------------------------------- inconsistências

    def inconsistencies(
        self,
        user: object | None,
        *,
        branch: str | None = None,
        issue_start: str | None = None,
        issue_end: str | None = None,
        entry_start: str | None = None,
        entry_end: str | None = None,
        supplier: str | None = None,
        invoice_document: str | None = None,
        freight_document: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        cfg = _settings()
        scope = self._prepare(
            user,
            cfg,
            branch=branch,
            issue_start=issue_start,
            issue_end=issue_end,
            entry_start=entry_start,
            entry_end=entry_end,
        )
        page_n = clamp_page(page, as_int((cfg.get("pagination") or {}).get("defaultPage"), 1))
        size_n = self._resolve_page_size(cfg, page_size)

        result, is_complete = self._analyse(
            cfg,
            scope,
            supplier=supplier,
            invoice_document=invoice_document,
            freight_document=freight_document,
            refresh=refresh,
        )
        ordered = self._sort_inconsistencies(result.inconsistencies)
        window, pagination = self._paginate(ordered, page_n, size_n, is_complete)
        reasons = cfg.get("inconsistencyReasons") or {}

        return {
            "branch": scope["branch"],
            "pagination": pagination,
            "totalsByReason": self._totals_by_reason(result.inconsistencies, reasons),
            "items": [self._map_inconsistency(item, reasons) for item in window],
        }

    # -------------------------------------------------------------- pipeline

    def _prepare(
        self,
        user: object | None,
        cfg: dict[str, Any],
        *,
        branch: str | None,
        issue_start: str | None,
        issue_end: str | None,
        entry_start: str | None,
        entry_end: str | None,
    ) -> dict[str, Any]:
        self._branch_access.assert_can_use(user, FIN_FREIGHT_VIEW)
        resolved_branch = self._branch_access.resolve_branch_scope(user, branch)

        issue = self._normalize_range(cfg, issue_start, issue_end)
        entry = self._normalize_range(cfg, entry_start, entry_end)
        if issue == (None, None) and entry == (None, None):
            raise InvalidPeriod(self._message(cfg, "periodRequired"))

        return {
            "branch": resolved_branch,
            "issue_start": issue[0],
            "issue_end": issue[1],
            "entry_start": entry[0],
            "entry_end": entry[1],
        }

    def _normalize_range(
        self,
        cfg: dict[str, Any],
        start: str | None,
        end: str | None,
    ) -> tuple[str | None, str | None]:
        start_text = as_str(start) or None
        end_text = as_str(end) or None
        if start_text is None and end_text is None:
            return None, None
        if start_text is None or end_text is None:
            raise InvalidPeriod("Informe início e fim do período juntos.")
        if start_text > end_text:
            raise InvalidPeriod(self._message(cfg, "invalidPeriod"))

        minimum = as_str(cfg.get("minimumIssueDate"))
        if minimum and start_text < minimum:
            template = self._message(cfg, "periodBeforeCutoff")
            raise InvalidPeriod(template.format(minimum=self._pt_date(minimum)))
        return start_text, end_text

    def _analyse(
        self,
        cfg: dict[str, Any],
        scope: dict[str, Any],
        *,
        supplier: str | None,
        invoice_document: str | None,
        freight_document: str | None,
        refresh: bool,
    ) -> tuple[FreightAllocationResult, bool]:
        payload = self._cached(
            cfg,
            "dashboard",
            {
                "branch": scope["branch"],
                "issue": (scope["issue_start"], scope["issue_end"]),
                "entry": (scope["entry_start"], scope["entry_end"]),
                "supplier": as_str(supplier) or None,
                "invoice": as_str(invoice_document) or None,
                "freight": as_str(freight_document) or None,
            },
            lambda: unwrap_data(
                self._gateway.fetch_purchase_freight_links(
                    branch=scope["branch"],
                    issue_start=scope["issue_start"],
                    issue_end=scope["issue_end"],
                    entry_start=scope["entry_start"],
                    entry_end=scope["entry_end"],
                    supplier=as_str(supplier) or None,
                    invoice_document=as_str(invoice_document) or None,
                    freight_document=as_str(freight_document) or None,
                    limit=as_int(cfg.get("linkFetchLimit"), 20000),
                )
            ),
            refresh=refresh,
        )
        links = [self._to_link(item) for item in payload.get("items") or []]
        result = self._allocation.allocate(
            links,
            branch_limits=self._branch_limits(cfg),
            special_freight_kinds=cfg.get("specialFreightKinds") or (),
            normal_freight_type=as_str(cfg.get("normalFreightType")) or "N",
            normal_freight_kind=as_str(cfg.get("normalFreightKind")) or "CTE",
        )
        pagination = payload.get("pagination")
        is_complete = bool(
            (pagination or {}).get("is_complete", True)
            if isinstance(pagination, dict)
            else True
        )
        return result, is_complete

    def _cached(
        self,
        cfg: dict[str, Any],
        kind: str,
        parts: dict[str, Any],
        loader,
        *,
        refresh: bool,
    ) -> dict[str, Any]:
        ttl = as_int((cfg.get("cacheTtlSeconds") or {}).get(kind), 0)
        key = f"freight:{kind}:{sorted(parts.items())}"
        return cached_fetch(key, ttl, loader, refresh=refresh)

    # ------------------------------------------------------------- tradução

    @staticmethod
    def _to_link(raw: Any) -> FreightLink:
        item = raw if isinstance(raw, dict) else {}
        return FreightLink(
            branch=as_str(item.get("branch")),
            in_filter=bool(item.get("in_filter")),
            invoice_found=bool(item.get("invoice_found")),
            invoice_document=as_str(item.get("invoice_document")),
            invoice_series=as_str(item.get("invoice_series")),
            supplier_code=as_str(item.get("supplier_code")),
            supplier_store=as_str(item.get("supplier_store")),
            supplier_name=as_str(item.get("supplier_name")),
            goods_value=FreightService._as_decimal(item.get("invoice_goods_value")),
            invoice_issue_date=as_str(item.get("invoice_issue_date")),
            invoice_entry_date=as_str(item.get("invoice_entry_date")),
            freight_found=bool(item.get("freight_found")),
            freight_document=as_str(item.get("freight_document")),
            freight_series=as_str(item.get("freight_series")),
            carrier_code=as_str(item.get("carrier_code")),
            carrier_store=as_str(item.get("carrier_store")),
            carrier_name=as_str(item.get("carrier_name")),
            freight_gross_value=FreightService._as_decimal(
                item.get("freight_gross_value")
            ),
            freight_issue_date=as_str(item.get("freight_issue_date")),
            freight_document_type=as_str(item.get("freight_document_type")),
            freight_document_kind=as_str(item.get("freight_document_kind")),
        )

    @staticmethod
    def _as_decimal(value: Any) -> Decimal | None:
        """``None`` preserva "documento não localizado" — nunca vira zero."""
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value)).quantize(_CENTS, rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _branch_limits(cfg: dict[str, Any]) -> dict[str, Decimal]:
        limits: dict[str, Decimal] = {}
        for code, raw in (cfg.get("branchLimits") or {}).items():
            try:
                limits[str(code)] = Decimal(str(raw))
            except (InvalidOperation, ValueError):
                continue
        return limits

    # -------------------------------------------------------------- filtros

    def _resolve_situation(self, cfg: dict[str, Any], situation: str | None) -> str:
        allowed = [str(item) for item in cfg.get("situations") or []]
        value = (as_str(situation) or _SITUATION_ALL).lower()
        if value not in allowed:
            raise InvalidFreightQuery(self._message(cfg, "invalidSituation"))
        return value

    def _resolve_sort(
        self,
        cfg: dict[str, Any],
        list_key: str,
        sort_by: str | None,
        sort_dir: str | None,
    ) -> tuple[str, str]:
        sort_cfg = (cfg.get("sort") or {}).get(list_key) or {}
        allowed = {str(item) for item in sort_cfg.get("allowed") or []}
        default_by = str(sort_cfg.get("default") or next(iter(sorted(allowed)), ""))
        field = (as_str(sort_by) or default_by) or default_by
        if field not in allowed:
            template = self._message(cfg, "invalidSortBy")
            raise InvalidFreightQuery(template.format(allowed=", ".join(sorted(allowed))))

        directions = {
            str(item) for item in (cfg.get("sort") or {}).get("allowedDirections") or []
        }
        direction = (as_str(sort_dir) or "desc").lower()
        if direction not in directions:
            raise InvalidFreightQuery(self._message(cfg, "invalidSortDir"))
        return field, direction

    @staticmethod
    def _resolve_page_size(cfg: dict[str, Any], page_size: int | None) -> int:
        pagination = cfg.get("pagination") or {}
        return clamp_page_size(
            page_size,
            default=as_int(pagination.get("defaultPageSize"), 25),
            maximum=as_int(pagination.get("maxPageSize"), 200),
        )

    @staticmethod
    def _filter_invoices(
        invoices: Sequence[FreightInvoice],
        situation: str,
    ) -> list[FreightInvoice]:
        if situation == _SITUATION_ALL:
            return list(invoices)
        return [invoice for invoice in invoices if invoice.situation == situation]

    @staticmethod
    def _sort_invoices(
        invoices: Sequence[FreightInvoice],
        field: str,
        direction: str,
    ) -> list[FreightInvoice]:
        keys = {
            "freight_percent": lambda item: item.freight_percent
            if item.freight_percent is not None
            else Decimal("-1"),
            "freight_total": lambda item: item.freight_total,
            "goods_value": lambda item: item.goods_value,
            "issue_date": lambda item: item.issue_date,
            "entry_date": lambda item: item.entry_date,
            "invoice_document": lambda item: item.invoice_document,
            "supplier_name": lambda item: item.supplier_name,
        }
        key = keys.get(field, keys["freight_percent"])
        ordered = sorted(
            invoices,
            key=lambda item: (key(item), item.invoice_document, item.invoice_series),
            reverse=direction == "desc",
        )
        return ordered

    @staticmethod
    def _sort_inconsistencies(
        items: Sequence[FreightInconsistency],
    ) -> list[FreightInconsistency]:
        return sorted(
            items,
            key=lambda item: (
                item.reason_code,
                item.branch,
                item.freight_document,
                item.invoice_document,
            ),
        )

    @staticmethod
    def _paginate(
        items: Sequence[Any],
        page: int,
        page_size: int,
        source_is_complete: bool,
    ) -> tuple[list[Any], dict[str, Any]]:
        total_items = len(items)
        total_pages = max(1, -(-total_items // page_size))
        current = min(page, total_pages)
        start = (current - 1) * page_size
        window = list(items[start : start + page_size])
        return window, {
            "page": current,
            "pageSize": page_size,
            "totalItems": total_items,
            "totalPages": total_pages,
            "hasNext": current < total_pages,
            "hasPrevious": current > 1,
            "isComplete": source_is_complete,
        }

    # --------------------------------------------------------------- saídas

    def _summary(
        self,
        invoices: Sequence[FreightInvoice],
        cfg: dict[str, Any],
    ) -> dict[str, Any]:
        """Totais só das NFs consistentes — percentual com furo não é indicador."""
        valid = [
            invoice
            for invoice in invoices
            if invoice.situation != SITUATION_INCONSISTENT
        ]
        goods_total = sum((invoice.goods_value for invoice in valid), _ZERO)
        freight_total = sum((invoice.freight_total for invoice in valid), _ZERO)
        # Mesmo arredondamento do rateio: dois modos no módulo dariam totais
        # que não fecham com a soma das linhas da grade.
        percent = (
            ((freight_total / goods_total) * Decimal("100")).quantize(
                _CENTS, rounding=ROUND_HALF_UP
            )
            if goods_total > _ZERO
            else None
        )
        return {
            "invoiceCount": len(valid),
            "goodsTotal": str(goods_total),
            "freightTotal": str(freight_total),
            "freightPercent": str(percent) if percent is not None else None,
            "aboveLimitCount": sum(
                1 for invoice in valid if invoice.situation == SITUATION_ABOVE_LIMIT
            ),
            "inconsistentCount": sum(
                1
                for invoice in invoices
                if invoice.situation == SITUATION_INCONSISTENT
            ),
        }

    @classmethod
    def _map_invoice(cls, invoice: FreightInvoice) -> dict[str, Any]:
        return {
            "branch": invoice.branch,
            "invoiceDocument": invoice.invoice_document,
            "invoiceSeries": invoice.invoice_series,
            "supplierCode": invoice.supplier_code,
            "supplierStore": invoice.supplier_store,
            "supplierName": invoice.supplier_name,
            "issueDate": invoice.issue_date,
            "entryDate": invoice.entry_date,
            "goodsValue": str(invoice.goods_value),
            "freightTotal": str(invoice.freight_total),
            "freightPercent": (
                str(invoice.freight_percent)
                if invoice.freight_percent is not None
                else None
            ),
            "freightLimit": (
                str(invoice.freight_limit) if invoice.freight_limit is not None else None
            ),
            "situation": invoice.situation,
            "reasonCodes": list(invoice.reason_codes),
            "freightDocumentCount": len(invoice.allocations),
            "allocations": [
                {
                    "freightDocument": item.freight_document,
                    "freightSeries": item.freight_series,
                    "carrierCode": item.carrier_code,
                    "carrierStore": item.carrier_store,
                    "carrierName": item.carrier_name,
                    "freightIssueDate": item.freight_issue_date,
                    "freightGrossValue": str(item.freight_gross_value),
                    "allocationBase": str(item.allocation_base),
                    "allocatedValue": str(item.allocated_value),
                    "linkedInvoiceCount": item.linked_invoice_count,
                }
                for item in invoice.allocations
            ],
        }

    @staticmethod
    def _map_inconsistency(
        item: FreightInconsistency,
        reasons: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "reasonCode": item.reason_code,
            "reason": str(reasons.get(item.reason_code) or item.reason_code),
            "branch": item.branch,
            "invoiceDocument": item.invoice_document,
            "invoiceSeries": item.invoice_series,
            "supplierCode": item.supplier_code,
            "supplierName": item.supplier_name,
            "freightDocument": item.freight_document,
            "freightSeries": item.freight_series,
            "carrierName": item.carrier_name,
            "goodsValue": str(item.goods_value) if item.goods_value is not None else None,
            "freightGrossValue": (
                str(item.freight_gross_value)
                if item.freight_gross_value is not None
                else None
            ),
        }

    @staticmethod
    def _totals_by_reason(
        items: Iterable[FreightInconsistency],
        reasons: dict[str, Any],
    ) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for item in items:
            counts[item.reason_code] = counts.get(item.reason_code, 0) + 1
        return [
            {
                "reasonCode": code,
                "reason": str(reasons.get(code) or code),
                "count": count,
            }
            for code, count in sorted(counts.items(), key=lambda pair: -pair[1])
        ]

    @staticmethod
    def _message(cfg: dict[str, Any], key: str) -> str:
        return str((cfg.get("messages") or {}).get(key) or key)

    @staticmethod
    def _pt_date(iso_date: str) -> str:
        try:
            return date.fromisoformat(iso_date[:10]).strftime("%d/%m/%Y")
        except ValueError:
            return iso_date
