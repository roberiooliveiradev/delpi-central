# app/tests/test_portal_tour_sync_use_case.py

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.sync_portal_tour_progress_use_case import (
    SyncPortalTourProgressUseCase,
)
from app.domain.ports.portal_tour_repository import PortalTourProgressDTO


@pytest.fixture
def uow():
    mock = MagicMock()
    mock.portal_tour.get_progress.return_value = None
    mock.portal_tour.record_quest_completion.return_value = True
    mock.portal_tour.upsert_progress.return_value = PortalTourProgressDTO(
        user_id=str(uuid4()),
        tour_version="2026-06-portal-v6-explore",
        status="exploring",
        completed_quest_ids=["open-apps"],
        started_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
        completed_at=None,
    )
    return mock


def test_sync_portal_tour_progress_merges_single_quest(uow):
    user_id = str(uuid4())
    uow.portal_tour.get_progress.return_value = PortalTourProgressDTO(
        user_id=user_id,
        tour_version="2026-06-portal-v6-explore",
        status="exploring",
        completed_quest_ids=["open-apps"],
        started_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
        completed_at=None,
    )

    SyncPortalTourProgressUseCase(uow).execute(
        user_id,
        tour_version="2026-06-portal-v6-explore",
        status="exploring",
        completed_quest_id="pin-app",
    )

    uow.portal_tour.upsert_progress.assert_called_once()
    kwargs = uow.portal_tour.upsert_progress.call_args.kwargs
    assert kwargs["completed_quest_ids"] == ["open-apps", "pin-app"]


def test_sync_portal_tour_progress_downgrades_invalid_completed_to_exploring(uow):
    user_id = str(uuid4())
    uow.portal_tour.get_progress.return_value = PortalTourProgressDTO(
        user_id=user_id,
        tour_version="2026-06-portal-v6-explore",
        status="exploring",
        completed_quest_ids=[],
        started_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
        completed_at=None,
    )
    uow.portal_tour.upsert_progress.return_value = PortalTourProgressDTO(
        user_id=user_id,
        tour_version="2026-06-portal-v6-explore",
        status="exploring",
        completed_quest_ids=[],
        started_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
        completed_at=None,
    )

    from app.domain.portal_tour.portal_tour_availability_service import PortalTourUserContext

    SyncPortalTourProgressUseCase(uow).execute(
        user_id,
        tour_version="2026-06-portal-v6-explore",
        status="completed",
        completed_quest_ids=[],
        user_context=PortalTourUserContext(permissions=frozenset(), is_superadmin=False),
    )

    kwargs = uow.portal_tour.upsert_progress.call_args.kwargs
    assert kwargs["status"] == "exploring"
    assert kwargs["completed_at"] is None


def test_sync_portal_tour_progress_rejects_invalid_status(uow):
    with pytest.raises(ValueError, match="status must be"):
        SyncPortalTourProgressUseCase(uow).execute(
            str(uuid4()),
            tour_version="2026-06-portal-v6-explore",
            status="invalid",
        )
