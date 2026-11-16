"""GLPI #635 regressions: final SCR approval or issue date for released SC without SCR."""

import pytest

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_sc_pc_conversion_sql import (
    build_conversion_cohort, build_conversion_page_sql, build_conversion_summary_sql,
    build_conversion_batch_sql,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_sc_pc_conversion_repository import (
    PurchaseRequestScPcConversionRepository,
)


def test_cohort_uses_final_scr_release_not_sc_creation():
    cte, params, filters = build_conversion_cohort(
        branches=["01", "02"], date_from="2026-10-01", date_to="2026-10-31",
    )
    assert params == [
        "01", "02", "20261001", "20261031",
        "01", "02", "20261001", "20261031",
        "20261031", "20261001", "20261031",
        "20261001", "20261031",
    ]
    assert "WITH release_candidates AS" in cte
    assert "UNION" in cte
    assert "SC.C1_EMISSAO >= ? AND SC.C1_EMISSAO <= ?" in cte
    assert "SC.C1_APROV = 'L'" in cte
    assert "NOT EXISTS (" in cte
    assert "SR.CR_TIPO = 'SC'" in cte
    assert "LEFT JOIN approval_history AP" in cte
    assert "AP.branch IS NULL" in cte
    assert "'issue_without_approval'" in cte
    assert "'approval_release'" in cte
    assert "effective_start_date" in cte
    assert "H.issue_date BETWEEN" in cte
    assert "SCR.CR_DATALIB >= ? AND SCR.CR_DATALIB <= ?" in cte
    assert "SC1.C1_FILIAL = C.branch" in cte
    assert "C7.C7_FILIAL = E.branch" in cte
    assert "C7.C7_NUMSC = E.request_number" in cte
    assert "RTRIM(C7.C7_NUMSC) = E.request_number" not in cte
    batch = build_conversion_batch_sql(cte)
    assert batch.count("WITH release_candidates AS") == 1
    assert "SELECT * INTO #sc_pc_conversion FROM measured" in batch
    assert "FROM #sc_pc_conversion" in batch
    assert "DROP TABLE #sc_pc_conversion" in batch
    assert "SET NOCOUNT ON" in batch
    assert filters["date_from"] == "2026-10-01"
    assert "SCR010" in cte and "SC1010" in cte and "SC7010" in cte
    assert "RTRIM(SCR.CR_STATUS) = '03'" in cte
    assert "SCR.CR_LIBAPRO" in cte and "SCR.CR_USERLIB" in cte
    assert "AP.unproven_entries = 0" in cte
    assert "AP.branch IS NOT NULL" in cte
    assert "AP.final_approval_date BETWEEN" in cte
    assert "R.first_order_date < E.effective_start_date" in cte
    assert "DATEDIFF(day, A.effective_start_date, A.first_order_date)" in cte
    assert "DATEDIFF(day, A.issue_date" not in cte
    assert "SUM(CASE WHEN start_date_source = 'issue_without_approval'" in build_conversion_summary_sql(cte)
    assert "ORDER BY effective_start_date DESC" in build_conversion_page_sql(cte)
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
                    "with_approval": 3, "without_approval": 1,
                    "pending_requests": 1, "before_release": 1,
                    "invalid_order_dates": 1, "sum_conversion_days": 2,
                    "avg_days": 2, "same_day": 0,
                },
                {
                    "branch": "", "approved_requests": 4, "converted_requests": 1,
                    "with_approval": 3, "without_approval": 1,
                    "pending_requests": 1, "before_release": 1,
                    "invalid_order_dates": 1, "sum_conversion_days": 2,
                    "avg_days": 2, "same_day": 0,
                },
            ]
        raise AssertionError("Paginated requests must use one SQL batch")

    def execute_query_multiple(self, sql, params):
        assert "SELECT * INTO #sc_pc_conversion FROM measured" in sql
        assert "FROM #sc_pc_conversion" in sql
        assert sql.count("WITH release_candidates AS") == 1
        assert params[-2:] == (0, 25)
        return [
            {"data": self.execute_query(sql, params[:-2])},
            {"data": [
            {
                "branch": "01", "request_number": "171945",
                "final_approval_date": "2026-10-10",
                "effective_start_date": "2026-10-10",
                "start_date_source": "approval_release",
                "first_order_date": "2026-10-12",
                "first_order_number": "00012",
                "linked_order_count": 3, "conversion_status": "converted",
                "conversion_days": 2,
            },
            {
                "branch": "01", "request_number": "171946",
                "final_approval_date": "",
                "effective_start_date": "2026-10-10",
                "start_date_source": "issue_without_approval",
                "first_order_date": "", "linked_order_count": 0,
                "conversion_status": "pending",
                "conversion_days": "",
            },
            ]},
        ]


def test_repository_excludes_pending_and_pre_release_from_mean():
    data = FakeRepository().get_conversion(
        branches=["01"], date_from="2026-10-01", date_to="2026-10-31",
    )
    assert data["summary"]["approved_requests"] == 4
    assert data["summary"]["with_approval"] == 3
    assert data["summary"]["without_approval"] == 1
    assert data["summary"]["avg_days"] == 2
    assert data["branch_breakdown"].keys() == {"01"}
    assert data["summary"]["converted_requests"] == 1
    assert data["summary"]["pending_requests"] == 1
    assert data["summary"]["before_release"] == 1
    assert data["summary"]["avg_days"] == 2
    assert data["items"][0]["linked_order_count"] == 3
    assert data["items"][0]["conversion_days"] == 2
    assert data["items"][1]["conversion_days"] is None
    assert data["items"][1]["final_approval_date"] is None
    assert data["items"][1]["first_order_date"] is None
    assert data["items"][1]["start_date_source"] == "issue_without_approval"
    assert data["items"][1]["effective_start_date"] == "2026-10-10"
    assert data["total_pages"] == 1
    assert data["period_anchor"] == "effective_start_date"
    assert data["scope"] == "release_or_issue_without_approval_to_first_order"


def test_summary_only_does_not_query_page():
    data = FakeRepository().get_conversion(
        branches=["01"], date_from="2026-10-01", date_to="2026-10-31",
        summary_only=True,
    )
    assert data["items"] == []
    assert data["branch_breakdown"]["01"]["sum_conversion_days"] == 2
    assert data["total_pages"] == 0


def test_summary_no_valid_orders_keeps_null_average():
    from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_sc_pc_conversion_repository import _summary

    result = _summary({"approved_requests": 2, "converted_requests": 0,
                       "avg_days": "", "without_approval": 2})
    assert result["approved_requests"] == 2
    assert result["avg_days"] is None
    assert result["without_approval"] == 2


def test_cohort_sc_number_filter_keeps_binding_order():
    cte, params, _ = build_conversion_cohort(
        branches=["01"], date_from="2026-11-01", date_to="2026-11-16",
        request_number="001234",
    )
    assert "SC1.C1_NUM = ?" in cte
    assert params == [
        "01", "20261101", "20261116",
        "01", "20261101", "20261116",
        "20261116", "001234",
        "20261101", "20261116", "20261101", "20261116",
    ]
