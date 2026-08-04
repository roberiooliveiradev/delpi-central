from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from app.application.use_cases.pedidos_venda_abertos.list_customer_billing_series_use_case import (
    ListCustomerBillingSeriesRequest,
    ListCustomerBillingSeriesUseCase,
)
from app.domain.ports.pedidos_venda_abertos.customer_enrichment_repository_port import (
    CustomerBillingMonthRow,
)
from app.domain.services.pedidos_venda_abertos.billing_series_service import (
    fill_billing_monthly_series,
    month_key_from_protheus,
)


def test_month_key_from_protheus() -> None:
    assert month_key_from_protheus("202608") == "2026-08"
    assert month_key_from_protheus("2026-08-15") == "2026-08"
    assert month_key_from_protheus("") is None


def test_fill_billing_monthly_series_pads_zeros() -> None:
    points = fill_billing_monthly_series(
        billed_by_month={"2026-07": 1000.0},
        end=date(2026, 8, 4),
        months=3,
    )
    assert [p.month for p in points] == ["2026-06", "2026-07", "2026-08"]
    assert points[0].value == 0.0
    assert points[1].value == 1000.0
    assert points[1].label == "jul/26"
    assert points[1].date_start == "2026-07-01"
    assert points[1].date_end == "2026-07-31"


def test_list_customer_billing_series_aggregates_and_fills() -> None:
    repo = MagicMock()
    repo.fetch_billing_monthly_series.return_value = [
        CustomerBillingMonthRow("202607", 100.0),
        CustomerBillingMonthRow("2026-07", 50.0),
    ]
    use_case = ListCustomerBillingSeriesUseCase(repo)

    class _FixedDate(date):
        @classmethod
        def today(cls) -> date:  # type: ignore[override]
            return date(2026, 8, 4)

    with patch(
        "app.application.use_cases.pedidos_venda_abertos.list_customer_billing_series_use_case.date",
        _FixedDate,
    ):
        result = use_case.execute(
            ListCustomerBillingSeriesRequest(
                customers=[("100", "01"), ("100", "01"), ("", "01")],
                months=3,
            )
        )

    assert result.customer_count == 1
    assert result.months == 3
    assert [p.month for p in result.points] == ["2026-06", "2026-07", "2026-08"]
    assert result.points[1].value == 150.0
    call_kwargs = repo.fetch_billing_monthly_series.call_args.kwargs
    assert call_kwargs["customers"] == [("100", "01")]
    payload = result.to_dict()
    assert payload["points"][1]["value"] == 150.0


def test_list_customer_billing_series_empty_customers_still_returns_months() -> None:
    repo = MagicMock()
    use_case = ListCustomerBillingSeriesUseCase(repo)
    result = use_case.execute(ListCustomerBillingSeriesRequest(customers=[], months=12))
    assert result.customer_count == 0
    assert len(result.points) == 12
    assert all(p.value == 0.0 for p in result.points)
    repo.fetch_billing_monthly_series.assert_not_called()


def test_list_customer_billing_series_operation_id_in_router() -> None:
    router = open(
        "app/interface/http/routes/pedidos_venda_abertos/pedidos_venda_abertos_router.py",
        encoding="utf-8",
    ).read()
    assert "list_customer_billing_series" in router
    assert "/customers/billing-series" in router
