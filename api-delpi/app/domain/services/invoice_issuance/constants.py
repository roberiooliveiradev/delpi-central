"""Constantes de domínio — emissão de NF."""

from __future__ import annotations

PARTY_TYPES = frozenset({"customer", "supplier"})
INVOICE_TYPES = frozenset({"sale", "return", "sample", "repair_shipment", "other"})
STOCK_WRITE_OFF_INVOICE_TYPES = frozenset({"sale", "return"})
FREIGHT_MODES = frozenset({"cif", "fob"})
OPEN_STATUSES = frozenset({"pending", "in_progress", "returned"})
TERMINAL_STATUSES = frozenset({"issued", "cancelled"})
CHECKLIST_KEYS = (
    "recipient",
    "item_codes",
    "quantity_price",
    "stock_write_off",
    "invoice_type",
    "freight_mode",
    "weight_volumes",
)
VALID_BRANCHES = frozenset({"01", "02"})


def default_stock_write_off(invoice_type: str | None) -> bool:
    """Venda e devolução saem de estoque; demais tipos nascem sem baixa."""
    return str(invoice_type or "").strip() in STOCK_WRITE_OFF_INVOICE_TYPES
