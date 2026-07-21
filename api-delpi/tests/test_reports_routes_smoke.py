"""Smoke Nível A — Delpi Reports (/reports)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

from app.interface.http.routes.reports.reports_router import (
    CreateReportDefinitionBody,
    ReplaceRecipientsBody,
    RecipientItemBody,
    UpdateReportDefinitionBody,
    UpsertScheduleBody,
    create_report_definition,
    get_report_definition,
    get_report_run,
    get_report_schedule,
    list_report_definitions,
    list_report_providers,
    list_report_recipients,
    list_report_runs,
    preview_safety_stock_shortage_30d,
    process_pending_report_schedules,
    replace_report_recipients,
    run_report_definition,
    update_report_definition,
    upsert_report_schedule,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_DEF_ID = UUID("11111111-1111-1111-1111-111111111111")

_DEFINITION = {
    "id": str(_DEF_ID),
    "name": "Rupturas 30d",
    "providerKey": "safety_stock_shortage_30d",
    "params": {"branch": "01"},
    "active": True,
    "createdByUserId": "user-1",
    "createdAt": "2026-07-21T12:00:00+00:00",
    "updatedAt": "2026-07-21T12:00:00+00:00",
}


@patch(
    "app.interface.http.routes.reports.reports_router.build_list_report_definitions_use_case"
)
def test_list_report_definitions_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"items": [], "total": 0}
    mock_build.return_value = use_case

    response = list_report_definitions()
    assert_envelope_meta(
        body_json(response),
        operation_id="list_report_definitions",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.build_create_report_definition_use_case"
)
def test_create_report_definition_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _DEFINITION
    mock_build.return_value = use_case

    response = create_report_definition(
        body=CreateReportDefinitionBody(
            name="Rupturas 30d",
            providerKey="safety_stock_shortage_30d",
            params={"branch": "01"},
            active=True,
        )
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="create_report_definition",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.build_get_report_definition_use_case"
)
def test_get_report_definition_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _DEFINITION
    mock_build.return_value = use_case

    response = get_report_definition(definition_id=_DEF_ID)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_report_definition",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.build_update_report_definition_use_case"
)
def test_update_report_definition_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {**_DEFINITION, "active": False}
    mock_build.return_value = use_case

    response = update_report_definition(
        definition_id=_DEF_ID,
        body=UpdateReportDefinitionBody(active=False),
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="update_report_definition",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.build_list_report_runs_use_case"
)
def test_list_report_runs_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"items": [], "total": 0}
    mock_build.return_value = use_case

    response = list_report_runs()
    assert_envelope_meta(
        body_json(response),
        operation_id="list_report_runs",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.build_list_report_providers_use_case"
)
def test_list_report_providers_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"items": [], "total": 0}
    mock_build.return_value = use_case

    response = list_report_providers()
    assert_envelope_meta(
        body_json(response),
        operation_id="list_report_providers",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.branch_access_error",
    return_value=None,
)
@patch(
    "app.interface.http.routes.reports.reports_router.build_preview_safety_stock_shortage_30d_use_case"
)
def test_preview_safety_stock_shortage_30d_returns_meta(
    mock_build,
    _mock_branch,
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [],
        "total": 0,
        "title": "Rupturas de estoque nos próximos 30 dias",
        "columns": ["product_code"],
        "meta": {"branch": "01", "horizonDays": 30},
        "providerKey": "safety_stock_shortage_30d",
    }
    mock_build.return_value = use_case

    response = preview_safety_stock_shortage_30d(branch="01", horizonDays=30)
    assert_envelope_meta(
        body_json(response),
        operation_id="preview_report_provider_safety_stock_shortage_30d",
        shape="paged_list",
    )
    use_case.execute.assert_called_once()
    params = use_case.execute.call_args.args[0]
    assert params["branch"] == "01"
    assert params["horizonDays"] == 30


@patch(
    "app.interface.http.routes.reports.reports_router.build_list_report_recipients_use_case"
)
def test_list_report_recipients_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"items": [], "total": 0}
    mock_build.return_value = use_case
    response = list_report_recipients(definition_id=_DEF_ID)
    assert_envelope_meta(
        body_json(response),
        operation_id="list_report_recipients",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.build_replace_report_recipients_use_case"
)
def test_replace_report_recipients_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"items": [], "total": 0}
    mock_build.return_value = use_case
    response = replace_report_recipients(
        definition_id=_DEF_ID,
        body=ReplaceRecipientsBody(
            items=[RecipientItemBody(userId="u1", email="a@delpi.com.br")]
        ),
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="replace_report_recipients",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.build_get_report_schedule_use_case"
)
def test_get_report_schedule_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "id": "s1",
        "definitionId": str(_DEF_ID),
        "scheduleKind": "daily",
        "hour": 8,
        "minute": 0,
        "enabled": True,
    }
    mock_build.return_value = use_case
    response = get_report_schedule(definition_id=_DEF_ID)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_report_schedule",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.build_upsert_report_schedule_use_case"
)
def test_upsert_report_schedule_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "id": "s1",
        "scheduleKind": "daily",
        "hour": 8,
        "minute": 30,
        "enabled": True,
    }
    mock_build.return_value = use_case
    response = upsert_report_schedule(
        definition_id=_DEF_ID,
        body=UpsertScheduleBody(scheduleKind="daily", hour=8, minute=30, enabled=True),
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="upsert_report_schedule",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.build_run_report_definition_use_case"
)
def test_run_report_definition_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "id": "run-1",
        "status": "succeeded",
        "deliveries": [],
    }
    mock_build.return_value = use_case
    response = run_report_definition(definition_id=_DEF_ID)
    assert_envelope_meta(
        body_json(response),
        operation_id="run_report_definition",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.build_get_report_run_use_case"
)
def test_get_report_run_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"id": "run-1", "status": "succeeded", "deliveries": []}
    mock_build.return_value = use_case
    response = get_report_run(run_id=UUID("22222222-2222-2222-2222-222222222222"))
    assert_envelope_meta(
        body_json(response),
        operation_id="get_report_run",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.reports.reports_router.request_has_valid_internal_service_token",
    return_value=True,
)
@patch(
    "app.interface.http.routes.reports.reports_router.build_process_due_report_schedules_use_case"
)
def test_process_pending_report_schedules_returns_meta(
    mock_build,
    _mock_token,
) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "dueCount": 0,
        "processedCount": 0,
        "errorCount": 0,
        "processed": [],
        "errors": [],
    }
    mock_build.return_value = use_case
    response = process_pending_report_schedules(request=MagicMock(), limit=10)
    assert_envelope_meta(
        body_json(response),
        operation_id="process_pending_report_schedules",
        shape="scalar",
    )
