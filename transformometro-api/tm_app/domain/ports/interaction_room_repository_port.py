from __future__ import annotations

from typing import Protocol

from tm_app.domain.entities.interaction_room import (
    InteractionAttachment,
    InteractionMessage,
    InteractionRoom,
    InteractionRoomLink,
    InteractionRoomParticipant,
)


class InteractionRoomRepositoryPort(Protocol):
    def get_or_create(self, *, processo_id: str, created_by_user_id: str) -> InteractionRoom | None: ...

    def get(self, room_id: str) -> InteractionRoom | None: ...

    def get_raw(self, room_id: str) -> InteractionRoom | None:
        """Room in any lifecycle state (incl. soft-deleted) with all links —
        administrative paths only, never for content reads."""
        ...

    def create_room(
        self,
        *,
        title: str | None,
        access_scope: str,
        created_by_user_id: str,
        processo_id: str | None = None,
    ) -> InteractionRoom | None: ...

    def soft_delete(
        self, room_id: str, *, actor_user_id: str | None = None
    ) -> InteractionRoom | None: ...

    def restore_room(self, room_id: str) -> InteractionRoom | None:
        """Atomically clears the tombstone and revives links inactivated by
        ``room_deleted``. Raises ``PrimaryLinkConflict`` when an active
        primary claim is already held by another room."""
        ...

    # --- typed links --------------------------------------------------------

    def list_links(
        self, room_id: str, *, include_inactive: bool = False
    ) -> list[InteractionRoomLink]: ...

    def find_active_primary_room(
        self, entity_type: str, entity_key: str
    ) -> InteractionRoom | None:
        """The room currently holding the active primary claim for the
        object, or None. At most one exists — enforced by the partial
        unique index."""
        ...

    def upsert_link(
        self,
        *,
        room_id: str,
        entity_type: str,
        entity_key: str,
        link_role: str,
        actor_user_id: str,
    ) -> InteractionRoomLink:
        """Insert or revive the tombstoned link row (no duplicate rows)."""
        ...

    def tombstone_link(self, link_id: str, *, cause: str) -> InteractionRoomLink | None: ...

    # --- participants -------------------------------------------------------

    def is_participant(self, room_id: str, user_id: str) -> bool: ...

    def add_participant(
        self, *, room_id: str, user_id: str, role: str, actor_user_id: str
    ) -> InteractionRoomParticipant: ...

    def remove_participant(self, *, room_id: str, user_id: str) -> None: ...

    def list_participants(
        self, room_id: str, *, active_only: bool = True
    ) -> list[InteractionRoomParticipant]: ...

    # --- authorization support ----------------------------------------------

    def protected_content_count(self, room_id: str) -> int:
        """All persisted room content — messages INCLUDING tombstones,
        attachments, reactions, mentions. Used by the expansion rule; a
        visible-only count is not proof of empty history."""
        ...

    def process_exists(self, processo_id: str) -> bool: ...

    def list_rooms(
        self,
        *,
        viewer_user_id: str | None = None,
        inbox_filter: str = "all",
    ) -> list[InteractionRoom]: ...

    def list_messages(
        self,
        room_id: str,
        *,
        limit: int,
        before_id: str | None = None,
    ) -> tuple[list[InteractionMessage], bool]: ...

    def add_message(
        self,
        *,
        room_id: str,
        author_user_id: str,
        content: str,
        parent_id: str | None = None,
        mentions: tuple[tuple[str, str], ...] = (),
    ) -> InteractionMessage: ...

    def get_message(self, message_id: str) -> InteractionMessage | None: ...

    def update_message(self, *, message_id: str, content: str) -> InteractionMessage | None: ...

    def soft_delete_message(self, message_id: str) -> InteractionMessage | None: ...

    def toggle_reaction(self, *, message_id: str, user_id: str, code: str) -> None: ...

    def pin_message(self, *, room_id: str, message_id: str, user_id: str) -> None: ...

    def unpin_message(self, *, room_id: str, message_id: str) -> None: ...

    def mark_read(self, *, room_id: str, user_id: str) -> None: ...

    def add_attachment(self, attachment: InteractionAttachment) -> InteractionAttachment: ...

    def get_attachment(self, attachment_id: str) -> InteractionAttachment | None: ...

    def delete_attachment(self, attachment_id: str) -> InteractionAttachment | None: ...

    def list_attachments(self, room_id: str) -> list[InteractionAttachment]: ...
