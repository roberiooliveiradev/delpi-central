from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class ChatSkillRepositoryPort(ABC):
    @abstractmethod
    def list_all(self, *, include_inactive: bool = False) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_active(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, skill_id: UUID) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_key(self, skill_key: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def create(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def update(self, skill_id: UUID, payload: dict) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def deactivate(self, skill_id: UUID) -> bool:
        raise NotImplementedError
