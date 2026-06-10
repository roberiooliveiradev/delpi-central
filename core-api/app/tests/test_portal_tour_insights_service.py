# app/tests/test_portal_tour_insights_service.py

from datetime import datetime, timedelta

from app.domain.portal_tour.portal_tour_insights_service import (
    compute_exploration_duration_seconds,
    compute_return_streak,
)
from app.domain.ports.portal_tour_repository import (
    PortalTourProgressDTO,
    PortalTourQuestEventDTO,
)


def test_compute_exploration_duration_seconds_uses_completed_at():
    started = datetime(2026, 6, 1, 10, 0, 0)
    completed = started + timedelta(minutes=12, seconds=30)

    progress = PortalTourProgressDTO(
        user_id="11111111-1111-1111-1111-111111111111",
        tour_version="v6",
        status="completed",
        completed_quest_ids=["a"],
        started_at=started,
        last_activity_at=completed,
        completed_at=completed,
    )

    assert compute_exploration_duration_seconds(progress) == 750


def test_compute_return_streak_after_gap():
    base = datetime(2026, 6, 1, 10, 0, 0)
    events = [
        PortalTourQuestEventDTO(
            quest_id="a",
            tour_version="v6",
            completed_at=base,
        ),
        PortalTourQuestEventDTO(
            quest_id="b",
            tour_version="v6",
            completed_at=base + timedelta(hours=1),
        ),
        PortalTourQuestEventDTO(
            quest_id="c",
            tour_version="v6",
            completed_at=base + timedelta(hours=26),
        ),
        PortalTourQuestEventDTO(
            quest_id="d",
            tour_version="v6",
            completed_at=base + timedelta(hours=27),
        ),
    ]

    count, message = compute_return_streak(events)

    assert count == 2
    assert message is not None
    assert "2 desafios" in message


def test_compute_return_streak_no_gap():
    base = datetime(2026, 6, 1, 10, 0, 0)
    events = [
        PortalTourQuestEventDTO(
            quest_id="a",
            tour_version="v6",
            completed_at=base,
        ),
        PortalTourQuestEventDTO(
            quest_id="b",
            tour_version="v6",
            completed_at=base + timedelta(hours=2),
        ),
    ]

    count, message = compute_return_streak(events)

    assert count == 0
    assert message is None
