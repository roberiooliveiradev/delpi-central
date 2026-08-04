from __future__ import annotations

from unittest.mock import MagicMock

from app.application.models.page import Page
from app.application.use_cases.pedidos_venda_abertos.search_active_customers_use_case import (
    SearchActiveCustomersRequest,
    SearchActiveCustomersUseCase,
)
from app.domain.entities.customer.customer_master import CustomerMaster


def test_search_active_customers_delegates_and_clamps_page_size() -> None:
    repo = MagicMock()
    repo.search_active_customers.return_value = Page(
        items=[
            CustomerMaster(code="000001", store="01", name="Cliente A", blocked="2"),
        ],
        total=1,
        page=1,
        page_size=20,
    )
    use_case = SearchActiveCustomersUseCase(repo)

    result = use_case.execute(
        SearchActiveCustomersRequest(query="  cli  ", page=0, page_size=500)
    )

    repo.search_active_customers.assert_called_once_with(
        query="  cli  ",
        page=1,
        page_size=100,
    )
    assert result.total == 1
    assert result.items[0].code == "000001"


def test_search_active_customers_for_portfolio_operation_id_in_router() -> None:
    router = open(
        "app/interface/http/routes/pedidos_venda_abertos/pedidos_venda_abertos_router.py",
        encoding="utf-8",
    ).read()
    assert "search_active_customers_for_portfolio" in router
    assert "/customers/search" in router
