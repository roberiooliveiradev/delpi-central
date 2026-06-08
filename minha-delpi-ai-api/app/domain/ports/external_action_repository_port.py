from __future__ import annotations

from abc import ABC, abstractmethod


class ExternalActionRepositoryPort(ABC):
    @abstractmethod
    def list_actions(self, provider_key: str | None = None) -> list[dict]:
        raise NotImplementedError
