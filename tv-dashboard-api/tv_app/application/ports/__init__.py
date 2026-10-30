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
        expected_revision: int | None = None,
    ) -> dict[str, Any]: ...

    def update_slide(
        self,
        playlist_id: UUID,
        slide_id: UUID,
        payload: dict[str, Any],
        *,
        actor_user_id: str,
        reason: str = "slide_updated",
        expected_revision: int | None = None,
    ) -> dict[str, Any]: ...

    def delete_slide(
        self,
        playlist_id: UUID,
        slide_id: UUID,
        *,
        actor_user_id: str,
        reason: str = "slide_deleted",
        expected_revision: int | None = None,
    ) -> None: ...

    def reorder_slides(
        self,
        playlist_id: UUID,
        items: list[dict[str, Any]],
        *,
        actor_user_id: str,
        reason: str = "slides_reordered",
        expected_revision: int | None = None,
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
        expected_revision: int | None = None,
    ) -> dict[str, Any]: ...

    def update_section(
        self,
        playlist_id: UUID,
        section_id: UUID,
        payload: dict[str, Any],
        *,
        actor_user_id: str,
        expected_revision: int | None = None,
    ) -> dict[str, Any]: ...

    def delete_section(
        self,
        playlist_id: UUID,
        section_id: UUID,
        *,
        actor_user_id: str,
        delete_slides: bool = False,
        expected_revision: int | None = None,
    ) -> None: ...

    def reorder_sections(
        self,
        playlist_id: UUID,
        items: list[dict[str, Any]],
        *,
        actor_user_id: str,
        expected_revision: int | None = None,
    ) -> list[dict[str, Any]]: ...

    def list_sections(self, playlist_id: UUID) -> list[dict[str, Any]]: ...

    def update_data_defaults(
        self,
        playlist_id: UUID,
        data_defaults: dict[str, Any],
        *,
        actor_user_id: str,
        reason: str = "playlist_data_defaults",
        expected_revision: int | None = None,
    ) -> dict[str, Any]: ...

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


class VistaConsentChallengeRepositoryPort(Protocol):
    """Consent challenge store for VISTA governed confirms (D-5).

    Lifecycle PENDING → APPROVED → CONSUMED | EXPIRED | REVOKED; each
    row is bound to actor + proposal + sealed plan hash + target ref.
    """

    def issue_for_proposal(
        self,
        *,
        proposal_id: str,
        actor_sub: str,
        plan_hash: str,
        target_ref: str,
        action: str,
        origin: str,
        expires_at: Any,
        correlation_id: str | None = None,
    ) -> dict | None: ...

    def get_by_id(self, *, challenge_id: str) -> dict | None: ...

    def latest_for_proposal(self, *, proposal_id: str) -> dict | None: ...

    def approve(
        self,
        *,
        challenge_id: str,
        actor_sub: str,
        plan_hash: str,
        token_jti: str | None,
        token_iat: Any,
        consent_record: dict,
    ) -> dict | None: ...

    def consume_approved(
        self, *, challenge_id: str, proposal_id: str, actor_sub: str
    ) -> dict | None: ...
