"""Row → DTO normalization for settlement events.

Self-contained helpers: this context must not import use-case internals from
sibling financeiro contexts (isolated settlement-query context, doc 48 D1).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.dto.financeiro_settlements.settlements_response import (
    LINK_MISSING_BOTH,
    LINK_MISSING_DOCUMENT,
    LINK_MISSING_NATURE,
    LINK_RESOLVED,
    SettlementItem,
)


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _iso_date(value: Any) -> str:
    if value is None or value == "":
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    text = _as_str(value)
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    if len(text) == 8 and text.isdigit():
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text


def _decimal_str(value: Any) -> str:
    if value is None or value == "":
        return "0.00"
    try:
        return str(Decimal(str(value)).quantize(Decimal("0.01")))
    except (InvalidOperation, ValueError):
        return "0.00"


def _opt_str(value: Any) -> str | None:
    text = _as_str(value)
    return text if text else None


def _link_status(row: dict) -> str:
    missing_doc = bool(row.get("missing_document"))
    missing_nature = bool(row.get("missing_nature"))
    if missing_doc and missing_nature:
        return LINK_MISSING_BOTH
    if missing_doc:
        return LINK_MISSING_DOCUMENT
    if missing_nature:
        return LINK_MISSING_NATURE
    return LINK_RESOLVED


def normalize_settlement_item(row: dict) -> SettlementItem:
    source_branch = _as_str(row.get("source_branch"))
    return SettlementItem(
        settlementId=_as_str(row.get("settlement_id")),
        settlementDate=_iso_date(row.get("settlement_date")) or None,
        settlementAmount=_decimal_str(row.get("settlement_amount")),
        currencyCode=_opt_str(row.get("currency_code")),
        natureCode=_opt_str(row.get("nature_code")),
        natureDescription=_opt_str(row.get("nature_description")),
        documentNumber=_opt_str(row.get("document_number")),
        prefix=_opt_str(row.get("prefix")),
        installment=_opt_str(row.get("installment")),
        documentType=_opt_str(row.get("document_type")),
        partyCode=_opt_str(row.get("party_code")),
        partyStore=_opt_str(row.get("party_store")),
        partyName=_opt_str(row.get("party_name")),
        issueDate=_iso_date(row.get("issue_date")) or None,
        dueDate=_iso_date(row.get("due_date")) or None,
        history=_opt_str(row.get("history")),
        movementType=_opt_str(row.get("movement_type")),
        paymentDirection=_opt_str(row.get("payment_direction")),
        # D3.1: expose the raw code only when the source actually carries
        # one — empty *_FILIAL must not become a fabricated branch.
        branchCode=source_branch or None,
        branchResolution="unresolved",
        linkStatus=_link_status(row),
    )


def build_pagination(
    *, page: int, page_size: int, total_items: int
) -> dict[str, int | bool]:
    total_pages = (
        max((total_items + page_size - 1) // page_size, 1) if total_items else 1
    )
    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


def as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)
