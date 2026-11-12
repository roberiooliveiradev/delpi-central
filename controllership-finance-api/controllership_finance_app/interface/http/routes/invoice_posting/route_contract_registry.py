"""Route contract registry — somente operationIds LNF (dataVersion 2026-07)."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RouteContract:
    entity: str
    shape: str

LNF_ROUTE_CONTRACTS: dict[str, RouteContract] = {
    "search_lancamento_notas_fiscais_suppliers": RouteContract("invoice_posting_supplier", "paged_list"),
    "list_lancamento_notas_fiscais_received_invoices": RouteContract("received_invoice", "paged_list"),
    "get_lancamento_notas_fiscais_received_invoice_danfe": RouteContract("received_invoice_danfe", "scalar"),
    "get_lancamento_notas_fiscais_received_nfse_detail": RouteContract("received_nfse_detail", "scalar"),
    "get_lancamento_notas_fiscais_received_nfse_xml": RouteContract("received_nfse_xml", "scalar"),
    "get_lancamento_notas_fiscais_received_cte_dacte": RouteContract("received_cte_dacte", "scalar"),
    "get_lancamento_notas_fiscais_request_fiscal_attachment": RouteContract("invoice_posting_fiscal_attachment", "scalar"),
    "get_lancamento_notas_fiscais_request_danfe": RouteContract("invoice_posting_danfe", "scalar"),
    "create_lancamento_notas_fiscais_request": RouteContract("invoice_posting_request", "scalar"),
    "list_lancamento_notas_fiscais_requests": RouteContract("invoice_posting_request", "paged_list"),
    "list_lancamento_notas_fiscais_unmapped_products": RouteContract("invoice_posting_unmapped_product", "paged_list"),
    "get_lancamento_notas_fiscais_request": RouteContract("invoice_posting_request", "scalar"),
    "list_lancamento_notas_fiscais_open_purchase_orders": RouteContract("invoice_posting_purchase_order", "paged_list"),
    "list_lancamento_notas_fiscais_request_purchase_orders": RouteContract("invoice_posting_purchase_order", "paged_list"),
    "link_lancamento_notas_fiscais_request_purchase_order": RouteContract("invoice_posting_request", "scalar"),
    "update_lancamento_notas_fiscais_request": RouteContract("invoice_posting_request", "scalar"),
    "start_lancamento_notas_fiscais_request": RouteContract("invoice_posting_request", "scalar"),
    "block_lancamento_notas_fiscais_request": RouteContract("invoice_posting_request", "scalar"),
    "resume_lancamento_notas_fiscais_request": RouteContract("invoice_posting_request", "scalar"),
    "add_lancamento_notas_fiscais_comment": RouteContract("invoice_posting_comment", "scalar"),
    "cancel_lancamento_notas_fiscais_request": RouteContract("invoice_posting_request", "scalar"),
    "post_manual_lancamento_notas_fiscais_request": RouteContract("invoice_posting_request", "scalar"),
    "run_lancamento_notas_fiscais_reconciliation": RouteContract("invoice_posting_reconciliation_batch", "scalar"),
    "refresh_lancamento_notas_fiscais_reconciliation": RouteContract("invoice_posting_reconciliation_refresh", "scalar"),
}

def resolve_contract(operation_id: str, *, entity: str | None = None, shape: str | None = None) -> tuple[str, str]:
    c = LNF_ROUTE_CONTRACTS.get(operation_id)
    if c is None:
        return entity or "unknown", shape or "scalar"
    return entity or c.entity, shape or c.shape
