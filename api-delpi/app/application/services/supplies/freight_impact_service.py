"""Projeção de frete para Suprimentos usando a regra homologada do Financeiro.

O SQL e a base do rateio vêm da leitura financeira de vínculos de frete.
A rotina pura é um espelho exato (com contrato de paridade) do Financeiro.
NÃO usar D1_CUSTO / SD1: o Financeiro usa F1_VALMERC e F1_VALBRUT e fecha
o rateio com TODAS as NFs de cada CT-e, mesmo fora do período pesquisado.
"""
from __future__ import annotations

import json
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import delpi_freight
from delpi_freight.freight_allocation_service import (
    FreightAllocationService,
    FreightInvoice,
    FreightLink,
    SITUATION_ABOVE_LIMIT,
    SITUATION_INCONSISTENT,
)

_CENTS = Decimal("0.01")
_ZERO = Decimal("0")


def freight_settings() -> dict[str, Any]:
    """Metas e tipos espelhados da configuração oficial financial-api."""
    file = Path(delpi_freight.__file__).with_name("freight.json")
    return json.loads(file.read_text(encoding="utf-8"))


def _money(value: Decimal) -> str:
    return str(value.quantize(_CENTS, rounding=ROUND_HALF_UP))


def _percent(numerator: Decimal, denominator: Decimal) -> str | None:
    if denominator <= _ZERO:
        return None
    return _money((numerator / denominator) * Decimal("100"))


def _decimal(value: Any) -> Decimal | None:
    """Mesma conversão do FreightService financeiro (None não é zero)."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value)).quantize(_CENTS, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None


def _text(value: Any) -> str:
    return str(value or "").strip()


def to_financial_link(raw: dict[str, Any]) -> FreightLink:
    """Contrato de entrada equivalente a FinancialService._to_link."""
    item = raw if isinstance(raw, dict) else {}
    return FreightLink(
        branch=_text(item.get("branch")),
        in_filter=bool(item.get("in_filter")),
        invoice_found=bool(item.get("invoice_found")),
        invoice_document=_text(item.get("invoice_document")),
        invoice_series=_text(item.get("invoice_series")),
        supplier_code=_text(item.get("supplier_code")),
        supplier_store=_text(item.get("supplier_store")),
        supplier_name=_text(item.get("supplier_name")),
        goods_value=_decimal(item.get("invoice_goods_value")),
        invoice_issue_date=_text(item.get("invoice_issue_date")),
        invoice_entry_date=_text(item.get("invoice_entry_date")),
        freight_found=bool(item.get("freight_found")),
        freight_document=_text(item.get("freight_document")),
        freight_series=_text(item.get("freight_series")),
        carrier_code=_text(item.get("carrier_code")),
        carrier_store=_text(item.get("carrier_store")),
        carrier_name=_text(item.get("carrier_name")),
        freight_gross_value=_decimal(item.get("freight_gross_value")),
        freight_issue_date=_text(item.get("freight_issue_date")),
        freight_document_type=_text(item.get("freight_document_type")),
        freight_document_kind=_text(item.get("freight_document_kind")),
        freight_access_key=_text(item.get("freight_access_key")),
    )


def _invoice_data(invoice: FreightInvoice) -> dict[str, Any]:
    """Inclui o detalhe e o rateio de cada CT-e, como no Portal Financeiro."""
    return {
        "branch": invoice.branch,
        "invoice_document": invoice.invoice_document,
        "invoice_series": invoice.invoice_series,
        "supplier_code": invoice.supplier_code,
        "supplier_store": invoice.supplier_store,
        "supplier_name": invoice.supplier_name,
        "issue_date": invoice.issue_date,
        "entry_date": invoice.entry_date,
        "goods_value": _money(invoice.goods_value),
        "freight_total": _money(invoice.freight_total),
        "freight_pct": _money(invoice.freight_percent) if invoice.freight_percent is not None else None,
        "freight_limit": _money(invoice.freight_limit) if invoice.freight_limit is not None else None,
        "situation": invoice.situation,
        "reason_codes": list(invoice.reason_codes),
        "cte_count": len(invoice.allocations),
        "allocations": [
            {
                "freight_document": a.freight_document,
                "freight_series": a.freight_series,
                "carrier_code": a.carrier_code,
                "carrier_store": a.carrier_store,
                "carrier_name": a.carrier_name,
                "freight_issue_date": a.freight_issue_date,
                "freight_access_key": a.freight_access_key,
                "freight_gross_value": _money(a.freight_gross_value),
                "allocation_base": _money(a.allocation_base),
                "allocated_value": _money(a.allocated_value),
                "linked_invoice_count": a.linked_invoice_count,
            }
            for a in invoice.allocations
        ],
    }


def compose_freight_impact(
    raw_links: list[dict[str, Any]],
    *,
    branches: list[str],
    date_from: str,
    date_to: str,
    page: int = 1,
    page_size: int = 25,
    situation: str = "all",
    date_mode: str = "issue",
) -> dict[str, Any]:
    """Reaproveita rateio, arredondamento, inconsistências e metas do Financeiro.

    Os totais, como no Financeiro, usam apenas NFs consistentes com vínculo
    de frete. Filtrar por situação altera somente a grade, não os KPIs.
    """
    if situation not in {"all", "normal", "above_limit", "inconsistent"}:
        raise ValueError("Situação inválida.")
    if date_mode not in {"issue", "entry"}:
        raise ValueError("Tipo de período inválido.")
    if not branches or set(branches) - {"01", "02"}:
        raise ValueError("Filial inválida.")
    if not 1 <= page_size <= 100 or page < 1:
        raise ValueError("Paginação inválida.")

    cfg = freight_settings()
    limits = {str(code): Decimal(str(value)) for code, value in cfg["branchLimits"].items()}
    result = FreightAllocationService().allocate(
        [to_financial_link(row) for row in raw_links],
        branch_limits=limits,
        special_freight_kinds=cfg.get("specialFreightKinds") or (),
        normal_freight_type=cfg.get("normalFreightType") or "N",
        normal_freight_kind=cfg.get("normalFreightKind") or "CTE",
    )
    invoices = result.invoices
    valid = [nf for nf in invoices if nf.situation != SITUATION_INCONSISTENT]
    goods_total = sum((nf.goods_value for nf in valid), _ZERO)
    freight_total = sum((nf.freight_total for nf in valid), _ZERO)
    by_month: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"purchases": _ZERO, "freight": _ZERO, "invoices": 0}
    )
    for nf in valid:
        # Igual ao recorte mensal usado anteriormente: emissão da NF.
        period = nf.issue_date[:7]
        if len(period) != 7 or period[4] != "-":
            continue
        by_month[period]["purchases"] += nf.goods_value
        by_month[period]["freight"] += nf.freight_total
        by_month[period]["invoices"] += 1

    monthly = [
        {
            "period": month,
            "purchase_cost": _money(values["purchases"]),
            "freight_cost": _money(values["freight"]),
            "freight_pct": _percent(values["freight"], values["purchases"]),
            "invoices": values["invoices"],
        }
        for month, values in sorted(by_month.items())
    ]
    visible = (
        invoices if situation == "all"
        else [nf for nf in invoices if nf.situation == situation]
    )
    visible.sort(
        key=lambda nf: (
            nf.freight_percent if nf.freight_percent is not None else Decimal("-1"),
            nf.invoice_document,
            nf.invoice_series,
        ),
        reverse=True,
    )
    count = len(visible)
    total_pages = max(1, (count + page_size - 1) // page_size)
    current_page = min(page, total_pages)
    offset = (current_page - 1) * page_size

    return {
        "source": "financial_purchase_freight_links",
        "method": "financial_freight_allocation_v1",
        "scope": "purchase_invoices_with_freight_links",
        "filters": {
            "branches": branches,
            "date_from": date_from,
            "date_to": date_to,
            "date_mode": date_mode,
            "situation": situation,
        },
        "limits": {code: _money(value) for code, value in limits.items() if code in branches},
        "reason_labels": cfg.get("inconsistencyReasons", {}),
        "summary": {
            "invoice_count": len(valid),
            "linked_invoice_count": len(invoices),
            "inconsistent_count": len(invoices) - len(valid),
            "above_limit_count": sum(nf.situation == SITUATION_ABOVE_LIMIT for nf in valid),
            "purchases_total": _money(goods_total),
            "freight_total": _money(freight_total),
            "freight_pct": _percent(freight_total, goods_total),
        },
        "monthly": monthly,
        "items": [_invoice_data(nf) for nf in visible[offset:offset + page_size]],
        "total": count,
        "page": current_page,
        "page_size": page_size,
        "total_pages": total_pages,
        "is_complete": True,
    }
