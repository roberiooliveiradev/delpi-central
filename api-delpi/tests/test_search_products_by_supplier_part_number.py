from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.infrastructure.persistence.totvs.product_repositories.product_suppliers_repository import (
    ProductSuppliersRepository,
)
from app.application.use_cases.product.search_products_by_supplier_part_number_use_case import (
    SearchProductsBySupplierPartNumberUseCase,
)
from app.application.dto.product.search_products_by_supplier_part_number_request import (
    SearchProductsBySupplierPartNumberRequest,
)
from app.domain.entities.product.supplier import Supplier
from app.application.models.page import Page
from app.interface.http.route_contract_registry import ROUTE_CONTRACTS
from app.interface.http.openapi_agent_metadata import PRODUCT_BY_SUPPLIER_PART_NUMBER
from app.interface.http.routes.product_routes import (
    search_products_by_supplier_part_number_route,
)


def _sample_supplier() -> Supplier:
    return Supplier(
        product_code="10080160",
        product_description="ITEM TESTE",
        unit="PC",
        supplier_code="000192",
        supplier_store="01",
        supplier_name="MOLEX BRASIL LTDA.",
        supplier_part_number="008700056",
        catalog_code=None,
        barcode=None,
        registered_lead_time_days=None,
        real_avg_lead_time_days=None,
        real_min_lead_time_days=None,
        real_max_lead_time_days=None,
        real_lead_time_sample_size=None,
        last_price=None,
        last_price_date=None,
    )


def _repo_with_mocks() -> ProductSuppliersRepository:
    repo = ProductSuppliersRepository()
    repo.execute_one = MagicMock(return_value={"total": 0})
    repo.execute_query = MagicMock(return_value=[])
    return repo


def test_search_by_supplier_part_number_sql_uses_a5_codprf() -> None:
    repo = _repo_with_mocks()

    with patch.object(ProductSuppliersRepository, "__enter__", return_value=repo), patch.object(
        ProductSuppliersRepository, "__exit__", return_value=False
    ):
        repo.search_by_supplier_part_number("008700056", page=1, page_size=10)

    count_sql = repo.execute_one.call_args[0][0]
    data_sql = repo.execute_query.call_args[0][0]
    count_params = repo.execute_one.call_args[0][1]
    data_params = repo.execute_query.call_args[0][1]

    assert "A5_CODPRF" in count_sql
    assert "A5_CODPRF" in data_sql
    assert "SA5010" in count_sql
    assert "008700056" in count_params
    assert "008700056" in data_params


def test_search_by_supplier_part_number_optional_supplier_code_filter() -> None:
    repo = _repo_with_mocks()

    with patch.object(ProductSuppliersRepository, "__enter__", return_value=repo), patch.object(
        ProductSuppliersRepository, "__exit__", return_value=False
    ):
        repo.search_by_supplier_part_number(
            "008700056",
            supplier_code="000192",
            page=1,
            page_size=10,
        )

    count_sql = repo.execute_one.call_args[0][0]
    count_params = repo.execute_one.call_args[0][1]

    assert "A5_FORNECE" in count_sql
    assert "000192" in count_params


def test_search_by_supplier_part_number_empty_returns_empty_page() -> None:
    repo = ProductSuppliersRepository()
    page = repo.search_by_supplier_part_number("   ", page=1, page_size=10)

    assert page.total == 0
    assert page.items == []


def test_use_case_delegates_to_repository() -> None:
    repository = MagicMock()
    repository.search_by_supplier_part_number.return_value = Page(
        items=[_sample_supplier()],
        total=1,
        page=1,
        page_size=50,
    )
    use_case = SearchProductsBySupplierPartNumberUseCase(repository)
    result = use_case.execute(
        SearchProductsBySupplierPartNumberRequest(
            supplier_part_number="008700056",
            page=1,
            page_size=50,
        )
    )

    repository.search_by_supplier_part_number.assert_called_once_with(
        "008700056",
        supplier_code=None,
        page=1,
        page_size=50,
    )
    assert result.total == 1
    assert result.items[0].product_code == "10080160"


def test_route_contract_and_agent_metadata_registered() -> None:
    oid = "search_products_by_supplier_part_number"
    assert oid in ROUTE_CONTRACTS
    assert ROUTE_CONTRACTS[oid].entity == "product_by_supplier_part_number"
    assert ROUTE_CONTRACTS[oid].shape == "paged_list"
    assert PRODUCT_BY_SUPPLIER_PART_NUMBER["operation_id"] == oid


def test_product_router_exposes_by_supplier_part_number_path() -> None:
    from app.interface.http.routes.product_routes import router

    paths = {getattr(route, "path", "") for route in router.routes}
    assert "/by-supplier-part-number" in paths


@patch(
    "app.interface.http.routes.product_routes.build_search_products_by_supplier_part_number_use_case"
)
def test_route_returns_meta_operation_id_entity_shape(mock_build_use_case) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = Page(
        items=[_sample_supplier()],
        total=1,
        page=1,
        page_size=50,
    )
    mock_build_use_case.return_value = mock_use_case

    response = search_products_by_supplier_part_number_route(
        supplier_part_number="008700056",
        supplier_code=None,
        page=1,
        page_size=50,
    )
    body = json.loads(response.body.decode())

    assert body["success"] is True
    assert body["meta"]["operationId"] == "search_products_by_supplier_part_number"
    assert body["meta"]["entity"] == "product_by_supplier_part_number"
    assert body["meta"]["shape"] == "paged_list"
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["product_code"] == "10080160"
    assert body["data"]["items"][0]["supplier_part_number"] == "008700056"

    request = mock_use_case.execute.call_args[0][0]
    assert request.supplier_part_number == "008700056"
    assert request.supplier_code is None


@patch(
    "app.interface.http.routes.product_routes.build_search_products_by_supplier_part_number_use_case"
)
def test_route_passes_optional_supplier_code(mock_build_use_case) -> None:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = Page(
        items=[],
        total=0,
        page=1,
        page_size=50,
    )
    mock_build_use_case.return_value = mock_use_case

    response = search_products_by_supplier_part_number_route(
        supplier_part_number="008700056",
        supplier_code="000192",
        page=1,
        page_size=50,
    )
    body = json.loads(response.body.decode())

    assert body["meta"]["operationId"] == "search_products_by_supplier_part_number"
    assert body["data"]["total"] == 0
    request = mock_use_case.execute.call_args[0][0]
    assert request.supplier_code == "000192"
