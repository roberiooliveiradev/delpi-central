from __future__ import annotations

from abc import ABC, abstractmethod


class AdminRuntimeSettingsRepositoryPort(ABC):
    @abstractmethod
    def get_json(self, key: str) -> object | None:
        raise NotImplementedError

    @abstractmethod
    def set_json(self, key: str, value: object) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_llm_cost_table(self) -> list[dict] | None:
        raise NotImplementedError

    @abstractmethod
    def save_llm_cost_table(self, entries: list[dict]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_chat_intelligence_settings(self) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def save_chat_intelligence_settings(self, payload: dict) -> None:
        raise NotImplementedError
