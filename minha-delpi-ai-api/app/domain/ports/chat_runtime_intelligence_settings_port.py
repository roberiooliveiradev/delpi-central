from __future__ import annotations

from abc import ABC, abstractmethod


class ChatRuntimeIntelligenceSettingsPort(ABC):
    """Overrides administrativos de inteligência (runtime DB), sem depender da application."""

    @abstractmethod
    def web_search_enabled(self) -> bool:
        raise NotImplementedError
