from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsAdminDepartmentsRepositoryPort(ABC):
    @abstractmethod
    def list_departments(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def create_department(
        self,
        *,
        department_id: str,
        department_name: str,
        short_name: str,
        strategic_summary: str,
        headline_goal: str,
        supporting_focus: str,
        weight_pct: float,
        aggregation_mode: str,
        display_order: int,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def update_department(
        self,
        *,
        department_id: str,
        department_name: str,
        short_name: str,
        strategic_summary: str,
        headline_goal: str,
        supporting_focus: str,
        weight_pct: float,
        aggregation_mode: str,
        is_active: bool,
        display_order: int,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def activate_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def deactivate_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def delete_department(
        self,
        *,
        department_id: str,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError