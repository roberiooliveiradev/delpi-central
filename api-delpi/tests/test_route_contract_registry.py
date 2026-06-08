import json
from unittest.mock import MagicMock, patch

from app.interface.http.route_contract_registry import ROUTE_CONTRACTS, resolve_contract
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.financial.financial_routes import get_rol


def test_route_contracts_cover_chat_critical_products() -> None:
    required = {
        "search_products",
        "get_product_detail",
        "get_product_stock",
        "get_supplies_cpv",
        "list_lmps",
        "get_financial_rol",
        "list_sale_orders",
        "execute_readonly_sql",
    }
    assert required.issubset(ROUTE_CONTRACTS.keys())


def test_resolve_contract_uses_registry_defaults() -> None:
    entity, shape = resolve_contract("get_financial_rol")
    assert entity == "financial_rol"
    assert shape == "scalar"


def test_api_delpi_success_includes_meta() -> None:
    response = api_delpi_success(
        {"value": 1},
        operation_id="get_financial_rol",
        message="ok",
    )
    body = json.loads(response.body.decode())
    assert body["meta"]["operationId"] == "get_financial_rol"
    assert body["meta"]["entity"] == "financial_rol"
    assert body["meta"]["shape"] == "scalar"
    assert body["meta"]["dataVersion"] == "2026-06"


@patch("app.interface.http.routes.financial.financial_routes.build_get_rol_use_case")
def test_financial_rol_route_returns_meta(mock_build) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = {
        "gross_revenue": 100.0,
        "rol": 80.0,
    }
    mock_build.return_value = mock_use_case

    response = get_rol()
    body = json.loads(response.body.decode())
    assert body["meta"]["operationId"] == "get_financial_rol"
    fields = body["meta"].get("fields") or {}
    assert fields.get("gross_revenue") == "Receita bruta"
    assert fields.get("rol") == "ROL"
