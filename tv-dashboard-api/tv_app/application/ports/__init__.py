"""Application ports for TV Dashboard GPT/write boundaries."""

from __future__ import annotations

from typing import Any, Literal, Protocol
from uuid import UUID

IdempotencyAcquireStatus = Literal["ACQUIRED", "REPLAY", "CONFLICT", "IN_PROGRESS"]


class PresentationRepositoryPort(Protocol):
    """Persistence surface used by presentation writes and GPT read/list."""

    def get_revision(self, playlist_id: UUID) -> int: ...

    def get_by_id(self, playlist_id: UUID) -> dict[str, Any] | None: ...

    def create(
        self, *, name: str, description: str | None, created_by: str | None
    ) -> dict[str, Any]: ...

    def add_slide(
        self,
        playlist_id: UUID,
        payload: dict[str, Any],
        *,
        actor_user_id: str,
        reason: str = "slide_created",
    ) -> dict[str, Any]: ...

    def update_slide(
        self,
        playlist_id: UUID,
        slide_id: UUID,
        payload: dict[str, Any],
        *,
        actor_user_id: str,
        reason: str = "slide_updated",
    ) -> dict[str, Any]: ...

    def delete_slide(
        self,
        playlist_id: UUID,
        slide_id: UUID,
        *,
        actor_user_id: str,
        reason: str = "slide_deleted",
    ) -> None: ...

    def reorder_slides(
        self,
        playlist_id: UUID,
        items: list[dict[str, Any]],
        *,
        actor_user_id: str,
        reason: str = "slides_reordered",
    ) -> list[dict[str, Any]]: ...

    def list_slides(self, playlist_id: UUID) -> list[dict[str, Any]]: ...

    def get_slide(
        self, slide_id: UUID, *, playlist_id: UUID | None = None
    ) -> dict[str, Any]: ...

    def add_section(
        self,
        playlist_id: UUID,
        payload: dict[str, Any],
        *,
        actor_user_id: str,
    ) -> dict[str, Any]: ...

    def update_section(
        self,
        playlist_id: UUID,
        section_id: UUID,
        payload: dict[str, Any],
        *,
        actor_user_id: str,
    ) -> dict[str, Any]: ...

    def delete_section(
        self,
        playlist_id: UUID,
        section_id: UUID,
        *,
        actor_user_id: str,
        delete_slides: bool = False,
    ) -> None: ...

    def reorder_sections(
        self,
        playlist_id: UUID,
        items: list[dict[str, Any]],
        *,
        actor_user_id: str,
    ) -> list[dict[str, Any]]: ...

    def list_sections(self, playlist_id: UUID) -> list[dict[str, Any]]: ...

    def list_playlists(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        user_id: str | None = None,
        include_all: bool = False,
    ) -> list[dict[str, Any]]: ...

    def get_share_role(self, playlist_id: UUID, user_id: str) -> str | None: ...


class IdempotencyAcquireResult:
    __slots__ = ("status", "response_snapshot")

    def __init__(
        self,
        status: IdempotencyAcquireStatus,
        response_snapshot: dict[str, Any] | None = None,
    ) -> None:
        self.status = status
        self.response_snapshot = response_snapshot


class IdempotencyRepositoryPort(Protocol):
    """Atomic idempotency reservation for GPT commit (owner-local)."""

    def acquire(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        operation: str = "gpt_commit_change",
        max_age_hours: int = 24,
    ) -> IdempotencyAcquireResult: ...

    def complete(
        self,
        *,
        key: str,
        actor_user_id: str,
        request_fingerprint: str,
        response_snapshot: dict[str, Any],
        operation: str = "gpt_commit_change",
    ) -> None: ...
