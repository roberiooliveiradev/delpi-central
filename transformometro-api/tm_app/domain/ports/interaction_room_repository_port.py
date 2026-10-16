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
    def get_by_process(self, processo_id: str) -> InteractionRoom | None:
        """Read-only legacy locate by ``rooms.processo_id`` — never writes."""
        ...

    def get(self, room_id: str) -> InteractionRoom | None: ...

    def get_raw(self, room_id: str) -> InteractionRoom | None:
        """Room in any lifecycle state (incl. soft-deleted) with all links —
        administrative paths only, never for content reads."""
        ...

    def create_room_graph(
        self,
        *,
        title: str | None,
        access_scope: str,
        created_by_user_id: str,
        processo_id: str | None = None,
        links: tuple[tuple[str, str, str], ...] = (),
        owner_participant: bool = False,
        participant_ids: tuple[str, ...] = (),
    ) -> InteractionRoom | None:
        """Atomic creation: room + links + participants in ONE transaction.
        ``links`` items are ``(entity_type, entity_key, link_role)``; an
        occupied active primary claim raises ``PrimaryLinkConflict`` and the
        whole graph rolls back — no orphan room. Returns None when the
        ``processo_id`` target does not exist."""
        ...

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

    def tombstone_link_guarded(
        self, *, room_id: str, link_id: str, cause: str
    ) -> InteractionRoomLink | None:
        """Atomic removal for externally governed links (R-1/P0): the
        room row is locked FOR UPDATE, protected content is re-counted
        INSIDE the lock, and the tombstone commits in the same
        transaction. A concurrent authorized history write either lands
        before the recount (→ ``RoomAccessExpansionBlocked``) or after
        the commit — never in between. Returns None when the link is not
        active."""
        ...

    # Every write above and every mutation of authorizing state (link
    # upsert/tombstone, participant add/remove, room tombstone/restore)
    # serializes on the same single-row room lock — consistent ordering,
    # one lock per transaction, no deadlock shape.
    #
    # ``expected_room`` is the snapshot the caller authorized against
    # (``repo.get`` output). When supplied, the writer re-validates it
    # UNDER the room lock before writing: room still active, same
    # access_scope, identical active-link set, and the actor's
    # participation intact when the snapshot included it. Any drift
    # raises ``StaleRoomAuthorization`` — the authorization taken over a
    # different context must never persist content (stale-authz fix).

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
        """Every persisted artifact tied to the room: messages INCLUDING
        tombstones, attachments, mentions, reactions, pins and read
        markers. Used by the expansion rule — a visible-only count is not
        proof of empty history (R-1, block on doubt)."""
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
        expected_room: InteractionRoom | None = None,
        mark_author_read: bool = False,
    ) -> InteractionMessage: ...

    def get_message(self, message_id: str) -> InteractionMessage | None: ...

    def update_message(
        self, *, message_id: str, content: str,
        expected_room: InteractionRoom | None = None,
    ) -> InteractionMessage | None: ...

    def soft_delete_message(
        self, message_id: str, *, expected_room: InteractionRoom | None = None
    ) -> InteractionMessage | None: ...

    def toggle_reaction(
        self, *, message_id: str, user_id: str, code: str,
        expected_room: InteractionRoom | None = None,
    ) -> None: ...

    def pin_message(
        self, *, room_id: str, message_id: str, user_id: str,
        expected_room: InteractionRoom | None = None,
    ) -> None: ...

    def unpin_message(
        self, *, room_id: str, message_id: str,
        expected_room: InteractionRoom | None = None,
    ) -> None: ...

    def mark_read(
        self, *, room_id: str, user_id: str,
        expected_room: InteractionRoom | None = None,
    ) -> None: ...

    def add_attachment(
        self, attachment: InteractionAttachment,
        *, expected_room: InteractionRoom | None = None,
    ) -> InteractionAttachment: ...

    def get_attachment(self, attachment_id: str) -> InteractionAttachment | None: ...

    def delete_attachment(
        self, attachment_id: str, *, expected_room: InteractionRoom | None = None
    ) -> InteractionAttachment | None: ...

    def list_attachments(self, room_id: str) -> list[InteractionAttachment]: ...
