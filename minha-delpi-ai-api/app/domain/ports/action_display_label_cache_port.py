from __future__ import annotations

from abc import ABC, abstractmethod


class ActionDisplayLabelCachePort(ABC):
    """Runtime cache of LLM-localized action display labels. Not an editable catalog."""

    @abstractmethod
    def get_label(self, cache_key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def put_label(
        self,
        cache_key: str,
        label: str,
        *,
        source: str = "LLM_LOCALIZATION",
    ) -> None:
        raise NotImplementedError
