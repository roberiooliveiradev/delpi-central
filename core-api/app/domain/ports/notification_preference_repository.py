# app/domain/ports/notification_preference_repository.py

from dataclasses import dataclass
from typing import Protocol


@dataclass
class NotificationPreferenceDTO:
    user_id: str
    muted_categories: list[str]


class NotificationPreferenceRepository(Protocol):

    def get_muted_categories(self, user_id: str) -> list[str]:
        ...

    def set_muted_categories(self, user_id: str, muted_categories: list[str]) -> None:
        ...

    def is_category_muted(self, user_id: str, category: str) -> bool:
        ...

    def filter_user_ids_accepting_category(self, user_ids: list[str], category: str) -> list[str]:
        ...
