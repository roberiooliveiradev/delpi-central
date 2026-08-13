"""Rotas públicas de agendamento — token do recurso, disponibilidade e solicitação."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from fastapi.responses import JSONResponse


def _json(response) -> dict:
    if isinstance(response, JSONResponse):
        import json

        return json.loads(bytes(response.body).decode())
    return response


_PUB = "app.interface.http.routes.scheduling.scheduling_public_router"


@patch(f"{_PUB}.build_scheduling_repository")
def test_get_public_scheduling_resource_returns_meta(mock_build) -> None:
    from app.interface.http.routes.scheduling.scheduling_public_router import (
        get_public_scheduling_resource,
    )

    repo = MagicMock()
    repo.get_resource_by_public_token.return_value = {
        "id": "res-1",
        "branch_code": "ES",
        "name": "Choupana",
        "resource_type": "other",
        "description": "Espaço externo",
        "capacity": 40,
        "requires_approval": False,
        "public_booking_enabled": True,
        "public_token": "tok",
        "active": True,
    }
    mock_build.return_value = repo

    body = _json(get_public_scheduling_resource("tok"))
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_public_scheduling_resource"
    assert body["data"]["name"] == "Choupana"
    assert body["data"]["requires_approval"] is True
    assert "public_token" not in body["data"]


@patch(f"{_PUB}.build_scheduling_repository")
def test_get_public_scheduling_resource_not_found(mock_build) -> None:
    from app.interface.http.routes.scheduling.scheduling_public_router import (
        get_public_scheduling_resource,
    )

    repo = MagicMock()
    repo.get_resource_by_public_token.return_value = None
    mock_build.return_value = repo

    response = get_public_scheduling_resource("missing")
    assert isinstance(response, JSONResponse)
    assert response.status_code == 404


@patch(f"{_PUB}.ExpirePendingSchedulingBookingsUseCase")
@patch(f"{_PUB}.build_scheduling_repository")
def test_get_public_availability_strips_pii(mock_build, _expire) -> None:
    from app.interface.http.routes.scheduling.scheduling_public_router import (
        get_public_scheduling_availability,
    )

    start = datetime.now(timezone.utc)
    end = start + timedelta(days=7)
    repo = MagicMock()
    repo.get_resource_by_public_token.return_value = {
        "id": "res-1",
        "branch_code": "ES",
        "name": "Choupana",
        "resource_type": "other",
        "description": None,
        "capacity": None,
        "requires_approval": True,
        "active": True,
    }
    repo.list_busy_slots.return_value = [
        {"start_at": start, "end_at": start + timedelta(hours=2)},
    ]
    mock_build.return_value = repo

    body = _json(
        get_public_scheduling_availability(
            "tok",
            from_at=start.isoformat(),
            to_at=end.isoformat(),
        )
    )
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_public_scheduling_availability"
    assert body["data"]["busy"][0]["start_at"]
    assert "booked_by_name" not in body["data"]["busy"][0]


@patch(f"{_PUB}.CreatePublicSchedulingBookingUseCase")
@patch(f"{_PUB}.build_scheduling_repository")
def test_create_public_booking_honeypot_accepts_without_persist(mock_build, mock_uc) -> None:
    from app.interface.http.routes.scheduling.scheduling_public_router import (
        PublicBookingBody,
        create_public_scheduling_booking,
    )

    mock_build.return_value = MagicMock()
    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(hours=2)
    body = PublicBookingBody(
        requester_name="Maria",
        requester_email="maria@delpi.com.br",
        title="Uso da Choupana",
        start_at=start,
        end_at=end,
        website="http://spam",
    )
    response = _json(create_public_scheduling_booking("tok", body))
    assert response["success"] is True
    assert response["data"]["accepted"] is True
    mock_uc.assert_not_called()


@patch(
    "app.application.use_cases.scheduling.create_public_scheduling_booking_use_case.notify_booking_approval_requested"
)
def test_public_booking_use_case_forces_pending(mock_notify) -> None:
    from app.application.use_cases.scheduling.create_public_scheduling_booking_use_case import (
        CreatePublicSchedulingBookingUseCase,
    )

    repo = MagicMock()
    repo.get_resource_by_public_token.return_value = {
        "id": "res-1",
        "branch_code": "ES",
        "name": "Choupana",
        "active": True,
        "public_booking_enabled": True,
    }
    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(hours=2)
    repo.create_booking.return_value = {
        "id": "b1",
        "status": "pending",
        "start_at": start,
        "end_at": end,
        "resource_name": "Choupana",
        "branch_code": "ES",
    }

    data = CreatePublicSchedulingBookingUseCase(repo).execute(
        public_token="tok",
        requester_name="Maria Silva",
        requester_email="maria@delpi.com.br",
        requester_phone="27999990000",
        title="Evento",
        notes=None,
        start_at=start,
        end_at=end,
    )
    assert data["status"] == "pending"
    kwargs = repo.create_booking.call_args.kwargs
    assert kwargs["status"] == "pending"
    assert kwargs["booked_by_user_id"] == "public:res-1"
    assert kwargs["requester_email"] == "maria@delpi.com.br"
    mock_notify.assert_called_once()
