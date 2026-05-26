from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsChangeRequestRepositoryPort(ABC):
    @abstractmethod
    def list_change_requests(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def create_change_request(
        self,
        *,
        title: str,
        description: str,
        target_block: str,
        proposed_payload: dict,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def add_comment(
        self,
        *,
        change_request_id: str,
        comment_text: str,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def submit_change_request(
        self,
        *,
        change_request_id: str,
        actor_user_id: str | None,
    ) -> dict:
        raise NotImplementedError