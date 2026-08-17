"""AnalyticsCustomerCodesService — escopo commercial → CSV TOTVS."""

from __future__ import annotations

from commercial_app.application.services.analytics_customer_codes_service import (
    AnalyticsCustomerCodesService,
)
from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)


def test_unrestricted_without_filter_returns_none():
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    assert AnalyticsCustomerCodesService.codes_param(scope) is None


def test_membership_codes_csv_sorted_unique():
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset(
            {("002", "01"), ("001", "01"), ("001", "02"), ("", "01")}
        ),
    )
    assert AnalyticsCustomerCodesService.codes_param(scope) == "001,002"


def test_empty_portfolio_uses_sentinel():
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset(),
        empty_portfolio=True,
    )
    assert AnalyticsCustomerCodesService.codes_param(scope) == "__no_customers__"
