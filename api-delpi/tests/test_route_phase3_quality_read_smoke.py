"""Smoke quality — PAC read/intelligence + Audit 5S leitura (onda inicial)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_PAC_READ = "app.interface.http.routes.quality.action_plans_read_router"
_PAC_INTEL = "app.interface.http.routes.quality.action_plans_intelligence_router"
_AUDIT = "app.interface.http.routes.quality.audit_5s_operational_router"


@patch(f"{_PAC_READ}.list_export_templates")
def test_list_export_templates_returns_meta(mock_list) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        list_rnc_8d_export_templates,
    )

    mock_list.return_value = [{"key": "default", "label": "8D"}]
    response = list_rnc_8d_export_templates()
    assert_envelope_meta(
        body_json(response),
        operation_id="list_quality_action_plan_export_templates",
    )


@patch(f"{_PAC_READ}.get_current_user", return_value=MagicMock(id="user-smoke"))
@patch(f"{_PAC_READ}.build_quality_action_plan_read_repository")
def test_list_my_queue_returns_meta(mock_repo, _user) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        list_my_action_queue,
    )

    mock_repo.return_value = MagicMock(
        list_my_queue=MagicMock(
            return_value={
                "items": [],
                "pagination": {
                    "page": 1,
                    "page_size": 50,
                    "total": 0,
                    "total_pages": 0,
                },
            }
        )
    )
    response = list_my_action_queue()
    assert_envelope_meta(
        body_json(response),
        operation_id="list_quality_action_plan_my_queue",
    )


@patch(f"{_PAC_READ}.build_quality_action_plan_read_repository")
def test_list_plan_audit_log_returns_meta(mock_repo) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        list_plan_audit_log,
    )

    repo = MagicMock()
    repo.get_plan_by_id.return_value = {"id": "plan-1"}
    repo.list_plan_audit_log.return_value = {
        "items": [{"event_type": "plan_created"}],
        "pagination": {"page": 1, "page_size": 50, "total": 1, "total_pages": 1},
    }
    mock_repo.return_value = repo
    response = list_plan_audit_log("plan-1")
    assert_envelope_meta(
        body_json(response),
        operation_id="list_quality_action_plan_audit_log",
    )


@patch(f"{_PAC_READ}.build_get_plan_similar_cases_use_case")
def test_get_plan_similar_cases_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        get_plan_similar_cases,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "similar_cases": [],
                "recurrence_signals": {},
                "similar_cases_decision_log": {"entries": []},
            }
        )
    )
    response = get_plan_similar_cases("plan-1")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_quality_action_plan_similar_cases",
    )


@patch(f"{_PAC_INTEL}.build_get_quality_knowledge_graph_use_case")
def test_knowledge_graph_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.action_plans_intelligence_router import (
        get_quality_knowledge_graph,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "nodes": [],
                "edges": [],
                "summary": {"node_count": 0},
                "filters": {},
            }
        )
    )
    response = get_quality_knowledge_graph()
    assert_envelope_meta(
        body_json(response),
        operation_id="get_quality_action_plan_knowledge_graph",
    )


@patch(f"{_PAC_INTEL}.build_assess_recurrence_on_opening_use_case")
def test_assess_recurrence_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.action_plans_intelligence_router import (
        RecurrenceOpeningAssessmentBody,
        assess_recurrence_on_opening,
    )

    mock_build.return_value = MagicMock(
        execute=MagicMock(
            return_value={
                "recurrence_score": 0.5,
                "alert_level": "medium",
                "should_warn_before_opening": False,
                "recurrence_key": "k",
            }
        )
    )
    response = assess_recurrence_on_opening(
        body=RecurrenceOpeningAssessmentBody(
            problem_description="oxidação em parafusos do produto"
        )
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="assess_quality_action_plan_recurrence_on_opening",
    )


@patch(f"{_PAC_READ}.CoreApiDirectoryService")
def test_list_assignable_users_returns_meta(mock_cls) -> None:
    from app.interface.http.routes.quality.action_plans_read_router import (
        list_assignable_users,
    )

    mock_cls.return_value = MagicMock(
        search_assignable_users=MagicMock(
            return_value=[{"user_id": "u1", "display_name": "User"}]
        )
    )
    response = list_assignable_users(q="ab", limit=20)
    assert_envelope_meta(
        body_json(response),
        operation_id="list_quality_action_plan_assignable_users",
    )


@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@patch(f"{_AUDIT}.build_get_audit_5s_dashboard_use_case")
def test_audit_5s_dashboard_returns_meta(mock_build, _branch) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        get_audit_5s_dashboard,
    )

    result = MagicMock()
    result.to_dict.return_value = {
        "summary": {},
        "charts": {},
        "items": [],
        "pagination": {"page": 1, "page_size": 20, "total": 0},
    }
    mock_build.return_value = MagicMock(execute=MagicMock(return_value=result))
    response = get_audit_5s_dashboard(
        branch="01", date_start="2026-01-01", date_end="2026-01-31"
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="get_audit_5s_analytics_dashboard",
    )


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_audit_5s_audits_returns_meta(mock_repo) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import list_audits

    mock_repo.return_value = MagicMock(
        list_audits=MagicMock(return_value={"items": [{"id": "aud-1"}]})
    )
    response = list_audits(branch="01")
    assert_envelope_meta(
        body_json(response),
        operation_id="list_audit_5s_audits",
    )


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_get_audit_5s_audit_returns_meta(mock_repo) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import get_audit

    mock_repo.return_value = MagicMock(
        get_audit=MagicMock(
            return_value={"id": "aud-1", "branch_code": "01", "status": "draft"}
        )
    )
    response = get_audit("aud-1")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_audit_5s_audit",
    )


@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_get_audit_5s_catalog_returns_meta(mock_repo, _branch) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import get_catalog

    mock_repo.return_value = MagicMock(
        get_active_catalog=MagicMock(
            return_value={"version": 1, "criteria": [], "senso_names": []}
        )
    )
    response = get_catalog(branch="01")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_audit_5s_catalog",
    )


@patch(f"{_AUDIT}.branch_access_error", return_value=None)
@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_catalog_publications_returns_meta(mock_repo, _branch) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        list_catalog_publications,
    )

    mock_repo.return_value = MagicMock(
        list_catalog_publications=MagicMock(
            return_value={"items": [{"version": 1}]}
        )
    )
    response = list_catalog_publications(branch="01")
    assert_envelope_meta(
        body_json(response),
        operation_id="list_audit_5s_catalog_publications",
    )


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_audit_5s_criteria_returns_meta(mock_repo) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        list_criteria,
    )

    mock_repo.return_value = MagicMock(
        list_criteria_catalog=MagicMock(
            return_value={"items": [{"criterion_code": "C1"}]}
        )
    )
    response = list_criteria()
    assert_envelope_meta(
        body_json(response),
        operation_id="list_audit_5s_criteria",
    )


@patch(f"{_AUDIT}.build_audit_5s_repository")
def test_list_audit_5s_areas_returns_meta(mock_repo) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import list_areas

    mock_repo.return_value = MagicMock(
        list_areas=MagicMock(return_value={"items": [{"id": "area-1"}]})
    )
    response = list_areas(branch="01")
    assert_envelope_meta(
        body_json(response),
        operation_id="list_audit_5s_areas",
    )
