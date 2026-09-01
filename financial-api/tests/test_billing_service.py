from __future__ import annotations

from financial_app.application.services.billing_service import BillingService, InvalidBillingQuery
from tests.conftest import full_user, user
from tests.fakes import FakeFinancialGateway


def build(failing: set[str] | None = None) -> tuple[BillingService, FakeFinancialGateway]:
    gateway = FakeFinancialGateway(failing=failing)
    return BillingService(gateway), gateway


def test_dashboard_aggregates_summary_series_customers_and_branches() -> None:
    service, gateway = build()
    result = service.dashboard(full_user(), branch="01", granularity="month")

    assert result["branch"] == "01"
    assert result["granularity"] == "month"
    summary = result["summary"]
    assert summary["rol"] == 5_000_000.0
    assert summary["grossRevenue"] == 6_200_000.0
    assert summary["target"] == 5_500_000.0
    assert summary["gap"] == -500_000.0
    assert summary["composition"][0]["key"] == "grossRevenue"
    assert summary["composition"][-1]["role"] == "result"
    assert result["series"]["available"] is True
    assert result["series"]["items"][0]["rol01"] == 3_200_000.0
    assert result["customers"]["items"][0]["customerCode"] == "000001"
    assert result["branches"]["items"] == [
        {
            "branch": "01",
            "rol": 3_200_000.0,
            "grossRevenue": 3_900_000.0,
            "returns": 110_000.0,
            "discounts": 50_000.0,
        }
    ]
    assert gateway.call_kwargs("fetch_rol")["branch"] == "01"


def test_consolidated_keeps_both_units() -> None:
    service, _ = build()
    result = service.dashboard(full_user(), branch="all")
    assert result["branch"] is None
    assert [item["branch"] for item in result["branches"]["items"]] == ["01", "02"]


def test_failing_series_does_not_break_the_screen() -> None:
    service, _ = build(failing={"fetch_rol_series"})
    result = service.dashboard(full_user(), branch="01")
    assert result["summary"]["rol"] == 5_000_000.0
    assert result["series"]["available"] is False
    assert result["series"]["error"]
    assert result["customers"]["available"] is True


def test_invalid_granularity_is_rejected() -> None:
    service, _ = build()
    try:
        service.dashboard(full_user(), branch="01", granularity="quarter")
    except InvalidBillingQuery as exc:
        assert "Granularidade" in str(exc)
    else:
        raise AssertionError("esperava InvalidBillingQuery")


def test_single_branch_user_can_open_billing() -> None:
    service, _ = build()
    scoped = user(
        "financial.access",
        "financial.view.filial-01",
    )
    result = service.dashboard(scoped, branch="01")
    assert result["summary"]["rol"] == 5_000_000.0
    assert result["series"]["available"] is True
