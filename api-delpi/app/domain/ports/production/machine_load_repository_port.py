"""Port — carga máquina (operações alocadas por centro de trabalho)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MachineLoadRepositoryPort(ABC):
    @abstractmethod
    def get_work_centers(self, **filters: Any) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def count_operations(self, **filters: Any) -> int:
        ...

    @abstractmethod
    def get_operations(
        self,
        *,
        sort: str,
        offset: int,
        page_size: int,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_appointment_status(
        self,
        *,
        branch: str,
        appointment_active_since: str,
        appointment_history_since: str,
    ) -> list[dict[str, Any]]:
        ...
