# app/domain/ports/portal_tour_repository.py

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class PortalTourProgressDTO:
    user_id: str
    tour_version: str
    status: str
    completed_quest_ids: list[str]
    started_at: datetime
    last_activity_at: datetime
    completed_at: datetime | None


@dataclass
class PortalTourExplorerDTO:
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
class PortalTourQuestEventDTO:
    quest_id: str
    tour_version: str
    completed_at: datetime


@dataclass
class PortalTourTopExplorerDTO:
    user_id: str
    name: str
    email: str
    tour_version: str
    quests_in_period: int
    last_activity_at: datetime | None


class PortalTourRepository(Protocol):

    def get_progress(self, user_id: str) -> PortalTourProgressDTO | None:
        ...

    def upsert_progress(
        self,
        *,
        user_id: str,
        tour_version: str,
        status: str,
        completed_quest_ids: list[str],
        completed_at: datetime | None = None,
    ) -> PortalTourProgressDTO:
        ...

    def record_quest_completion(
        self,
        *,
        user_id: str,
        tour_version: str,
        quest_id: str,
        completed_at: datetime | None = None,
    ) -> bool:
        ...

    def delete_progress(self, user_id: str) -> None:
        ...

    def list_explorers(
        self,
        *,
        tour_version: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PortalTourExplorerDTO], int]:
        ...

    def list_quest_events(
        self,
        user_id: str,
        *,
        tour_version: str | None = None,
    ) -> list[PortalTourQuestEventDTO]:
        ...

    def list_top_explorers(
        self,
        *,
        tour_version: str | None = None,
        period_days: int = 7,
        limit: int = 10,
    ) -> list[PortalTourTopExplorerDTO]:
        ...
