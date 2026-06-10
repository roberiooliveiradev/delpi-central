# app/application/use_cases/admin/list_portal_tour_explorers_use_case.py

from dataclasses import dataclass
from datetime import datetime

from app.application.unit_of_work import UnitOfWork


@dataclass
class PortalTourExplorerItem:
    user_id: str
    name: str
    email: str
    tour_version: str
    status: str
    completed_quest_ids: list[str]
    completed_quest_count: int
    started_at: datetime
    last_activity_at: datetime
    completed_at: datetime | None


@dataclass
class ListPortalTourExplorersResult:
    items: list[PortalTourExplorerItem]
    total: int
    tour_version: str | None
    status: str | None


class ListPortalTourExplorersUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        *,
        tour_version: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ListPortalTourExplorersResult:
        normalized_status = (status or "").strip().lower() or None
        if normalized_status == "all":
            normalized_status = None

        items, total = self.uow.portal_tour.list_explorers(
            tour_version=(tour_version or "").strip() or None,
            status=normalized_status,
            limit=limit,
            offset=offset,
        )

        return ListPortalTourExplorersResult(
            items=[
                PortalTourExplorerItem(
                    user_id=item.user_id,
                    name=item.name,
                    email=item.email,
                    tour_version=item.tour_version,
                    status=item.status,
                    completed_quest_ids=list(item.completed_quest_ids),
                    completed_quest_count=item.completed_quest_count,
                    started_at=item.started_at,
                    last_activity_at=item.last_activity_at,
                    completed_at=item.completed_at,
                )
                for item in items
            ],
            total=total,
            tour_version=(tour_version or "").strip() or None,
            status=normalized_status,
        )
