from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsSettingsRepositoryPort(ABC):
    @abstractmethod
    def get_settings(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def update_settings(
        self,
        *,
        weights: dict,
        goals: dict,
        parameters: dict,
        governance: dict,
        actor_user_id: str | None,
        actor_email: str | None,
    ) -> dict:
        raise NotImplementedError