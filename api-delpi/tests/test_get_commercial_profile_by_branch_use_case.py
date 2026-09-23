"""Unit — GetCommercialProfileByBranchUseCase (composition + consistency)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.commercial.get_commercial_profile_by_branch_request import (
    GetCommercialProfileByBranchRequest,
)
from app.application.use_cases.commercial.get_commercial_profile_by_branch_use_case import (
    METRIC_CONVERSION,
    METRIC_NEW_BUSINESS,
    METRIC_ORDER,
    METRIC_OTD,
    METRIC_ROL_ATTAINMENT,
    GetCommercialProfileByBranchUseCase,
    profile_value_for_metric,
)


def _build_use_case(
    *,
    otd_pct=90.0,
    conversion_pct=25.0,
    new_business_pct=40.0,
    rol=150000.0,
    rol_target_pct=99.8,
    otd_by_branch: dict | None = None,
    conversion_by_branch: dict | None = None,
    new_business_by_branch: dict | None = None,
    rol_by_branch: dict | None = None,
    rol_target_by_branch: dict | None = None,
) -> GetCommercialProfileByBranchUseCase:
    otd_uc = MagicMock()
    conversion_uc = MagicMock()
    new_business_uc = MagicMock()
    rol_uc = MagicMock()
    goals = MagicMock()

    def _otd(request):
        branch = request.branch
        pct = (otd_by_branch or {}).get(branch, otd_pct)
        return {
            "branch": branch,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "sales_order_otd_pct": pct,
        }

    def _conversion(request):
        branch = request.branch
        pct = (conversion_by_branch or {}).get(branch, conversion_pct)
        return {
            "branch": branch,
            "sales_conversion_rate_pct": pct,
        }

    def _new_business(request):
        branch = request.branch
        pct = (new_business_by_branch or {}).get(branch, new_business_pct)
        return {
            "branch": branch,
            "new_business_rol_pct": pct,
        }

    def _rol(**kwargs):
        branch = kwargs["branch"]
        value = (rol_by_branch or {}).get(branch, rol)
        return {
            "branch": branch,
            "start_date": kwargs.get("start_date"),
            "end_date": kwargs.get("end_date"),
            "rol": value,
            "gross_revenue": value,
            "returns": 0.0,
            "discounts": 0.0,
        }

    def _attach(payload, **kwargs):
        branch = kwargs.get("branch")
        target = (rol_target_by_branch or {}).get(branch, rol_target_pct)
        if target is None:
            return dict(payload)
        return {**payload, "rol_target_pct": target, "comparable_goal": 1.0}

    otd_uc.execute.side_effect = _otd
    conversion_uc.execute.side_effect = _conversion
    new_business_uc.execute.side_effect = _new_business
    rol_uc.execute.side_effect = _rol
    goals.attach_goal_fields.side_effect = _attach

    return GetCommercialProfileByBranchUseCase(
        sales_order_otd_use_case=otd_uc,
        sales_conversion_rate_use_case=conversion_uc,
        new_business_rol_pct_use_case=new_business_uc,
        commercial_rol_summary_use_case=rol_uc,
        dashboard_goals_service=goals,
    )


def test_without_branch_returns_sc_and_es_with_four_metrics_each() -> None:
    use_case = _build_use_case(
        otd_by_branch={"01": 91.0, "02": 88.0},
        conversion_by_branch={"01": 25.0, "02": 30.0},
        new_business_by_branch={"01": 40.0, "02": 35.0},
        rol_target_by_branch={"01": 99.8, "02": 80.0},
    )
    result = use_case.execute(
        GetCommercialProfileByBranchRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
        )
    )
    items = result["items"]
    assert result["summary"]["branches_count"] == 2
    assert result["summary"]["items_count"] == 8
    branches = {row["branch"] for row in items}
    assert branches == {"01", "02"}
    assert {row["branch_label"] for row in items if row["branch"] == "01"} == {"SC"}
    assert {row["branch_label"] for row in items if row["branch"] == "02"} == {"ES"}
    for branch in ("01", "02"):
        metrics = [row["metric"] for row in items if row["branch"] == branch]
        assert metrics == list(METRIC_ORDER)


def test_ordering_is_deterministic_branch_then_metric() -> None:
    use_case = _build_use_case()
    items = use_case.execute(GetCommercialProfileByBranchRequest()).get("items") or []
    keys = [(row["branch"], row["metric"]) for row in items]
    assert keys == [
        ("01", METRIC_OTD),
        ("01", METRIC_CONVERSION),
        ("01", METRIC_NEW_BUSINESS),
        ("01", METRIC_ROL_ATTAINMENT),
        ("02", METRIC_OTD),
        ("02", METRIC_CONVERSION),
        ("02", METRIC_NEW_BUSINESS),
        ("02", METRIC_ROL_ATTAINMENT),
    ]


def test_optional_branch_filters_to_single_filial() -> None:
    use_case = _build_use_case()
    result = use_case.execute(GetCommercialProfileByBranchRequest(branch="02"))
    assert result["summary"]["branches_count"] == 1
    assert {row["branch"] for row in result["items"]} == {"02"}
    assert len(result["items"]) == 4


def test_null_when_source_metric_missing_not_zero() -> None:
    use_case = _build_use_case(
        otd_pct=None,
        conversion_pct=0.0,
        new_business_pct=None,
        rol_target_pct=None,
    )
    items = use_case.execute(GetCommercialProfileByBranchRequest(branch="01"))["items"]
    assert profile_value_for_metric(items, branch="01", metric=METRIC_OTD) is None
    assert profile_value_for_metric(items, branch="01", metric=METRIC_CONVERSION) == 0.0
    assert (
        profile_value_for_metric(items, branch="01", metric=METRIC_NEW_BUSINESS) is None
    )
    assert (
        profile_value_for_metric(items, branch="01", metric=METRIC_ROL_ATTAINMENT)
        is None
    )


def test_period_and_filters_propagated_to_source_use_cases() -> None:
    use_case = _build_use_case()
    use_case.execute(
        GetCommercialProfileByBranchRequest(
            branch="01",
            start_date="20260801",
            end_date="20260828",
            customer_segment="weg",
            customer_codes=["000001"],
        )
    )
    otd_req = use_case._otd.execute.call_args.args[0]
    assert otd_req.branch == "01"
    assert otd_req.start_date == "2026-08-01"
    assert otd_req.end_date == "2026-08-28"
    assert otd_req.customer_segment == "weg"
    assert otd_req.customer_codes == ["000001"]

    conversion_req = use_case._conversion.execute.call_args.args[0]
    assert conversion_req.customer_codes == ["000001"]

    new_business_req = use_case._new_business.execute.call_args.args[0]
    assert new_business_req.customer_segment == "weg"

    rol_kwargs = use_case._rol_summary.execute.call_args.kwargs
    assert rol_kwargs["branch"] == "01"
    assert rol_kwargs["start_date"] == "2026-08-01"
    assert rol_kwargs["customer_codes"] == ["000001"]

    goals_kwargs = use_case._goals.attach_goal_fields.call_args.kwargs
    assert goals_kwargs["branch"] == "01"
    assert goals_kwargs["recompute_target_pct_from"] == "rol"


def test_consistency_with_source_use_case_payloads() -> None:
    """Profile value_pct equals the canonical fields of the four source use cases."""
    otd_by_branch = {"01": 91.46, "02": 87.1}
    conversion_by_branch = {"01": 25.0, "02": 18.5}
    new_business_by_branch = {"01": 40.89, "02": 33.3}
    rol_target_by_branch = {"01": 99.8, "02": 72.4}

    use_case = _build_use_case(
        otd_by_branch=otd_by_branch,
        conversion_by_branch=conversion_by_branch,
        new_business_by_branch=new_business_by_branch,
        rol_target_by_branch=rol_target_by_branch,
    )
    profile = use_case.execute(
        GetCommercialProfileByBranchRequest(
            start_date="2026-08-01",
            end_date="2026-08-31",
        )
    )
    items = profile["items"]

    for branch in ("01", "02"):
        assert profile_value_for_metric(items, branch=branch, metric=METRIC_OTD) == (
            otd_by_branch[branch]
        )
        assert profile_value_for_metric(
            items, branch=branch, metric=METRIC_CONVERSION
        ) == conversion_by_branch[branch]
        assert profile_value_for_metric(
            items, branch=branch, metric=METRIC_NEW_BUSINESS
        ) == new_business_by_branch[branch]
        assert profile_value_for_metric(
            items, branch=branch, metric=METRIC_ROL_ATTAINMENT
        ) == rol_target_by_branch[branch]
