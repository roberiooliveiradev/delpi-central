from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsDepartmentIndicatorsRepositoryPort(ABC):
    @abstractmethod
    def list_department_indicators(
        self,
        *,
        department_id: str,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def create_department_indicator(
        self,
        *,
        department_id: str,
        indicator_id: str,
        indicator_name: str,
        weight_pct: float,
        scope_type: str,
        performance_direction: str,
        strategic_description: str,
        source_key: str | None,
        value_unit: str | None,
        value_prefix: str | None,
        value_suffix: str | None,
        value_decimals: int,
        display_order: int,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def update_department_indicator(
        self,
        *,
        indicator_id: str,
        indicator_name: str,
        weight_pct: float,
        scope_type: str,
        performance_direction: str,
        strategic_description: str,
        source_key: str | None,
        value_unit: str | None,
        value_prefix: str | None,
        value_suffix: str | None,
        value_decimals: int,
        is_active: bool,
        display_order: int,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def activate_department_indicator(
        self,
        *,
        indicator_id: str,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def deactivate_department_indicator(
        self,
        *,
        indicator_id: str,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def delete_department_indicator(
        self,
        *,
        indicator_id: str,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_indicator_ids_by_departments(
        self,
        *,
        department_ids: list[str] | None = None,
    ) -> list[str]:
        raise NotImplementedError