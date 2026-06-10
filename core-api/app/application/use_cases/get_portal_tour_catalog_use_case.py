# app/application/use_cases/get_portal_tour_catalog_use_case.py

from dataclasses import dataclass

from app.application.unit_of_work import UnitOfWork
from app.domain.portal_tour.portal_tour_availability_service import (
    PortalTourUserContext,
    resolve_available_quests,
    resolve_new_quest_ids,
    resolve_optional_quest_ids,
    resolve_required_quest_ids,
)
from app.domain.portal_tour.portal_tour_gamification_service import (
    compute_earned_xp,
    compute_progress_percent,
    resolve_explorer_level,
)
from app.domain.portal_tour.portal_tour_quest_catalog import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    CURRENT_PORTAL_TOUR_VERSION,
    PortalTourQuestDefinition,
)


@dataclass
class PortalTourCatalogQuestItem:
    id: str
    title: str
    hint: str
    category: str
    category_label: str
    scope: str
    optional: bool
    introduced_in_version: str
    is_new: bool


@dataclass
class PortalTourCatalogResult:
    tour_version: str
    quests: list[PortalTourCatalogQuestItem]
    required_quest_ids: list[str]
    optional_quest_ids: list[str]
    new_quest_ids: list[str]
    progress_percent: int
    explorer_level: str
    earned_xp: int
    category_labels: dict[str, str]
    category_order: list[str]


class GetPortalTourCatalogUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        user_id: str,
        context: PortalTourUserContext,
        *,
        tour_version: str | None = None,
    ) -> PortalTourCatalogResult:
        version = (tour_version or "").strip() or CURRENT_PORTAL_TOUR_VERSION
        available_quests = resolve_available_quests(context)
        required_quest_ids = resolve_required_quest_ids(available_quests)
        optional_quest_ids = resolve_optional_quest_ids(available_quests)

        progress = self.uow.portal_tour.get_progress(user_id)
        quest_events = self.uow.portal_tour.list_quest_events(
            user_id,
            tour_version=version,
        )

        completed_quest_ids = set(progress.completed_quest_ids if progress else [])
        completed_quest_ids.update(event.quest_id for event in quest_events)

        new_quest_ids = resolve_new_quest_ids(
            available_quests,
            completed_quest_ids,
            tour_version=version,
        )
        new_set = set(new_quest_ids)

        progress_percent = compute_progress_percent(
            completed_quest_ids,
            required_quest_ids,
        )

        quests = [
            self._to_item(quest, is_new=quest.id in new_set)
            for quest in available_quests
        ]

        return PortalTourCatalogResult(
            tour_version=version,
            quests=quests,
            required_quest_ids=required_quest_ids,
            optional_quest_ids=optional_quest_ids,
            new_quest_ids=new_quest_ids,
            progress_percent=progress_percent,
            explorer_level=resolve_explorer_level(progress_percent),
            earned_xp=compute_earned_xp(available_quests, completed_quest_ids),
            category_labels=dict(CATEGORY_LABELS),
            category_order=list(CATEGORY_ORDER),
        )

    @staticmethod
    def _to_item(
        quest: PortalTourQuestDefinition,
        *,
        is_new: bool,
    ) -> PortalTourCatalogQuestItem:
        return PortalTourCatalogQuestItem(
            id=quest.id,
            title=quest.title,
            hint=quest.hint,
            category=quest.category,
            category_label=CATEGORY_LABELS.get(quest.category, quest.category),
            scope=quest.scope,
            optional=quest.optional,
            introduced_in_version=quest.introduced_in_version,
            is_new=is_new,
        )
