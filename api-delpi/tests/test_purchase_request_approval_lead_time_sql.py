"""Regression contract: no fictitious approval history or duplicated group KPIs."""

import pytest

from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_approval_lead_time_sql import (
    build_lead_time_events_sql,
    build_lead_time_products_sql,
    build_lead_time_filter,
    build_lead_time_page_sql,
    build_lead_time_summary_sql,
    build_lead_time_pending_sql,
    build_lead_time_approvers_sql,
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
    assert "six_to_ten_days" in summary
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


def test_approver_rollup_uses_actual_actor_and_previous_stage_time():
    where, params = build_lead_time_filter(
        branches=["01"], date_from="2026-01-01", date_to="2026-11-12",
    )
    sql = build_lead_time_approvers_sql(where)
    assert "SAK010" in sql
    assert "SCR.CR_LIBAPRO" in sql
    assert "SCR.CR_STATUS) = '02'" in sql  # only separate pending count
    assert "FROM eligible E" in sql  # completed SCs only feed response mean
    assert "LAG(level_finished)" in sql
    assert "E.registered_at" in sql
    assert "E.approved_at >= T.started_at" in sql
    assert "ROW_NUMBER() OVER" in sql
    assert params == ["01", "20260101", "20261112"]


def test_pending_only_active_scr_status_no_queued_future_levels():
    sql = build_lead_time_pending_sql("SC1.C1_FILIAL IN (?)")
    assert "SCR.CR_STATUS) = '02'" in sql
    assert "SCR.CR_APROV" in sql
    assert "SAK010" in sql
    assert "AK.AK_NOME" in sql
    assert "H.rn <= 100" in sql
    assert "COUNT(*) OVER () AS pending_total" in sql
    assert "SCR.CR_STATUS) = '01'" not in sql


def test_batch_events_deduplicate_groups_without_n_plus_one():
    sql, params = build_lead_time_events_sql([("01", "171945"), ("02", "169847")])
    assert "SELECT DISTINCT" in sql
    assert "SCR010" in sql
    assert "CR_GRUPO" not in sql
    assert "CR_LIBAPRO" in sql and "CR_USERLIB" in sql
    assert "SAK010" in sql and "AK_NOME" in sql
    assert "CR_LIBAPRO" in sql  # recorded actor, not CR_APROV
    assert params == ["01", "171945", "02", "169847"]


def test_products_sql_is_batched_filtered_and_grouped_without_scr_fanout():
    sql, params = build_lead_time_products_sql([
        ("01", "178771"), ("01", "179909"), ("02", "169847")
    ])
    assert "SC1010 SC1" in sql
    assert "C1_PRODUTO" in sql and "C1_DESCRI" in sql
    assert "SC1.D_E_L_E_T_ = ''" in sql
    assert "COUNT(*) AS line_count" in sql
    assert "GROUP BY" in sql
    assert "SCR010" not in sql and "SAK010" not in sql
    assert "?" in sql and "178771" not in sql  # all keys are parameters
    assert params == ["01", "178771", "01", "179909", "02", "169847"]
    with pytest.raises(ValueError):
        build_lead_time_products_sql([])
    with pytest.raises(ValueError):
        build_lead_time_products_sql([("01", str(i)) for i in range(201)])


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
            "three_to_five_days": 0, "six_to_ten_days": 0, "over_10_days": 0, "multi_level": 1,
        }

    def execute_query(self, sql, params):
        if "COUNT(*) AS line_count" in sql and "C1_PRODUTO" in sql:
            assert params == ("01", "171945", "01", "179909")
            return [
                {"branch": "01", "request_number": "171945",
                 "product_code": "51000026",
                 "product_description": "SERVIÇOS PRESTADOS POR TERCEIROS",
                 "line_count": 1},
                {"branch": "01", "request_number": "179909",
                 "product_code": "41000019",
                 "product_description": "CURSOS E TREINAMENTO PESSOAL",
                 "line_count": 1},
            ]
        if "pending_heads AS" in sql:
            return [{
                "branch": "01", "request_number": "179909",
                "issue_date": "2026-11-09", "requester_name": "TEST",
                "unapproved_items": 1, "pending_total": 1,
                "level": "01", "approver_code": "000012",
                "approver_name": "JOSE CARLOS DE LIMA JUNIOR",
                "approver_user_code": "000100", "pending_since": "2026-11-09",
                "waiting_days": 3,
            }]
        if "approver_metrics AS" in sql:
            return [{
                "approver_code": "000005", "approver_name": "MAX ULIANO LEMOS",
                "approver_user_code": "000074", "approvals": 95,
                "avg_days": 3.14, "max_days": 116, "same_day": 47,
                "pending_count": 0,
            }]
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
             "approver_code": "000007", "approver_name": "LAERCIO AUGUSTO KOCH"},
            {"branch": "01", "request_number": "171945", "level": "01",
             "approved_at": "2026-02-20", "action_user_code": "000047",
             "approver_code": "000007", "approver_name": "LAERCIO AUGUSTO KOCH"},
            {"branch": "01", "request_number": "171945", "level": "03",
             "approved_at": "2026-02-23", "action_user_code": "000028",
             "approver_code": "000003", "approver_name": "DENNIS PICCOLI"},
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
    assert data["items"][0]["products"] == [{
        "product_code": "51000026",
        "product_description": "SERVIÇOS PRESTADOS POR TERCEIROS",
        "line_count": 1,
    }]
    assert data["pending_items"][0]["products"][0]["product_code"] == "41000019"
    assert len(data["items"][0]["events"]) == 2
    assert data["items"][0]["events"][0]["approver_name"] == "LAERCIO AUGUSTO KOCH"
    assert data["pending_total"] == 1
    assert data["summary"]["total_requests"] == 1  # pending excluded
    assert data["pending_items"][0]["pending_approvers"][0]["approver_name"] == "JOSE CARLOS DE LIMA JUNIOR"
    assert data["approver_stats"][0]["approver_name"] == "MAX ULIANO LEMOS"
    assert data["approver_stats"][0]["avg_days"] == 3.14
