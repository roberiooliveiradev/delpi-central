from __future__ import annotations

from abc import ABC, abstractmethod


class ChatQualityIssueRepositoryPort(ABC):
    @abstractmethod
    def find_open_by_code(self, code: str, *, within_days: int = 7) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        *,
        code: str,
        title: str,
        description: str,
        source: str,
        metadata: dict | None = None,
        external_url: str | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_issues(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def update_status(self, issue_id: int, *, status: str) -> dict | None:
        raise NotImplementedError
