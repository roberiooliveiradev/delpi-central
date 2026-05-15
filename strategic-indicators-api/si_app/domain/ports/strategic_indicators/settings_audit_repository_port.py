from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsSettingsAuditRepositoryPort(ABC):
    @abstractmethod
    def list_recent_events(
        self,
        *,
        limit: int = 20,
        entity_key: str | None = None,
    ) -> list[dict]:
        raise NotImplementedError