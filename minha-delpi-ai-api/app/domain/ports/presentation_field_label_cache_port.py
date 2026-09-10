from __future__ import annotations

from abc import ABC, abstractmethod


class PresentationFieldLabelCachePort(ABC):
    """Runtime cache of LLM-generated presentation field labels. Not an editable catalog."""

    @abstractmethod
    def get_label(self, field_key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def put_label(
        self,
        field_key: str,
        label: str,
        *,
        source: str = "LLM_LOCALIZATION",
    ) -> None:
        raise NotImplementedError
