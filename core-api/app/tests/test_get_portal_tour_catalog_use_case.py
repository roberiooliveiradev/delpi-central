# app/tests/test_get_portal_tour_catalog_use_case.py

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.get_portal_tour_catalog_use_case import (
    GetPortalTourCatalogUseCase,
)
from app.domain.portal_tour.portal_tour_availability_service import PortalTourUserContext
from app.domain.ports.portal_tour_repository import PortalTourProgressDTO


def test_get_portal_tour_catalog_scopes_quests_and_progress():
    user_id = str(uuid4())
    now = datetime.utcnow()

    uow = MagicMock()
    uow.portal_tour.get_progress.return_value = PortalTourProgressDTO(
        user_id=user_id,
        tour_version="2026-06-portal-v6-explore",
        status="exploring",
        completed_quest_ids=["open-apps"],
        started_at=now,
        last_activity_at=now,
        completed_at=None,
    )
    uow.portal_tour.list_quest_events.return_value = []

    context = PortalTourUserContext(
        permissions=frozenset(),
        is_superadmin=False,
    )

    result = GetPortalTourCatalogUseCase(uow).execute(user_id, context)

    quest_ids = {item.id for item in result.quests}
    assert "open-apps" in quest_ids
    assert "sidebar-admin" not in quest_ids
    assert result.required_quest_ids
    assert "sidebar-admin" not in result.required_quest_ids
    assert result.progress_percent >= 0
    assert result.new_quest_ids
