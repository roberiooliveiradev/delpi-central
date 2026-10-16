"""Effective-access rules for interaction rooms (V2 intersection).

Pure decision logic — no IO. The use case resolves each active link
through the owning authority (process existence, Helpdesk BFF ticket
visibility) and feeds the outcomes here.

Invariant: ``link_role`` (primary/reference) is never a security class;
every active link participates in the intersection. A link whose target
cannot be proven visible fails closed — restricted, missing and
unavailable all deny.
"""

from __future__ import annotations

from tm_app.domain.entities.interaction_room import (
    LINK_ENTITY_HELPDESK_TICKET,
    ROOM_ACCESS_SCOPE_MEMBERS,
    InteractionRoom,
    InteractionRoomLink,
)

# Entity types whose visibility is governed by an authority outside the
# Transformômetro. Removing one of these links can widen the audience of
# protected history — see the expansion rule in the use case.
EXTERNALLY_GOVERNED_ENTITY_TYPES = frozenset({LINK_ENTITY_HELPDESK_TICKET})

LINK_STATE_VISIBLE = "visible"
LINK_STATE_RESTRICTED = "restricted"
LINK_STATE_NOT_FOUND = "not_found"
LINK_STATE_SESSION_MISSING = "session_missing"
LINK_STATE_UNAVAILABLE = "unavailable"


class RoomAuthorizationDenied(PermissionError):
    """Content access denied by room scope or link intersection.

    ``status_code`` mirrors the transport contract: hidden for
    restricted/missing targets (no existence oracle), 503 when the
    external authority could not be evaluated (fail closed, retryable).
    """

    def __init__(self, message: str, *, status_code: int, error_code: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class RoomAccessExpansionBlocked(PermissionError):
    """Removing this link would widen the audience of protected history
    for current OR future users. No per-message segregation exists in V2,
    so the only provably safe outcomes are: keep the link or archive the
    room."""

    error_code = "room_access_expansion_blocked"
    status_code = 409


class PrimaryLinkConflict(RuntimeError):
    """The object already has an active primary room owned by another
    room. Atomic operations never partially apply."""

    error_code = "primary_link_conflict"
    status_code = 409


def is_externally_governed(link: InteractionRoomLink) -> bool:
    return link.entity_type in EXTERNALLY_GOVERNED_ENTITY_TYPES


def deny_reason_for_state(link_state: str) -> tuple[str, int, str]:
    """(message, status_code, error_code) for a non-visible link state."""
    if link_state == LINK_STATE_UNAVAILABLE:
        return (
            "Não foi possível validar um objeto vinculado à sala.",
            503,
            "upstream_unavailable",
        )
    if link_state == LINK_STATE_SESSION_MISSING:
        return (
            "Sala vinculada a objeto que exige sessão externa vinculada.",
            403,
            "glpi_link_required",
        )
    return ("Sala não encontrada.", 404, "not_found")


def check_room_access(
    room: InteractionRoom,
    *,
    is_participant: bool,
    resolve_link_state,
) -> None:
    """Enforce scope + full link intersection. Raises RoomAuthorizationDenied.

    ``resolve_link_state(link) -> LINK_STATE_*`` performs the external
    authority check and is supplied by the application layer.
    """
    if room.access_scope == ROOM_ACCESS_SCOPE_MEMBERS and not is_participant:
        raise RoomAuthorizationDenied(
            "Sala não encontrada.", status_code=404, error_code="not_found"
        )
    for link in room.links:
        if not link.active:
            continue
        link_state = resolve_link_state(link)
        if link_state != LINK_STATE_VISIBLE:
            message, status_code, error_code = deny_reason_for_state(link_state)
            raise RoomAuthorizationDenied(
                message, status_code=status_code, error_code=error_code
            )
