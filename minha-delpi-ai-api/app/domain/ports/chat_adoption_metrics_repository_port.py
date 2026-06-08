from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class ChatAdoptionMetricsRepositoryPort(ABC):
    @abstractmethod
    def count_audit_action(self, action: str, *, since: datetime) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_audit_actions(self, actions: tuple[str, ...], *, since: datetime) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_active_sessions(self, *, since: datetime) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_active_users(self, *, since: datetime) -> int:
        raise NotImplementedError
