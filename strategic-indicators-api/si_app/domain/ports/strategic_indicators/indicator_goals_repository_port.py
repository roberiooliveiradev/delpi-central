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
    def list_resolved_goals_map(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        scope_branch: str | None = None,
    ) -> dict[str, dict]:
        """Metas ativas (versão mais recente) por ``indicator_id`` para o período."""
        raise NotImplementedError

    @abstractmethod
    def list_latest_active_goals_map(
        self,
        *,
        indicator_ids: list[str],
        department_id: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        scope_branch: str | None = None,
    ) -> dict[str, dict]:
        """Meta ativa mais recente por indicador (qualquer ano), para fallback em séries históricas."""
        raise NotImplementedError

    @abstractmethod
    def list_branch_scoped_goals_map(
        self,
        *,
        indicator_ids: list[str],
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, dict[str, dict]]:
        """Metas ativas por filial (01/02) agrupadas por ``indicator_id``."""
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
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def activate_indicator_goal(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def deactivate_indicator_goal(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def delete_indicator_goal(
        self,
        *,
        goal_id: str,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_indicator_goal_policy(self, indicator_id: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def fetch_goal_identity(self, goal_id: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def bulk_create_indicator_goals(
        self,
        *,
        goal_year: int,
        items: list[dict],
        actor_user_id: str | None,
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
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_branch_scoped_goals_ignoring_validity(
        self,
        *,
        indicator_ids: list[str],
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
    ) -> dict[str, dict[str, dict]]:
        """Metas ativas por filial (01/02) sem filtro de vigência (valid_from/valid_to)."""
        raise NotImplementedError

    @abstractmethod
    def list_latest_goals_ignoring_validity(
        self,
        *,
        indicator_ids: list[str],
        department_id: str | None = None,
        competence: str | None = None,
        scope_branch: str | None = None,
    ) -> dict[str, dict]:
        """Meta ativa mais recente sem filtro de vigência (valid_from/valid_to)."""
        raise NotImplementedError

    @abstractmethod
    def list_goal_years_overview(self) -> list[dict]:
        raise NotImplementedError