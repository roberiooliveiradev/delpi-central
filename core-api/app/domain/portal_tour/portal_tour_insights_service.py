# app/domain/portal_tour/portal_tour_insights_service.py

from datetime import datetime, timedelta

from app.domain.ports.portal_tour_repository import (
    PortalTourProgressDTO,
    PortalTourQuestEventDTO,
)

RETURN_GAP_HOURS = 24


def compute_exploration_duration_seconds(
    progress: PortalTourProgressDTO | None,
    *,
    now: datetime | None = None,
) -> int | None:
    if not progress or not progress.started_at:
        return None

    end = progress.completed_at or progress.last_activity_at or now or datetime.utcnow()
    delta = end - progress.started_at
    return max(0, int(delta.total_seconds()))


def compute_return_streak(
    quest_events: list[PortalTourQuestEventDTO],
    *,
    gap_hours: int = RETURN_GAP_HOURS,
) -> tuple[int, str | None]:
    if len(quest_events) < 2:
        return 0, None

    ordered = sorted(quest_events, key=lambda item: item.completed_at)
    gap = timedelta(hours=gap_hours)
    last_gap_index = -1

    for index in range(1, len(ordered)):
        previous = ordered[index - 1].completed_at
        current = ordered[index].completed_at
        if current - previous >= gap:
            last_gap_index = index

    if last_gap_index <= 0:
        return 0, None

    quests_after_return = len(ordered) - last_gap_index
    if quests_after_return <= 0:
        return 0, None

    if quests_after_return == 1:
        message = "Você voltou e completou mais 1 desafio — continue explorando!"
    else:
        message = (
            f"Você voltou e completou mais {quests_after_return} desafios — "
            "continue explorando!"
        )

    return quests_after_return, message
