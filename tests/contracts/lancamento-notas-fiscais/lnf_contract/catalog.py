"""Catálogo das 24 rotas e da matriz AuthZ derivada dos decorators e do branch gate.

A suíte não importa o código da api-delpi. Os conjuntos abaixo espelham
api_delpi_permissions.py, o router e lancamento_notas_fiscais_branch_access.py.
"""

from __future__ import annotations

from dataclasses import dataclass

FAKE_REQUEST_ID = "00000000-0000-4000-8000-000000000099"

# @require_permission(CREATE) — só create (não process/manage).
CREATE_STRICT = frozenset({"P5", "P11", "P12"})
# @require_any_permission(CREATE_PERMISSIONS) — create | process | manage.
CREATE_SET = frozenset({"P5", "P6", "P7", "P11", "P12"})
# @require_any_permission(PROCESS_PERMISSIONS)
PROCESS_SET = frozenset({"P6", "P7"})
# @require_permission(MANAGE)
MANAGE_ONLY = frozenset({"P7"})
# @require_permission(REVIEW_UNMAPPED_PRODUCTS)
REVIEW_ONLY = frozenset({"P8"})
# @require_any_permission(READ_PERMISSIONS) — access|create|view|filiais|process|manage
READ = frozenset({"P1", "P2", "P3", "P4", "P5", "P6", "P7", "P11", "P12"})
# Branch global: view | process | manage (não create nem access).
GLOBAL_BRANCH = frozenset({"P4", "P6", "P7"})
FILIAL = {"P2": "01", "P3": "02", "P11": "01", "P12": "02"}


@dataclass(frozen=True)
class Route:
    operation_id: str
    method: str
    path: str
    auth: str
    branch_mode: str
    entity: str
    shape: str
    binary: bool = False


ROUTES: tuple[Route, ...] = (
    Route("search_lancamento_notas_fiscais_suppliers", "GET", "/lancamento-notas-fiscais/suppliers", "create_strict", "none", "invoice_posting_supplier", "paged_list"),
    Route("list_lancamento_notas_fiscais_received_invoices", "GET", "/lancamento-notas-fiscais/received-invoices", "create_strict", "none", "received_invoice", "paged_list"),
    Route("get_lancamento_notas_fiscais_received_invoice_danfe", "GET", "/lancamento-notas-fiscais/received-invoices/contract-missing/danfe", "create_strict", "none", "received_invoice_danfe", "scalar", True),
    Route("get_lancamento_notas_fiscais_received_cte_dacte", "GET", "/lancamento-notas-fiscais/received-invoices/contract-missing/dacte", "create_strict", "none", "received_cte_dacte", "scalar", True),
    Route("get_lancamento_notas_fiscais_received_nfse_detail", "GET", "/lancamento-notas-fiscais/received-invoices/contract-missing/detail", "create_strict", "none", "received_nfse_detail", "scalar"),
    Route("get_lancamento_notas_fiscais_received_nfse_xml", "GET", "/lancamento-notas-fiscais/received-invoices/contract-missing/xml/nfe", "create_strict", "none", "received_nfse_xml", "scalar", True),
    Route("create_lancamento_notas_fiscais_request", "POST", "/lancamento-notas-fiscais/requests", "create_strict", "body", "invoice_posting_request", "scalar"),
    Route("list_lancamento_notas_fiscais_unmapped_products", "GET", "/lancamento-notas-fiscais/unmapped-products", "review_only", "none", "invoice_posting_unmapped_product", "paged_list"),
    Route("list_lancamento_notas_fiscais_requests", "GET", "/lancamento-notas-fiscais/requests", "read", "query_optional", "invoice_posting_request", "paged_list"),
    Route("get_lancamento_notas_fiscais_request", "GET", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}", "read", "loaded", "invoice_posting_request", "scalar"),
    Route("get_lancamento_notas_fiscais_request_danfe", "GET", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/danfe", "read", "loaded", "invoice_posting_danfe", "scalar", True),
    Route("get_lancamento_notas_fiscais_request_fiscal_attachment", "GET", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/fiscal-attachments/xml_original", "read", "loaded", "invoice_posting_fiscal_attachment", "scalar", True),
    Route("list_lancamento_notas_fiscais_open_purchase_orders", "GET", "/lancamento-notas-fiscais/purchase-orders/open", "create_strict", "query_required", "invoice_posting_purchase_order", "paged_list"),
    Route("list_lancamento_notas_fiscais_request_purchase_orders", "GET", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/purchase-orders", "read", "loaded", "invoice_posting_purchase_order", "paged_list"),
    Route("link_lancamento_notas_fiscais_request_purchase_order", "POST", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/purchase-orders/link", "process", "loaded", "invoice_posting_request", "scalar"),
    Route("update_lancamento_notas_fiscais_request", "PATCH", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}", "create_set", "loaded", "invoice_posting_request", "scalar"),
    Route("start_lancamento_notas_fiscais_request", "POST", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/start", "process", "loaded", "invoice_posting_request", "scalar"),
    Route("block_lancamento_notas_fiscais_request", "POST", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/block", "process", "loaded", "invoice_posting_request", "scalar"),
    Route("resume_lancamento_notas_fiscais_request", "POST", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/resume", "process", "loaded", "invoice_posting_request", "scalar"),
    Route("add_lancamento_notas_fiscais_comment", "POST", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/comments", "create_set", "loaded", "invoice_posting_comment", "scalar"),
    Route("cancel_lancamento_notas_fiscais_request", "POST", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/cancel", "create_set", "loaded", "invoice_posting_request", "scalar"),
    Route("post_manual_lancamento_notas_fiscais_request", "POST", f"/lancamento-notas-fiscais/requests/{FAKE_REQUEST_ID}/post-manual", "process", "loaded", "invoice_posting_request", "scalar"),
    Route("run_lancamento_notas_fiscais_reconciliation", "POST", "/lancamento-notas-fiscais/reconciliation/run", "manage", "none", "invoice_posting_reconciliation_batch", "scalar"),
    Route("refresh_lancamento_notas_fiscais_reconciliation", "POST", "/lancamento-notas-fiscais/reconciliation/refresh", "read", "none", "invoice_posting_reconciliation_refresh", "scalar"),
)

assert len(ROUTES) == 24

_AUTH_SETS = {
    "read": READ,
    "create_strict": CREATE_STRICT,
    "create_set": CREATE_SET,
    "process": PROCESS_SET,
    "manage": MANAGE_ONLY,
    "review_only": REVIEW_ONLY,
}

SIDE_EFFECT_SAMPLE = frozenset(
    {
        "run_lancamento_notas_fiscais_reconciliation",
    }
)


def decorator_allows(profile: str, route: Route, *, target: str) -> bool:
    if profile == "P9":
        return True
    if profile == "P10":
        return target != "bff"
    if profile == "P0":
        return False
    return profile in _AUTH_SETS[route.auth]


def has_global_branch(profile: str, *, target: str) -> bool:
    if profile == "P9":
        return True
    if profile == "P10":
        return target != "bff"
    return profile in GLOBAL_BRANCH


def branch_allowed(profile: str, branch: str, *, target: str) -> bool:
    if has_global_branch(profile, target=target):
        return True
    return FILIAL.get(profile) == branch


def auth_probe(route: Route, profile: str) -> tuple[str, dict | None, dict | None]:
    """Pedido válido para o Pydantic, sem gravar solicitação real.

    Create usa fornecedor inexistente: o use case rejeita antes do insert.
    Rotas com id falso devolvem not_found depois do decorator.
    """
    params: dict | None = None
    body: dict | None = None
    path = route.path
    if route.operation_id == "search_lancamento_notas_fiscais_suppliers":
        params = {"query": "aa", "limit": "5"}
    elif route.operation_id == "list_lancamento_notas_fiscais_received_invoices":
        params = {"invoice_number": "0", "page": "1", "page_size": "5"}
    elif route.operation_id == "list_lancamento_notas_fiscais_requests":
        if profile in FILIAL:
            params = {"branch": FILIAL[profile], "page": "1", "page_size": "5"}
        else:
            params = {"branch": "01", "page": "1", "page_size": "5"}
    elif route.operation_id == "list_lancamento_notas_fiscais_open_purchase_orders":
        branch = FILIAL.get(profile, "01")
        params = {"branch": branch, "supplier_code": "0", "supplier_store": "01"}
    elif route.operation_id == "create_lancamento_notas_fiscais_request":
        body = _safe_create_body(FILIAL.get(profile, "01"))
    elif route.operation_id == "link_lancamento_notas_fiscais_request_purchase_order":
        body = {"order_number": "000000"}
    elif route.operation_id == "update_lancamento_notas_fiscais_request":
        body = {"observation": "CONTRACT-TEST F2 auth-probe"}
    elif route.operation_id == "block_lancamento_notas_fiscais_request":
        body = {
            "block_reason": "other",
            "block_description": "CONTRACT-TEST F2",
            "assignee_user_id": "00000000-0000-4000-8000-0000000000aa",
            "assignee_name": "Contract Probe",
        }
    elif route.operation_id == "add_lancamento_notas_fiscais_comment":
        body = {"body": "CONTRACT-TEST F2", "mentioned_user_ids": []}
    elif route.operation_id == "cancel_lancamento_notas_fiscais_request":
        body = {"justification": "CONTRACT-TEST F2"}
    elif route.operation_id == "post_manual_lancamento_notas_fiscais_request":
        body = {"justification": "CONTRACT-TEST F2"}
    elif route.operation_id == "get_lancamento_notas_fiscais_request_danfe":
        params = {"disposition": "inline"}
    return path, params, body


def _safe_create_body(branch: str) -> dict:
    return {
        "branch": branch,
        "document": "999999",
        "series": "1",
        "fiscal_model": "nfe",
        "supplier_code": "CONTRACT-NO-SUCH",
        "supplier_store": "01",
        "issue_date": "2026-11-12",
        "amount": 1,
        "received_at": "2026-11-12T12:00:00",
        "observation": "CONTRACT-TEST F2 auth-probe",
    }
