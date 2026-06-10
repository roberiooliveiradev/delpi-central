# app/tests/test_get_portal_tour_achievements_use_case.py

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.get_portal_tour_achievements_use_case import (
    GetPortalTourAchievementsUseCase,
)
from app.domain.portal_tour.portal_tour_availability_service import PortalTourUserContext
from app.domain.ports.portal_tour_repository import (
    PortalTourProgressDTO,
    PortalTourQuestEventDTO,
)


def test_get_portal_tour_achievements_unlocks_quest_and_milestone():
    user_id = str(uuid4())
    now = datetime.utcnow()

    uow = MagicMock()
    uow.portal_tour.get_progress.return_value = PortalTourProgressDTO(
        user_id=user_id,
        tour_version="2026-06-portal-v6-explore",
        status="exploring",
        completed_quest_ids=["sidebar-favorites", "open-apps"],
        started_at=now,
        last_activity_at=now,
        completed_at=None,
    )
    uow.portal_tour.list_quest_events.return_value = [
        PortalTourQuestEventDTO(
            quest_id="sidebar-favorites",
            tour_version="2026-06-portal-v6-explore",
            completed_at=now,
        )
    ]

    context = PortalTourUserContext(
        permissions=frozenset(),
        is_superadmin=False,
    )

    result = GetPortalTourAchievementsUseCase(uow).execute(
        user_id,
        context,
    )

    unlocked_ids = {item.id for item in result.items if item.unlocked}
    assert "quest-first-favorite" in unlocked_ids
    assert "category-admin" not in {item.id for item in result.items}
    assert result.total_count < 15
