"""Testes do fluxo de aprovação prévia do Central de Agendamento."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.application.security.api_delpi_permissions import (
    CENTRAL_AGENDAMENTO_APPROVE_FILIAL_ES,
)
from app.application.use_cases.scheduling.create_scheduling_booking_use_case import (
    CreateSchedulingBookingUseCase,
)
from app.application.use_cases.scheduling.decide_scheduling_booking_use_case import (
    DecideSchedulingBookingUseCase,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.interface.http.routes.scheduling.scheduling_router import (
    _branch_approve_allowed,
    _branch_view_allowed,
)


def test_branch_approve_allowed_with_approve_permission() -> None:
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[CENTRAL_AGENDAMENTO_APPROVE_FILIAL_ES],
    )

    with patch(
        "app.interface.http.routes.scheduling.scheduling_router.get_current_user",
        return_value=user,
    ):
        with patch(
            "app.interface.http.routes.scheduling.scheduling_router.has_permission",
            side_effect=lambda current_user, perm: perm in user.permissions,
        ):
            assert _branch_approve_allowed("ES") is True
            assert _branch_approve_allowed("SC") is False
            assert _branch_view_allowed("ES") is True


def test_create_booking_requires_approval_sets_pending() -> None:
    repo = MagicMock()
    repo.expire_overdue_pending_bookings.return_value = []
    repo.get_resource.return_value = {
        "id": "res-1",
        "branch_code": "ES",
        "active": True,
        "requires_approval": True,
        "name": "Sala VIP",
        "resource_type": "meeting_room",
    }
    start = datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)
    repo.create_booking.return_value = {
        "id": "book-1",
        "status": "pending",
        "branch_code": "ES",
        "title": "Reunião",
        "resource_name": "Sala VIP",
        "booked_by_user_id": "user-1",
        "booked_by_name": "Ana",
    }

    with patch(
        "app.application.use_cases.scheduling.create_scheduling_booking_use_case.notify_booking_approval_requested",
        return_value=True,
    ) as notify:
        data, operation_id, message = CreateSchedulingBookingUseCase(repo).execute(
            branch_code="ES",
            resource_id="res-1",
            title="Reunião",
            notes=None,
            start_at=start,
            end_at=end,
            booked_by_user_id="user-1",
            booked_by_name="Ana",
        )

    assert data["status"] == "pending"
    assert operation_id == "create_scheduling_booking"
    assert "aprovação" in message.lower()
    kwargs = repo.create_booking.call_args.kwargs
    assert kwargs["status"] == "pending"
    assert kwargs["expires_at"] == start
    notify.assert_called_once()


def test_create_booking_rejects_past_start_when_requires_approval() -> None:
    repo = MagicMock()
    repo.expire_overdue_pending_bookings.return_value = []
    repo.get_resource.return_value = {
        "id": "res-1",
        "branch_code": "ES",
        "active": True,
        "requires_approval": True,
    }
    start = datetime(2020, 1, 1, 10, 0, tzinfo=timezone.utc)

    with pytest.raises(PluginsRepositoryError, match="já iniciou"):
        CreateSchedulingBookingUseCase(repo).execute(
            branch_code="ES",
            resource_id="res-1",
            title="Passado",
            notes=None,
            start_at=start,
            end_at=start + timedelta(hours=1),
            booked_by_user_id="user-1",
            booked_by_name="Ana",
        )


def test_create_booking_blocks_recurrence_when_requires_approval() -> None:
    repo = MagicMock()
    repo.expire_overdue_pending_bookings.return_value = []
    repo.get_resource.return_value = {
        "id": "res-1",
        "branch_code": "ES",
        "active": True,
        "requires_approval": True,
    }
    start = datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc)

    with pytest.raises(PluginsRepositoryError, match="recorrência"):
        CreateSchedulingBookingUseCase(repo).execute(
            branch_code="ES",
            resource_id="res-1",
            title="Série",
            notes=None,
            start_at=start,
            end_at=start + timedelta(hours=1),
            booked_by_user_id="user-1",
            booked_by_name="Ana",
            recurrence={
                "frequency": "weekly",
                "until": start + timedelta(days=30),
                "interval": 1,
            },
        )


def test_decide_booking_rejects_self_approval() -> None:
    repo = MagicMock()
    repo.expire_overdue_pending_bookings.return_value = []
    repo.get_booking.return_value = {
        "id": "book-1",
        "status": "pending",
        "branch_code": "ES",
        "booked_by_user_id": "user-1",
    }

    with pytest.raises(PluginsRepositoryError, match="própria solicitação"):
        DecideSchedulingBookingUseCase(repo).execute(
            booking_id="book-1",
            action="approve",
            actor_user_id="user-1",
            actor_name="Ana",
            is_superadmin=False,
        )


def test_decide_booking_approve_notifies_requester() -> None:
    repo = MagicMock()
    repo.expire_overdue_pending_bookings.return_value = []
    pending = {
        "id": "book-1",
        "status": "pending",
        "branch_code": "ES",
        "booked_by_user_id": "user-1",
        "title": "Reunião",
    }
    confirmed = {
        **pending,
        "status": "confirmed",
        "decided_by_user_id": "approver-1",
        "decided_by_name": "Bruno",
    }
    repo.get_booking.return_value = pending
    repo.decide_booking.return_value = confirmed

    with patch(
        "app.application.use_cases.scheduling.decide_scheduling_booking_use_case.notify_booking_decision",
        return_value=True,
    ) as notify:
        result = DecideSchedulingBookingUseCase(repo).execute(
            booking_id="book-1",
            action="approve",
            actor_user_id="approver-1",
            actor_name="Bruno",
        )

    assert result["status"] == "confirmed"
    notify.assert_called_once_with(booking=confirmed, event_type="booking_approved")


def test_list_my_bookings_route_registered() -> None:
    from app.interface.http.routes.scheduling.scheduling_router import router

    paths = {getattr(route, "path", None) for route in router.routes}
    assert "/bookings/mine" in paths


def test_reject_requires_reason() -> None:
    repo = MagicMock()
    repo.expire_overdue_pending_bookings.return_value = []
    repo.get_booking.return_value = {
        "id": "book-1",
        "status": "pending",
        "branch_code": "ES",
        "booked_by_user_id": "user-1",
    }

    with pytest.raises(PluginsRepositoryError, match="motivo"):
        DecideSchedulingBookingUseCase(repo).execute(
            booking_id="book-1",
            action="reject",
            actor_user_id="approver-1",
            actor_name="Bruno",
            reason="  ",
        )
