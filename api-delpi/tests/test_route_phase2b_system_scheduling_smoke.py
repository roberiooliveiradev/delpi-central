"""Smoke — system (Protheus metadata + console) e scheduling restante."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_SYSTEM = "app.interface.http.routes.system_routes"
_SCHED = "app.interface.http.routes.scheduling.scheduling_router"


@patch(f"{_SYSTEM}.build_get_table_use_case")
def test_get_protheus_table_returns_meta(mock_build) -> None:
    from app.interface.http.routes.system_routes import table

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"name": "SB1010"})
    )
    response = table(tableName="SB1010")
    assert_envelope_meta(
        body_json(response), operation_id="get_protheus_table", shape="scalar"
    )


@patch(f"{_SYSTEM}.build_list_table_columns_use_case")
def test_list_protheus_table_columns_returns_meta(mock_build) -> None:
    from app.interface.http.routes.system_routes import table_columns

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"items": [], "page": 1, "total": 0})
    )
    response = table_columns(tableName="SB1010", page=1, limit=50)
    assert_envelope_meta(
        body_json(response),
        operation_id="list_protheus_table_columns",
        shape="paged_list",
    )


@patch(f"{_SYSTEM}.build_get_table_indexes_use_case")
def test_get_protheus_table_indexes_returns_meta(mock_build) -> None:
    from app.interface.http.routes.system_routes import table_indexes

    mock_build.return_value = MagicMock(execute=MagicMock(return_value={"items": []}))
    response = table_indexes(tableName="SB1010")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_protheus_table_indexes",
        shape="paged_list",
    )


@patch(f"{_SYSTEM}.build_get_table_relations_use_case")
def test_get_protheus_table_relations_returns_meta(mock_build) -> None:
    from app.interface.http.routes.system_routes import table_relations

    mock_build.return_value = MagicMock(execute=MagicMock(return_value={"items": []}))
    response = table_relations(tableName="SB1010")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_protheus_table_relations",
        shape="paged_list",
    )


@patch(f"{_SYSTEM}.build_get_table_schema_use_case")
def test_get_protheus_table_schema_returns_meta(mock_build) -> None:
    from app.interface.http.routes.system_routes import table_schema

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"table": "SB1010", "columns": []})
    )
    response = table_schema(tableName="SB1010")
    assert_envelope_meta(
        body_json(response),
        operation_id="get_protheus_table_schema",
        shape="composite_analysis",
    )


@patch(f"{_SYSTEM}.build_search_columns_in_table_use_case")
def test_search_protheus_columns_in_table_returns_meta(mock_build) -> None:
    from app.interface.http.routes.system_routes import search_columns

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"items": [], "total": 0})
    )
    response = search_columns(tableName="SB1010", q="codigo")
    assert_envelope_meta(
        body_json(response),
        operation_id="search_protheus_columns_in_table",
        shape="paged_list",
    )


@patch(f"{_SYSTEM}.build_search_columns_by_description_use_case")
def test_search_protheus_columns_by_description_returns_meta(mock_build) -> None:
    from app.interface.http.routes.system_routes import search_columns_global

    mock_build.return_value = MagicMock(
        execute=MagicMock(return_value={"items": [], "page": 1, "total": 0})
    )
    response = search_columns_global(description="produto", page=1, limit=20)
    assert_envelope_meta(
        body_json(response),
        operation_id="search_protheus_columns_by_description",
        shape="paged_list",
    )


@patch(f"{_SYSTEM}.load_smoke_definitions")
def test_get_smoke_definitions_returns_meta(mock_load) -> None:
    from app.interface.http.routes.system_routes import get_smoke_definitions

    mock_load.return_value = {"suites": []}
    response = get_smoke_definitions()
    assert_envelope_meta(
        body_json(response), operation_id="get_smoke_definitions", shape="scalar"
    )


@patch(f"{_SYSTEM}.list_console_alert_history")
def test_get_console_alerts_returns_meta(mock_list) -> None:
    from app.interface.http.routes.system_routes import get_console_alerts

    mock_list.return_value = {"alerts": [], "total": 0}
    response = get_console_alerts(limit=25)
    assert_envelope_meta(
        body_json(response), operation_id="get_console_alerts", shape="scalar"
    )


@patch(f"{_SYSTEM}.process_console_alerts")
def test_notify_console_smoke_alerts_returns_meta(mock_process) -> None:
    from app.interface.http.routes.system_routes import post_console_alerts_smoke

    mock_process.return_value = {"alert_count": 0, "alerts": []}
    response = post_console_alerts_smoke(
        smoke_result={"suiteId": "x", "passed": 1, "failed": 0, "cases": []},
        notify=False,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="notify_console_smoke_alerts",
        shape="scalar",
    )


@patch(f"{_SCHED}._branch_access_error", return_value=None)
@patch(f"{_SCHED}.build_scheduling_repository")
def test_create_scheduling_resource_returns_meta(mock_build, _branch) -> None:
    from app.interface.http.routes.scheduling.scheduling_router import (
        CreateResourceBody,
        create_resource,
    )

    mock_build.return_value = MagicMock(
        create_resource=MagicMock(return_value={"id": "r1", "name": "Sala A"})
    )
    with patch(f"{_SCHED}._current_user_id", return_value="user-1"):
        response = create_resource(
            body=CreateResourceBody(
                branch_code="ES",
                name="Sala A",
                resource_type="meeting_room",
            )
        )
    assert_envelope_meta(
        body_json(response),
        operation_id="create_scheduling_resource",
        shape="scalar",
    )


@patch(f"{_SCHED}._branch_access_error", return_value=None)
@patch(f"{_SCHED}.build_scheduling_repository")
def test_update_scheduling_resource_returns_meta(mock_build, _branch) -> None:
    from app.interface.http.routes.scheduling.scheduling_router import (
        UpdateResourceBody,
        update_resource,
    )

    repo = MagicMock()
    repo.get_resource.return_value = {"id": "r1", "branch_code": "ES"}
    repo.update_resource.return_value = {"id": "r1", "name": "Sala B"}
    mock_build.return_value = repo

    response = update_resource(
        resource_id="r1", body=UpdateResourceBody(name="Sala B")
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="update_scheduling_resource",
        shape="scalar",
    )


@patch(f"{_SCHED}.ExpirePendingSchedulingBookingsUseCase")
@patch(f"{_SCHED}._branch_access_error", return_value=None)
@patch(f"{_SCHED}.build_scheduling_repository")
def test_list_scheduling_bookings_returns_meta(mock_build, _branch, mock_expire) -> None:
    from app.interface.http.routes.scheduling.scheduling_router import list_bookings

    mock_expire.return_value = MagicMock(execute=MagicMock())
    mock_build.return_value = MagicMock(list_bookings=MagicMock(return_value=[]))
    response = list_bookings(
        branch="ES",
        from_at="2026-07-01T00:00:00+00:00",
        to_at="2026-07-02T00:00:00+00:00",
        resource_id=None,
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="list_scheduling_bookings",
        shape="paged_list",
    )


@patch(f"{_SCHED}.ExpirePendingSchedulingBookingsUseCase")
@patch(f"{_SCHED}._branch_approve_allowed", return_value=True)
@patch(f"{_SCHED}._branch_access_error", return_value=None)
@patch(f"{_SCHED}.build_scheduling_repository")
def test_list_pending_scheduling_bookings_returns_meta(
    mock_build, _branch, _approve, mock_expire
) -> None:
    from app.interface.http.routes.scheduling.scheduling_router import (
        list_pending_bookings,
    )

    mock_expire.return_value = MagicMock(execute=MagicMock())
    mock_build.return_value = MagicMock(
        list_pending_bookings=MagicMock(return_value=[])
    )
    response = list_pending_bookings(branch="ES", mine=False)
    assert_envelope_meta(
        body_json(response),
        operation_id="list_pending_scheduling_bookings",
        shape="paged_list",
    )


@patch(f"{_SCHED}.ExpirePendingSchedulingBookingsUseCase")
@patch(f"{_SCHED}._current_user_id", return_value="user-1")
@patch(f"{_SCHED}._branch_access_error", return_value=None)
@patch(f"{_SCHED}.build_scheduling_repository")
def test_list_my_scheduling_bookings_returns_meta(
    mock_build, _branch, _user, mock_expire
) -> None:
    from app.interface.http.routes.scheduling.scheduling_router import list_my_bookings

    mock_expire.return_value = MagicMock(execute=MagicMock())
    mock_build.return_value = MagicMock(list_my_bookings=MagicMock(return_value=[]))
    response = list_my_bookings(branch="ES", limit=50)
    assert_envelope_meta(
        body_json(response),
        operation_id="list_my_scheduling_bookings",
        shape="paged_list",
    )


@patch(f"{_SCHED}.DecideSchedulingBookingUseCase")
@patch(f"{_SCHED}._branch_access_error", return_value=None)
@patch(f"{_SCHED}.build_scheduling_repository")
def test_approve_scheduling_booking_returns_meta(mock_build, _branch, mock_decide) -> None:
    from app.interface.http.routes.scheduling.scheduling_router import approve_booking

    mock_build.return_value = MagicMock(
        get_booking=MagicMock(
            return_value={"id": "b1", "branch_code": "ES", "booked_by_user_id": "other"}
        )
    )
    mock_decide.return_value = MagicMock(
        execute=MagicMock(return_value={"id": "b1", "status": "approved"})
    )
    with (
        patch(f"{_SCHED}._current_user_id", return_value="approver"),
        patch(f"{_SCHED}._current_user_name", return_value="Approver"),
        patch(f"{_SCHED}._is_superadmin", return_value=True),
    ):
        response = approve_booking(booking_id="b1")
    assert_envelope_meta(
        body_json(response),
        operation_id="approve_scheduling_booking",
        shape="scalar",
    )


@patch(f"{_SCHED}.DecideSchedulingBookingUseCase")
@patch(f"{_SCHED}._branch_access_error", return_value=None)
@patch(f"{_SCHED}.build_scheduling_repository")
def test_reject_scheduling_booking_returns_meta(mock_build, _branch, mock_decide) -> None:
    from app.interface.http.routes.scheduling.scheduling_router import (
        RejectBookingBody,
        reject_booking,
    )

    mock_build.return_value = MagicMock(
        get_booking=MagicMock(
            return_value={"id": "b1", "branch_code": "ES", "booked_by_user_id": "other"}
        )
    )
    mock_decide.return_value = MagicMock(
        execute=MagicMock(return_value={"id": "b1", "status": "rejected"})
    )
    with (
        patch(f"{_SCHED}._current_user_id", return_value="approver"),
        patch(f"{_SCHED}._current_user_name", return_value="Approver"),
        patch(f"{_SCHED}._is_superadmin", return_value=True),
    ):
        response = reject_booking(
            booking_id="b1", body=RejectBookingBody(reason="Indisponível")
        )
    assert_envelope_meta(
        body_json(response),
        operation_id="reject_scheduling_booking",
        shape="scalar",
    )


@patch(f"{_SCHED}._branch_access_error", return_value=None)
@patch(f"{_SCHED}.build_scheduling_repository")
def test_cancel_scheduling_booking_returns_meta(mock_build, _branch) -> None:
    from app.interface.http.routes.scheduling.scheduling_router import cancel_booking

    repo = MagicMock()
    repo.get_booking.return_value = {
        "id": "b1",
        "branch_code": "ES",
        "booked_by_user_id": "user-1",
        "status": "confirmed",
    }
    repo.cancel_booking.return_value = {"id": "b1", "status": "cancelled", "cancelled_count": 1}
    mock_build.return_value = repo

    with (
        patch(f"{_SCHED}._current_user_id", return_value="user-1"),
        patch(f"{_SCHED}._is_superadmin", return_value=False),
        patch(f"{_SCHED}._branch_manage_allowed", return_value=False),
        patch(f"{_SCHED}._branch_approve_allowed", return_value=False),
    ):
        response = cancel_booking(booking_id="b1", scope="occurrence")

    assert_envelope_meta(
        body_json(response),
        operation_id="cancel_scheduling_booking",
        shape="scalar",
    )
