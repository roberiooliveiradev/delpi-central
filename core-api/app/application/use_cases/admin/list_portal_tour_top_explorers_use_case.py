# app/application/use_cases/admin/list_portal_tour_top_explorers_use_case.py

from dataclasses import dataclass
from datetime import datetime

from app.application.unit_of_work import UnitOfWork


@dataclass
class PortalTourTopExplorerItem:
    user_id: str
    name: str
    email: str
    tour_version: str
    quests_in_period: int
    last_activity_at: datetime | None


@dataclass
class ListPortalTourTopExplorersResult:
    period_days: int
    tour_version: str | None
    items: list[PortalTourTopExplorerItem]


class ListPortalTourTopExplorersUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        tour_version: str | None = None,
        period_days: int = 7,
        limit: int = 10,
    ) -> ListPortalTourTopExplorersResult:
        items = self.uow.portal_tour.list_top_explorers(
            tour_version=(tour_version or "").strip() or None,
            period_days=max(1, min(period_days, 90)),
            limit=max(1, min(limit, 50)),
        )

        return ListPortalTourTopExplorersResult(
            period_days=period_days,
            tour_version=(tour_version or "").strip() or None,
            items=[
                PortalTourTopExplorerItem(
                    user_id=item.user_id,
                    name=item.name,
                    email=item.email,
                    tour_version=item.tour_version,
                    quests_in_period=item.quests_in_period,
                    last_activity_at=item.last_activity_at,
                )
                for item in items
            ],
        )
