from unittest.mock import MagicMock

from commercial_app.domain.ports.open_orders_metrics_port import CustomerOpenOrderMetric
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)
from commercial_app.application.use_cases.manage_seller_portfolio import (
    ManageSellerPortfolioUseCase,
    coverage_audit_to_dict,
    load_summary_to_dict,
)


def _portfolio(**kwargs) -> SellerPortfolio:
    members = kwargs.pop("members", (SellerPortfolioMember(user_id="u1", role="owner"),))
    return SellerPortfolio(
        id=kwargs.pop("id", "p1"),
        user_id=kwargs.pop("user_id", "u1"),
        display_name=kwargs.pop("display_name", "Carteira"),
        active=kwargs.pop("active", True),
        customers=kwargs.pop("customers", ()),
        members=members,
    )


def test_summarize_portfolio_load_uses_metrics_port() -> None:
    repository = MagicMock()
    repository.list_portfolios.return_value = [
        _portfolio(
            customers=(
                SellerCustomerAssignment("100", "01", "A"),
                SellerCustomerAssignment("200", "01", "B"),
            ),
        )
    ]
    metrics = MagicMock()
    metrics.list_customer_metrics.return_value = [
        CustomerOpenOrderMetric("100", "01", "A", 80.0, True),
        CustomerOpenOrderMetric("200", "01", "B", 20.0, False),
    ]
    use_case = ManageSellerPortfolioUseCase(
        repository,
        open_orders_metrics=metrics,
    )
    payload = load_summary_to_dict(use_case.summarize_portfolio_load())
    assert payload["totvs_metrics"]["available"] is True
    assert payload["portfolios"][0]["open_value"] == 100.0
    assert payload["portfolios"][0]["attention_count"] == 1


def test_summarize_portfolio_load_keeps_stub_on_metrics_failure() -> None:
    repository = MagicMock()
    repository.list_portfolios.return_value = [_portfolio()]
    metrics = MagicMock()
    metrics.list_customer_metrics.side_effect = RuntimeError("totvs down")
    use_case = ManageSellerPortfolioUseCase(
        repository,
        open_orders_metrics=metrics,
    )
    payload = load_summary_to_dict(use_case.summarize_portfolio_load())
    assert payload["totvs_metrics"]["available"] is False
    assert payload["totvs_metrics"]["reason"] == "open_orders_metrics_fetch_failed"
    assert payload["portfolios"][0]["open_value"] is None


def test_audit_customer_coverage_fills_gap_from_metrics() -> None:
    repository = MagicMock()
    repository.list_portfolios.return_value = [
        _portfolio(customers=(SellerCustomerAssignment("100", "01", "A"),)),
    ]
    metrics = MagicMock()
    metrics.list_customer_metrics.return_value = [
        CustomerOpenOrderMetric("100", "01", "A", 10.0, False),
        CustomerOpenOrderMetric("999", "01", "Gap", 500.0, True),
    ]
    use_case = ManageSellerPortfolioUseCase(
        repository,
        open_orders_metrics=metrics,
    )
    payload = coverage_audit_to_dict(use_case.audit_customer_coverage())
    assert payload["gap"]["available"] is True
    assert payload["gap"]["universe"] == "open_orders"
    assert payload["gap"]["uncovered_count"] == 1
    assert payload["gap"]["uncovered"][0]["customer_code"] == "999"
