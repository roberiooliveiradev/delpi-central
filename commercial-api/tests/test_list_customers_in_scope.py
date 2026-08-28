"""Unit — ListCustomersInScopeService + use case."""

from __future__ import annotations

from unittest.mock import MagicMock

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.application.use_cases.list_customers_in_scope import (
    ListCustomersInScopeUseCase,
)
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)
from commercial_app.domain.ports.open_orders_metrics_port import CustomerOpenOrderMetric
from commercial_app.domain.services.list_customers_in_scope_service import (
    ListCustomersInScopeService,
)


def test_service_left_joins_metrics_and_zeros_missing() -> None:
    service = ListCustomersInScopeService()
    result = service.build(
        [
            SellerCustomerAssignment("100", "01", "Alpha"),
            SellerCustomerAssignment("200", "01", "Beta"),
            SellerCustomerAssignment("100", "01", "Alpha Dup"),
        ],
        [
            CustomerOpenOrderMetric(
                customer_code="100",
                customer_store="01",
                customer_name="Alpha TOTVS",
                open_value=1500.0,
                has_overdue=True,
            )
        ],
    )
    assert result.customer_count == 2
    by_code = {item.customer_code: item for item in result.items}
    assert by_code["100"].open_value == 1500.0
    assert by_code["100"].has_overdue is True
    assert by_code["100"].has_open_orders is True
    assert by_code["100"].customer_name == "Alpha"
    assert by_code["200"].open_value == 0.0
    assert by_code["200"].has_overdue is False
    assert by_code["200"].has_open_orders is False


def test_use_case_membership_without_open_orders_still_listed() -> None:
    repo = MagicMock()
    repo.list_portfolios.return_value = [
        SellerPortfolio(
            id="p1",
            user_id="u1",
            display_name="Sul",
            active=True,
            customers=(
                SellerCustomerAssignment("000204", "01", "AHT"),
                SellerCustomerAssignment("000100", "01", "Com aberto"),
            ),
        )
    ]
    metrics = MagicMock()
    metrics.list_customer_metrics.return_value = [
        CustomerOpenOrderMetric(
            customer_code="000100",
            customer_store="01",
            customer_name="Com aberto",
            open_value=99.0,
            has_overdue=False,
        )
    ]
    use_case = ListCustomersInScopeUseCase(
        repository=repo,
        open_orders_metrics=metrics,
    )
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("000204", "01"), ("000100", "01")}),
        portfolio_id="p1",
    )
    payload = use_case.execute(scope)
    codes = {item["customer_code"] for item in payload["items"]}
    assert codes == {"000204", "000100"}
    by_code = {item["customer_code"]: item for item in payload["items"]}
    assert by_code["000204"]["open_value"] == 0.0
    assert by_code["000204"]["has_open_orders"] is False
    assert by_code["000100"]["open_value"] == 99.0
    assert payload["summary"]["customer_count"] == 2
    metrics.list_customer_metrics.assert_called_once()
    called_keys = metrics.list_customer_metrics.call_args[0][0]
    assert ("000204", "01") in called_keys
    assert None not in (called_keys if isinstance(called_keys, list) else [])


def test_use_case_empty_portfolio() -> None:
    repo = MagicMock()
    metrics = MagicMock()
    use_case = ListCustomersInScopeUseCase(repository=repo, open_orders_metrics=metrics)
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset(),
        empty_portfolio=True,
        message="Sua carteira ainda não possui clientes vinculados.",
    )
    payload = use_case.execute(scope)
    assert payload["items"] == []
    assert payload["empty_portfolio"] is True
    assert "vinculados" in (payload["message"] or "")
    metrics.list_customer_metrics.assert_not_called()


def test_use_case_unrestricted_unions_all_portfolios() -> None:
    repo = MagicMock()
    repo.list_portfolios.return_value = [
        SellerPortfolio(
            id="p1",
            user_id="a",
            display_name="A",
            active=True,
            customers=(SellerCustomerAssignment("1", "01", "One"),),
        ),
        SellerPortfolio(
            id="p2",
            user_id="b",
            display_name="B",
            active=True,
            customers=(SellerCustomerAssignment("2", "01", "Two"),),
        ),
    ]
    metrics = MagicMock()
    metrics.list_customer_metrics.return_value = []
    use_case = ListCustomersInScopeUseCase(repository=repo, open_orders_metrics=metrics)
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    payload = use_case.execute(scope)
    codes = {item["customer_code"] for item in payload["items"]}
    assert codes == {"1", "2"}
