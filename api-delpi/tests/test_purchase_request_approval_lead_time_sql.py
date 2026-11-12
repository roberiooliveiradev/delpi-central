"""Regression contract: no fictitious approval history or duplicated group KPIs."""

import pytest

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_approval_lead_time_sql import (
    build_lead_time_events_sql,
    build_lead_time_filter,
    build_lead_time_page_sql,
    build_lead_time_summary_sql,
    normalize_lead_time_filters,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_approval_lead_time_repository import (
    PurchaseRequestApprovalLeadTimeRepository,
)


def test_sql_uses_scr_as_exclusive_approval_evidence_and_sc_header_grain():
    where, params = build_lead_time_filter(
        branches=["01", "02"],
        date_from="2026-01-01",
        date_to="2026-11-12",
    )
    summary = build_lead_time_summary_sql(where)
    page = build_lead_time_page_sql(where)
    assert params == ["01", "02", "20260101", "20261112"]
    assert "SC1010" in summary and "SCR010" in summary
    assert "SC7010" not in summary
    assert "purchase_request_approval_states" not in summary
    assert "SCR.CR_TIPO = 'SC'" in summary
    assert "SCR.CR_STATUS) = '03'" in summary
    assert "SC.unapproved_items = 0" in summary
    assert "AP.unproven_entries = 0" in summary
    assert "AP.final_approval_date >= SC.issue_date" in summary
    assert "COUNT(DISTINCT CASE" in summary
    assert "GROUP BY RTRIM(SC1.C1_FILIAL), RTRIM(SC1.C1_NUM)" in summary
    assert "DATEDIFF(day, SC.issue_date, AP.final_approval_date)" in page
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in page


def test_filters_fail_closed_and_cap_period():
    with pytest.raises(ValueError):
        normalize_lead_time_filters(branches=None, date_from=None, date_to=None)
    with pytest.raises(ValueError):
        normalize_lead_time_filters(branches=["all"], date_from=None, date_to=None)
    with pytest.raises(ValueError):
        normalize_lead_time_filters(branches=["01", "03"], date_from=None, date_to=None)
    with pytest.raises(ValueError):
        normalize_lead_time_filters(branches=["01"], date_from="2026-12-30", date_to="2026-01-01")
    with pytest.raises(ValueError):
        normalize_lead_time_filters(branches=["01"], date_from="2020-01-01", date_to="2026-01-01")
    with pytest.raises(ValueError):
        normalize_lead_time_filters(branches=["01"], date_from="2026-01-01", date_to="2026-01-02", request_number="1' OR 1=1")
    where, params = build_lead_time_filter(
        branches=["02"], date_from="2026-01-01",
        date_to="2026-01-31", request_number="171945",
    )
    assert "RTRIM(SC1.C1_NUM) = ?" in where
    assert params[-1] == "171945"


def test_batch_events_deduplicate_groups_without_n_plus_one():
    sql, params = build_lead_time_events_sql([("01", "171945"), ("02", "169847")])
    assert "SELECT DISTINCT" in sql
    assert "SCR010" in sql
    assert "CR_GRUPO" not in sql
    assert "CR_LIBAPRO" in sql and "CR_USERLIB" in sql
    assert params == ["01", "171945", "02", "169847"]


class FakeRepository(PurchaseRequestApprovalLeadTimeRepository):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def execute_one(self, sql, params):
        assert "FROM eligible" in sql
        return {
            "total_requests": 1, "avg_lead_days": 10,
            "same_day": 0, "one_to_two_days": 0,
            "three_to_five_days": 0, "over_10_days": 0, "multi_level": 1,
        }

    def execute_query(self, sql, params):
        if "OFFSET" in sql:
            assert params[-2:] == (0, 25)
            return [{
                "branch": "01", "request_number": "171945",
                "issue_date": "2026-02-13", "requester_name": "TEST",
                "requester_user_id": "x", "item_count": 1,
                "final_approval_date": "2026-02-23", "approval_levels": 3,
                "lead_days": 10,
            }]
        return [
            {"branch": "01", "request_number": "171945", "level": "01",
             "approved_at": "2026-02-20", "action_user_code": "000047",
             "approver_code": "000007"},
            {"branch": "01", "request_number": "171945", "level": "01",
             "approved_at": "2026-02-20", "action_user_code": "000047",
             "approver_code": "000007"},
            {"branch": "01", "request_number": "171945", "level": "03",
             "approved_at": "2026-02-23", "action_user_code": "000028",
             "approver_code": "000003"},
        ]


def test_repository_counts_sc_once_and_deduplicates_approver_events():
    data = FakeRepository().get_lead_time(
        branches=["01"], date_from="2026-02-01", date_to="2026-02-28",
    )
    assert data["source"] == "SCR010"
    assert data["scope"] == "confirmed_history_only"
    assert data["total"] == 1
    assert data["summary"]["avg_lead_days"] == 10
    assert data["items"][0]["lead_days"] == 10
    assert len(data["items"][0]["events"]) == 2
