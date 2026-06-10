# app/application/use_cases/admin/list_portal_tour_explorers_use_case.py

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.portal_tour.portal_tour_availability_service import PortalTourUserContext
from app.domain.portal_tour.portal_tour_explorer_progress_service import (
    resolve_explorer_progress_snapshot,
)
from app.domain.services.permission_resolver import PermissionResolver


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
    progress_percent: int
    explorer_level: str
    required_quest_done: int
    required_quest_total: int


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

        resolver = PermissionResolver(
            self.uow.permission_queries,
            self.uow.cache,
        )

        enriched: list[PortalTourExplorerItem] = []
        for item in items:
            permissions = resolver.resolve(
                UUID(item.user_id),
                bool(item.is_superadmin),
            )
            snapshot = resolve_explorer_progress_snapshot(
                list(item.completed_quest_ids),
                PortalTourUserContext(
                    permissions=frozenset(permissions),
                    is_superadmin=bool(item.is_superadmin),
                ),
            )
            enriched.append(
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
                    progress_percent=snapshot.progress_percent,
                    explorer_level=snapshot.explorer_level,
                    required_quest_done=snapshot.required_quest_done,
                    required_quest_total=snapshot.required_quest_total,
                )
            )

        return ListPortalTourExplorersResult(
            items=enriched,
            total=total,
            tour_version=(tour_version or "").strip() or None,
            status=normalized_status,
        )
