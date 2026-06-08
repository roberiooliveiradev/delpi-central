from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AssistantContentPort(ABC):
    """Contrato para bundles em app/content/pt-BR/assistant/*.json."""

    @abstractmethod
    def load_bundle(self, bundle: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def load_personality_playbook(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def load_stream(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def load_skills_catalog(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def invalidate_cache(self, bundle: str | None = None) -> None:
        raise NotImplementedError
