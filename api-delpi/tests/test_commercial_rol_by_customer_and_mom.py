"""Unit — ranking ROL por cliente e comparativo MoM."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.commercial.get_rol_by_customer_request import (
    GetRolByCustomerRequest,
)
from app.application.use_cases.commercial.get_commercial_rol_by_customer_use_case import (
    GetCommercialRolByCustomerUseCase,
)
from app.domain.entities.commercial.rol_by_customer import (
    RolByCustomerItem,
    RolByCustomerResult,
)
from app.domain.services.commercial.commercial_rol_mom_comparison_service import (
    CommercialRolMomComparisonService,
    pct_change_allow_new,
)
from app.domain.services.reports.report_previous_calendar_month_service import (
    ReportPreviousCalendarMonthService,
)


def test_get_rol_by_customer_request_validate() -> None:
    req = GetRolByCustomerRequest(
        start_date="2026-06-01",
        end_date="2026-06-30",
        limit=20,
    )
    req.validate()


def test_get_rol_by_customer_request_rejects_bad_limit() -> None:
    req = GetRolByCustomerRequest(
        start_date="2026-06-01",
        end_date="2026-06-30",
        limit=0,
    )
    try:
        req.validate()
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "limit" in str(exc)


def test_get_commercial_rol_by_customer_use_case() -> None:
    repo = MagicMock()
    repo.get_rol_by_customer.return_value = RolByCustomerResult(
        branch="consolidated",
        start_date="2026-06-01",
        end_date="2026-06-30",
        items=(
            RolByCustomerItem(
                customer_code="000001",
                customer_store="01",
                customer_name="WEG",
                rol=1000.0,
                share_pct=100.0,
                rank=1,
            ),
        ),
        others=None,
        total_rol=1000.0,
        customers_count=1,
    )
    result = GetCommercialRolByCustomerUseCase(repo).execute(
        GetRolByCustomerRequest(
            start_date="2026-06-01",
            end_date="2026-06-30",
            limit=10,
        )
    )
    assert result.total_rol == 1000.0
    repo.get_rol_by_customer.assert_called_once()


def test_pct_change_allow_new() -> None:
    assert pct_change_allow_new(110.0, 100.0) == 10.0
    assert pct_change_allow_new(90.0, 100.0) == -10.0
    assert pct_change_allow_new(50.0, 0.0) is None


def test_mom_comparison_merges_customers() -> None:
    financial = MagicMock()

    def _get_rol(request):
        start = str(request.start_date)
        month = int(start[5:7])
        year = int(start[:4])
        if request.branch is None:
            if year == 2026 and month == 6:
                return {"rol": 300.0}
            if year == 2026 and month == 5:
                return {"rol": 200.0}
            if year == 2026 and 1 <= month <= 4:
                return {"rol": float(month) * 50.0}
            return {"rol": 0.0}
        table = {
            "01": {"2026-06": 200.0, "2026-05": 150.0},
            "02": {"2026-06": 100.0, "2026-05": 50.0},
        }
        period = "2026-06" if month == 6 else "2026-05"
        return {"rol": table[request.branch][period]}

    financial.get_rol.side_effect = _get_rol

    by_customer = MagicMock()

    def _by_customer(request: GetRolByCustomerRequest) -> RolByCustomerResult:
        if str(request.start_date).startswith("2026-06"):
            return RolByCustomerResult(
                branch="consolidated",
                start_date=request.start_date or "",
                end_date=request.end_date or "",
                items=(
                    RolByCustomerItem(
                        customer_code="A",
                        customer_store="01",
                        customer_name="Cliente A",
                        rol=80.0,
                        share_pct=80.0,
                        rank=1,
                    ),
                ),
                others=RolByCustomerItem(
                    customer_code="",
                    customer_store="",
                    customer_name="Demais",
                    rol=20.0,
                    share_pct=20.0,
                    rank=2,
                ),
                total_rol=100.0,
                customers_count=3,
            )
        return RolByCustomerResult(
            branch="consolidated",
            start_date=request.start_date or "",
            end_date=request.end_date or "",
            items=(
                RolByCustomerItem(
                    customer_code="A",
                    customer_store="01",
                    customer_name="Cliente A",
                    rol=50.0,
                    share_pct=50.0,
                    rank=1,
                ),
                RolByCustomerItem(
                    customer_code="B",
                    customer_store="01",
                    customer_name="Cliente B",
                    rol=50.0,
                    share_pct=50.0,
                    rank=2,
                ),
            ),
            others=None,
            total_rol=100.0,
            customers_count=2,
        )

    by_customer.get_rol_by_customer.side_effect = _by_customer

    from datetime import date

    periods = ReportPreviousCalendarMonthService.resolve(date(2026, 7, 1))
    payload = CommercialRolMomComparisonService(financial, by_customer).build(
        periods,
        customer_limit=1,
    )
    assert payload["report_period"]["label_pt"] == "jun/2026"
    assert payload["branches"][0]["current"] == 300.0
    assert payload["branches"][0]["pct_change"] == 50.0
    assert payload["customers"][0]["customer_code"] == "A"
    assert payload["customers"][0]["pct_change"] == 60.0
    assert payload["customers"][-1]["is_others"] is True
    assert payload["customers"][-1]["previous"] == 50.0
    assert len(payload["year_evolution"]) == 6
    assert payload["year_evolution"][0]["label"] == "Jan/26"
    assert payload["year_evolution"][-1]["value"] == 300.0
