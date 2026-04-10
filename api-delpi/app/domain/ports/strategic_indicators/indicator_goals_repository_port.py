from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsIndicatorGoalsRepositoryPort(ABC):
    @abstractmethod
    def list_indicator_goals(
        self,
        *,
        indicator_id: str | None = None,
        goal_year: int | None = None,
        department_id: str | None = None,
        active_only: bool = False,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_indicator_goal_history(
        self,
        *,
        indicator_id: str,
        goal_year: int | None = None,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_resolved_goal(
        self,
        *,
        indicator_id: str,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def create_indicator_goal(
        self,
        *,
        indicator_id: str,
        goal_year: int,
        goal_label: str,
        goal_value: float,
        goal_periodicity: str,
        valid_from: str | None,
        valid_to: str | None,
        notes: str | None,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def update_indicator_goal(
        self,
        *,
        goal_id: str,
        goal_label: str,
        goal_value: float,
        goal_periodicity: str,
        valid_from: str | None,
        valid_to: str | None,
        notes: str | None,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def activate_indicator_goal(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def deactivate_indicator_goal(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def bulk_create_indicator_goals(
        self,
        *,
        goal_year: int,
        items: list[dict],
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def duplicate_goals_year(
        self,
        *,
        source_year: int,
        target_year: int,
        indicator_ids: list[str] | None,
        overwrite_existing: bool,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def fill_missing_goals(
        self,
        *,
        goal_year: int,
        indicator_ids: list[str],
        copy_from_year: int | None,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_goal_years_overview(self) -> list[dict]:
        raise NotImplementedError