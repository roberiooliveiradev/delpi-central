"""Garante que todo operation_id dos routers está no registry de contratos."""

from app.interface.http.route_contract_registry import ROUTE_CONTRACTS
from tests.route_operation_ids import collect_operation_ids_from_routes


def test_all_route_operation_ids_are_registered() -> None:
    used = collect_operation_ids_from_routes()
    missing = sorted(used - set(ROUTE_CONTRACTS))
    assert not missing, f"operation_id sem entrada em ROUTE_CONTRACTS: {missing}"


def test_registry_covers_chat_critical_and_kpi_modules() -> None:
    required = {
        "search_products",
        "get_financial_rol",
        "get_supplies_cpv",
        "get_sales_conversion_rate",
        "get_kaizen_summary",
        "list_lmps",
        "list_hr_branches",
        "list_sale_orders",
        "execute_readonly_sql",
        "search_tables_by_description",
        "list_scheduling_resources",
    }
    assert required.issubset(ROUTE_CONTRACTS.keys())
