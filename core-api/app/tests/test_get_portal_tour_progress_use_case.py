# app/tests/test_get_portal_tour_progress_use_case.py

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.get_portal_tour_progress_use_case import (
    GetPortalTourProgressUseCase,
)
from app.domain.ports.portal_tour_repository import PortalTourProgressDTO


def test_get_portal_tour_progress_normalizes_invalid_completed_to_exploring():
    user_id = str(uuid4())
    now = datetime.utcnow()

    uow = MagicMock()
    uow.portal_tour.get_progress.return_value = PortalTourProgressDTO(
        user_id=user_id,
        tour_version="2026-06-portal-v6-explore",
        status="completed",
        completed_quest_ids=[],
        started_at=now,
        last_activity_at=now,
        completed_at=now,
    )
    uow.portal_tour.upsert_progress.return_value = PortalTourProgressDTO(
        user_id=user_id,
        tour_version="2026-06-portal-v6-explore",
        status="exploring",
        completed_quest_ids=[],
        started_at=now,
        last_activity_at=now,
        completed_at=None,
    )

    result = GetPortalTourProgressUseCase(uow).execute(user_id)

    assert result.status == "exploring"
    assert result.completed_at is None
    uow.portal_tour.upsert_progress.assert_called_once()


def test_get_portal_tour_progress_normalizes_dismissed_to_exploring():
    user_id = str(uuid4())
    now = datetime.utcnow()

    uow = MagicMock()
    uow.portal_tour.get_progress.return_value = PortalTourProgressDTO(
        user_id=user_id,
        tour_version="2026-06-portal-v6-explore",
        status="dismissed",
        completed_quest_ids=["open-apps"],
        started_at=now,
        last_activity_at=now,
        completed_at=None,
    )
    uow.portal_tour.upsert_progress.return_value = PortalTourProgressDTO(
        user_id=user_id,
        tour_version="2026-06-portal-v6-explore",
        status="exploring",
        completed_quest_ids=["open-apps"],
        started_at=now,
        last_activity_at=now,
        completed_at=None,
    )

    result = GetPortalTourProgressUseCase(uow).execute(user_id)

    assert result.status == "exploring"
    uow.portal_tour.upsert_progress.assert_called_once()
