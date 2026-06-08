from __future__ import annotations

from abc import ABC, abstractmethod


class ChatSkillRepositoryPort(ABC):
    @abstractmethod
    def list_active(self) -> list[dict]:
        raise NotImplementedError
