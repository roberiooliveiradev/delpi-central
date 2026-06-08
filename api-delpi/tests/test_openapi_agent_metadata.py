"""Smoke: operationId estável nas rotas usadas pelo chat."""

from app.main import app

EXPECTED_CHAT_OPERATION_IDS = {
    "get_product_detail",
    "get_product_summary",
    "get_product_parents",
    "get_product_suppliers",
    "get_product_customers",
    "get_product_inspection",
    "get_product_guide",
    "get_product_internal_movements",
    "get_product_pricing",
    "get_product_sales_billing",
    "search_products",
    "get_product_structure",
    "get_product_stock",
    "get_product_analyser",
    "get_lmps_dashboard_summary",
    "list_lmps_dashboard_items",
    "get_lmps_dashboard_charts",
    "list_transforma_mais_processes",
    "get_transforma_mais_summary",
    "list_lmps",
    "list_lmps_dashboard",
    "get_lmp_by_sale_number",
}


def _collect_operation_ids() -> set[str]:
    schema = app.openapi()
    found: set[str] = set()
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict) and operation.get("operationId"):
                found.add(operation["operationId"])
    return found


def test_chat_critical_routes_have_stable_operation_ids() -> None:
    found = _collect_operation_ids()
    missing = EXPECTED_CHAT_OPERATION_IDS - found
    assert not missing, f"operationIds ausentes no OpenAPI: {sorted(missing)}"
