"""GLPI #635 regressions: the clock begins only after the final SCR approval."""

import pytest

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_sc_pc_conversion_sql import (
    build_conversion_cohort, build_conversion_page_sql, build_conversion_summary_sql,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_sc_pc_conversion_repository import (
    PurchaseRequestScPcConversionRepository,
)


def test_cohort_uses_final_scr_release_not_sc_creation():
    cte, params, filters = build_conversion_cohort(
        branches=["01", "02"], date_from="2026-10-01", date_to="2026-10-31",
    )
    assert params == ["01", "02", "20261031", "20261001", "20261031"]
    assert filters["date_from"] == "2026-10-01"
    assert "SCR010" in cte and "SC1010" in cte and "SC7010" in cte
    assert "RTRIM(SCR.CR_STATUS) = '03'" in cte
    assert "SCR.CR_LIBAPRO" in cte and "SCR.CR_USERLIB" in cte
    assert "AP.unproven_entries = 0" in cte
    assert "AP.final_approval_date BETWEEN" in cte
    assert "R.first_order_date < E.final_approval_date" in cte
    assert "DATEDIFF(day, A.final_approval_date, A.first_order_date)" in cte
    assert "DATEDIFF(day, A.issue_date" not in cte
    assert "C7.C7_NUMSC" in cte and "C7.C7_ITEMSC" in cte
    assert "EXISTS (" in cte and "C7.D_E_L_E_T_ = ''" in cte
    assert "GROUP BY ROLLUP(branch)" in build_conversion_summary_sql(cte)
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in build_conversion_page_sql(cte)
    assert "COUNT(DISTINCT order_number)" in cte


def test_cohort_filters_fail_closed():
    with pytest.raises(ValueError):
        build_conversion_cohort(branches=[], date_from=None, date_to=None)
    with pytest.raises(ValueError):
        build_conversion_cohort(branches=["03"], date_from=None, date_to=None)
    with pytest.raises(ValueError):
        build_conversion_cohort(
            branches=["01"], date_from="2026-12-01", date_to="2026-01-01",
        )
    with pytest.raises(ValueError):
        build_conversion_cohort(
            branches=["01"], date_from="2026-10-01", date_to="2026-10-31",
            request_number="1' OR 1=1",
        )


class FakeRepository(PurchaseRequestScPcConversionRepository):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute_query(self, sql, params):
        if "GROUP BY ROLLUP(branch)" in sql:
            return [
                {
                    "branch": "01", "approved_requests": 4, "converted_requests": 1,
                    "pending_requests": 1, "before_release": 1,
                    "invalid_order_dates": 1, "sum_conversion_days": 2,
                    "avg_days": 2, "same_day": 0,
                },
                {
                    "branch": None, "approved_requests": 4, "converted_requests": 1,
                    "pending_requests": 1, "before_release": 1,
                    "invalid_order_dates": 1, "sum_conversion_days": 2,
                    "avg_days": 2, "same_day": 0,
                },
            ]
        assert params[-2:] == (0, 25)
        return [
            {
                "branch": "01", "request_number": "171945",
                "final_approval_date": "2026-10-10",
                "first_order_date": "2026-10-12",
                "first_order_number": "00012",
                "linked_order_count": 3, "conversion_status": "converted",
                "conversion_days": 2,
            },
            {
                "branch": "01", "request_number": "171946",
                "final_approval_date": "2026-10-10",
                "first_order_date": None, "linked_order_count": 0,
                "conversion_status": "pending",
                "conversion_days": None,
            },
        ]


def test_repository_excludes_pending_and_pre_release_from_mean():
    data = FakeRepository().get_conversion(
        branches=["01"], date_from="2026-10-01", date_to="2026-10-31",
    )
    assert data["summary"]["approved_requests"] == 4
    assert data["summary"]["converted_requests"] == 1
    assert data["summary"]["pending_requests"] == 1
    assert data["summary"]["before_release"] == 1
    assert data["summary"]["avg_days"] == 2
    assert data["items"][0]["linked_order_count"] == 3
    assert data["items"][0]["conversion_days"] == 2
    assert data["items"][1]["conversion_days"] is None
    assert data["total_pages"] == 1
    assert data["period_anchor"] == "final_approval_date"


def test_summary_only_does_not_query_page():
    data = FakeRepository().get_conversion(
        branches=["01"], date_from="2026-10-01", date_to="2026-10-31",
        summary_only=True,
    )
    assert data["items"] == []
    assert data["branch_breakdown"]["01"]["sum_conversion_days"] == 2
    assert data["total_pages"] == 0
