from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from tm_app.application.security.authorization_policy import (
    AuthorizationDenied,
    TransformometroAuthorizationPolicy,
)
from tm_app.application.helpdesk.ticket_visibility_port import TicketVisibilityPort
from tm_app.domain.entities.interaction_room import (
    LINK_DELETED_EXPLICIT,
    LINK_DELETED_ROOM_DELETED,
    LINK_ENTITY_HELPDESK_TICKET,
    LINK_ENTITY_PROCESS,
    LINK_ROLE_PRIMARY,
    PARTICIPANT_ROLE_MEMBER,
    PARTICIPANT_ROLE_OWNER,
    ROOM_ACCESS_SCOPE_MEMBERS,
    ROOM_ACCESS_SCOPE_OPEN,
    InteractionAttachment,
    InteractionMessage,
    InteractionRoom,
    InteractionRoomLink,
)
from tm_app.domain.ports.interaction_room_repository_port import InteractionRoomRepositoryPort
from tm_app.domain.services.interaction_room_access_service import (
    LINK_STATE_SESSION_MISSING,
    LINK_STATE_UNAVAILABLE,
    LINK_STATE_VISIBLE,
    PrimaryLinkConflict,
    RoomAccessExpansionBlocked,
    RoomAnchorLinkRemovalLocked,
    RoomAuthorizationDenied,
    check_room_access,
    deny_reason_for_state,
    is_externally_governed,
)
from tm_app.domain.services.interaction_room_rules import (
    normalize_entity_key,
    normalize_inbox_filter,
    normalize_link_entity,
    normalize_link_role,
    normalize_mentions,
    normalize_message_content,
    normalize_processo_id,
    normalize_reaction_code,
    normalize_room_title,
    normalize_uuid,
)
from tm_app.domain.services.transformometro_task_rules import normalize_user_id
from tm_app.infrastructure.storage.interaction_attachment_storage import InteractionAttachmentStorage

DEFAULT_MESSAGE_LIMIT = 50
MAX_MESSAGE_LIMIT = 100

logger = logging.getLogger(__name__)


def _actor(user: Any) -> str:
    return normalize_user_id(str(getattr(user, "id", "") or ""), field="Usuário autenticado")


def _limit(value: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = DEFAULT_MESSAGE_LIMIT
    return max(1, min(parsed, MAX_MESSAGE_LIMIT))


class InteractionRoomUseCases:
    """Canonical room use cases — same paths serve HTTP routes and the
    governed TÉO surface. Content authorization is the full intersection:
    Core access + room scope + every active link's external authority.
    Administrative authority (owner/manager) never grants content read.
    """

    def __init__(
        self,
        repo: InteractionRoomRepositoryPort,
        policy: TransformometroAuthorizationPolicy | None = None,
        storage: InteractionAttachmentStorage | None = None,
        ticket_visibility: TicketVisibilityPort | None = None,
        audit: Any | None = None,
    ) -> None:
        self._repo = repo
        self._policy = policy or TransformometroAuthorizationPolicy()
        self._storage = storage
        self._tickets = ticket_visibility
        self._audit = audit

    # --- effective authorization -------------------------------------------

    def _resolve_link_state(
        self, link: InteractionRoomLink, authorization: str | None
    ) -> str:
        """External authority probe for one active link. Fresh per call —
        never cached, never inferred."""
        if link.entity_type == LINK_ENTITY_PROCESS:
            return (
                LINK_STATE_VISIBLE
                if self._repo.process_exists(link.entity_key)
                else "not_found"
            )
        if link.entity_type == LINK_ENTITY_HELPDESK_TICKET:
            if self._tickets is None:
                return LINK_STATE_UNAVAILABLE
            if not authorization:
                return LINK_STATE_SESSION_MISSING
            return self._tickets.check_ticket_visibility(
                authorization, link.entity_key
            )
        return LINK_STATE_UNAVAILABLE

    def _authorized_room(
        self, user: Any, room_id: str, authorization: str | None
    ) -> InteractionRoom:
        """Content path: full intersection enforced before any content or
        sensitive metadata is returned."""
        self._policy.require_access(user)
        room = self._repo.get(normalize_uuid(room_id, label="A sala"))
        if room is None:
            raise LookupError("Sala não encontrada.")
        actor = _actor(user)
        is_participant = any(
            item.user_id == actor for item in room.participants
        )
        check_room_access(
            room,
            is_participant=is_participant,
            resolve_link_state=lambda link: self._resolve_link_state(
                link, authorization
            ),
        )
        return room

    def _admin_room(self, user: Any, room_id: str) -> InteractionRoom:
        """Administrative path: owner or effective `transformometro.manage`.
        Never requires `transformometro.access` and never authorizes
        content reads — administration and reading are separate
        authorities."""
        self._policy._require_user(user)
        room = self._repo.get(normalize_uuid(room_id, label="A sala"))
        if room is None:
            raise LookupError("Sala não encontrada.")
        if self._can_admin(user, room):
            return room
        raise AuthorizationDenied("Sem autoridade administrativa sobre a sala.")

    def _admin_room_raw(self, user: Any, room_id: str) -> InteractionRoom:
        self._policy._require_user(user)
        room = self._repo.get_raw(normalize_uuid(room_id, label="A sala"))
        if room is None:
            raise LookupError("Sala não encontrada.")
        if self._can_admin(user, room):
            return room
        raise AuthorizationDenied("Sem autoridade administrativa sobre a sala.")

    def _can_admin(self, user: Any, room: InteractionRoom) -> bool:
        return (
            room.created_by_user_id == _actor(user)
            or self._policy.has_manage(user)
        )

    def _audit_log(self, action: str, room_id: str, user: Any, **extra: Any) -> None:
        """Best-effort append to the canonical audit trail. An audit
        failure after a committed write is an observability event, not a
        reason to report a false failure — the operation result stands and
        the loss is logged (same convention as gpt_actions._audit)."""
        if self._audit is None:
            return
        try:
            self._audit.log(
                entity_type="interaction_room",
                entity_id=room_id,
                action=action,
                user_id=str(getattr(user, "id", "") or "") or None,
                user_email=str(getattr(user, "email", "") or "") or None,
                user_name=str(getattr(user, "name", "") or "") or None,
                payload=extra or None,
            )
        except Exception as exc:
            logger.warning(
                "interaction_room_audit_failed action=%s room=%s err=%s",
                action,
                room_id,
                exc,
            )

    # --- room lifecycle ------------------------------------------------------

    def open_for_process(
        self, user: Any, processo_id: str, *, authorization: str | None = None
    ) -> InteractionRoom:
        """Legacy process room — unchanged semantics, plus dual-write of the
        primary process link (Expand).

        Order is locate → authorize → mutate: an unauthorized requester
        resolves the canonical room and is denied BEFORE any write — no
        link revival, no room touch, no duplicate (P1 correction)."""
        self._policy.require_access(user)
        actor = _actor(user)
        processo = normalize_processo_id(processo_id)
        # Canonical resolution first: the active primary claim is the source
        # of truth (D-01); a room anchored elsewhere (e.g. a ticket) and
        # later made primary for this process must still be located here.
        room = self._repo.find_active_primary_room(LINK_ENTITY_PROCESS, processo)
        if room is None:
            room = self._repo.get_by_process(processo)
        if room is not None:
            confirmed = self._authorized_room(user, room.id, authorization)
            self._assert_process_link(room.id, processo, actor)
            return confirmed
        try:
            room = self._repo.create_room_graph(
                title=None,
                access_scope=ROOM_ACCESS_SCOPE_OPEN,
                created_by_user_id=actor,
                processo_id=processo,
                links=((LINK_ENTITY_PROCESS, processo, LINK_ROLE_PRIMARY),),
            )
        except PrimaryLinkConflict:
            # Lost the create race — resolve the winner, then authorize.
            winner = self._repo.find_active_primary_room(
                LINK_ENTITY_PROCESS, processo
            ) or self._repo.get_by_process(processo)
            if winner is None:
                raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
            return self._authorized_room(user, winner.id, authorization)
        if room is None:
            raise LookupError("Processo não encontrado.")
        self._audit_log("create", room.id, user, kind="process", processo_id=processo)
        confirmed = self._authorized_room(user, room.id, authorization)
        if confirmed.id != room.id:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def _assert_process_link(
        self, room_id: str, processo: str, actor: str
    ) -> None:
        """Dual-write for the EXPAND era: materialize the primary process
        link when missing, but NEVER resurrect a link the owner removed
        explicitly — explicit removals are honored."""
        existing = next(
            (
                item
                for item in self._repo.list_links(room_id, include_inactive=True)
                if item.entity_type == LINK_ENTITY_PROCESS
                and item.entity_key == processo
            ),
            None,
        )
        if existing is not None and (
            existing.active or existing.deleted_cause == LINK_DELETED_EXPLICIT
        ):
            return
        self._repo.upsert_link(
            room_id=room_id,
            entity_type=LINK_ENTITY_PROCESS,
            entity_key=processo,
            link_role=LINK_ROLE_PRIMARY,
            actor_user_id=actor,
        )
        # Authoritative read-back (5.4): the pre-write snapshot is not
        # proof — the persisted link set must show the revived claim.
        persisted = self._repo.list_links(room_id)
        if not any(
            item.active
            and item.entity_type == LINK_ENTITY_PROCESS
            and item.entity_key == processo
            and item.link_role == LINK_ROLE_PRIMARY
            for item in persisted
        ):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")

    def open_standalone(
        self,
        user: Any,
        title: str,
        *,
        participant_ids: list[str] | None = None,
    ) -> InteractionRoom:
        """Standalone collaboration — always `members` scope (D-03). The
        creator is the owner participant."""
        self._policy.require_access(user)
        actor = _actor(user)
        room = self._repo.create_room_graph(
            title=normalize_room_title(title),
            access_scope=ROOM_ACCESS_SCOPE_MEMBERS,
            created_by_user_id=actor,
            owner_participant=True,
            participant_ids=tuple(
                normalize_user_id(str(member_id), field="O participante")
                for member_id in (participant_ids or [])
            ),
        )
        if room is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        self._audit_log("create", room.id, user, kind="standalone")
        confirmed = self._authorized_room(user, room.id, None)
        if confirmed.access_scope != ROOM_ACCESS_SCOPE_MEMBERS:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def open_for_ticket(
        self, user: Any, ticket_id: str, *, authorization: str | None = None
    ) -> InteractionRoom:
        """`open_or_locate` for a GLPI ticket: returns the room holding the
        active primary claim when the caller satisfies the intersection;
        otherwise creates a `members` room. A ticket the caller cannot
        read can never anchor a room."""
        self._policy.require_access(user)
        actor = _actor(user)
        ticket_key = normalize_entity_key(LINK_ENTITY_HELPDESK_TICKET, ticket_id)
        existing = self._repo.find_active_primary_room(
            LINK_ENTITY_HELPDESK_TICKET, ticket_key
        )
        if existing is not None:
            return self._authorized_room(user, existing.id, authorization)
        link = InteractionRoomLink(
            id="",
            room_id="",
            entity_type=LINK_ENTITY_HELPDESK_TICKET,
            entity_key=ticket_key,
            link_role=LINK_ROLE_PRIMARY,
            created_by_user_id=actor,
        )
        state = self._resolve_link_state(link, authorization)
        if state != LINK_STATE_VISIBLE:
            message, status_code, error_code = deny_reason_for_state(state)
            raise RoomAuthorizationDenied(
                message, status_code=status_code, error_code=error_code
            )
        try:
            # Atomic: room + primary link + owner participant in one
            # transaction; a competing claim rolls everything back (23505).
            room = self._repo.create_room_graph(
                title=None,
                access_scope=ROOM_ACCESS_SCOPE_MEMBERS,
                created_by_user_id=actor,
                links=((LINK_ENTITY_HELPDESK_TICKET, ticket_key, LINK_ROLE_PRIMARY),),
                owner_participant=True,
            )
        except PrimaryLinkConflict:
            # Lost the create race — the transaction left nothing behind;
            # re-resolve to the canonical winner and authorize.
            winner = self._repo.find_active_primary_room(
                LINK_ENTITY_HELPDESK_TICKET, ticket_key
            )
            if winner is None:
                raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
            return self._authorized_room(user, winner.id, authorization)
        if room is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        self._audit_log("create", room.id, user, kind="ticket", ticket=ticket_key)
        return self._authorized_room(user, room.id, authorization)

    # --- links & participants -------------------------------------------------

    def add_link(
        self,
        user: Any,
        room_id: str,
        entity_type: str,
        entity_key: str,
        *,
        link_role: str = "reference",
        authorization: str | None = None,
    ) -> InteractionRoomLink:
        """Owner/manager only. Adding a restrictive link only ever narrows
        the audience — the safe direction — but the target itself must be
        resolvable and visible to the actor."""
        room = self._admin_room(user, room_id)
        actor = _actor(user)
        entity = normalize_link_entity(entity_type)
        key = normalize_entity_key(entity, entity_key)
        role = normalize_link_role(link_role)
        probe = InteractionRoomLink(
            id="",
            room_id=room.id,
            entity_type=entity,
            entity_key=key,
            link_role=role,
            created_by_user_id=actor,
        )
        state = self._resolve_link_state(probe, authorization)
        if state != LINK_STATE_VISIBLE:
            message, status_code, error_code = deny_reason_for_state(state)
            raise RoomAuthorizationDenied(
                message, status_code=status_code, error_code=error_code
            )
        if role == LINK_ROLE_PRIMARY:
            holder = self._repo.find_active_primary_room(entity, key)
            if holder is not None and holder.id != room.id:
                raise PrimaryLinkConflict(
                    "O objeto já possui outra sala primária ativa."
                )
        link = self._repo.upsert_link(
            room_id=room.id,
            entity_type=entity,
            entity_key=key,
            link_role=role,
            actor_user_id=actor,
        )
        self._audit_log(
            "add_link", room.id, user,
            entity_type=entity, entity_key=key, link_role=role,
        )
        confirmed = self._repo.get(room.id)
        if confirmed is None or not any(
            item.active and item.entity_type == entity and item.entity_key == key
            for item in confirmed.links
        ):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return link

    def remove_link(self, user: Any, room_id: str, link_id: str) -> None:
        """Owner/manager may request, never bypass. An externally governed
        link cannot be removed while protected history exists — current or
        future participants would otherwise gain access to an era they
        could not read (no per-message segregation in V2)."""
        room = self._admin_room(user, room_id)
        actor = _actor(user)
        link = next(
            (item for item in room.links if item.id == normalize_uuid(link_id, label="O vínculo")),
            None,
        )
        if link is None or not link.active:
            raise LookupError("Vínculo não encontrado.")
        if (
            link.entity_type == LINK_ENTITY_PROCESS
            and link.link_role == LINK_ROLE_PRIMARY
            and room.processo_id == link.entity_key
        ):
            raise RoomAnchorLinkRemovalLocked(
                "O vínculo primário do processo âncora não pode ser removido nesta versão."
            )
        if is_externally_governed(link):
            # R-1/P0: lock + recount + tombstone in ONE transaction — a
            # concurrent authorized history write cannot slip between the
            # check and the removal (TOCTOU fix).
            tombstoned = self._repo.tombstone_link_guarded(
                room_id=room.id, link_id=link.id, cause=LINK_DELETED_EXPLICIT
            )
        else:
            tombstoned = self._repo.tombstone_link(link.id, cause=LINK_DELETED_EXPLICIT)
        if tombstoned is None or tombstoned.deleted_at is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        self._audit_log(
            "remove_link", room.id, user,
            entity_type=link.entity_type, entity_key=link.entity_key,
        )

    def list_links(
        self, user: Any, room_id: str, *, authorization: str | None = None
    ) -> list[dict[str, Any]]:
        """Active link metadata — content-authorized surface only; entity
        keys are protected context."""
        room = self._authorized_room(user, room_id, authorization)
        return [item.to_dict() for item in room.links]

    def add_participant(self, user: Any, room_id: str, user_id: str) -> None:
        room = self._admin_room(user, room_id)
        actor = _actor(user)
        member = normalize_user_id(str(user_id), field="O participante")
        self._repo.add_participant(
            room_id=room.id,
            user_id=member,
            role=PARTICIPANT_ROLE_MEMBER,
            actor_user_id=actor,
        )
        self._audit_log("add_participant", room.id, user, participant=member)
        if not self._repo.is_participant(room.id, member):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")

    def remove_participant(self, user: Any, room_id: str, user_id: str) -> None:
        """Owner/manager may remove others; any participant may remove
        ONLY themselves (approved contract). The owner can never leave —
        room continuity requires a governed ownership transfer."""
        actor = _actor(user)
        member = normalize_user_id(str(user_id), field="O participante")
        if member == actor:
            # Self-removal: the caller only needs to be a participant —
            # never grants content access, never touches others.
            self._policy._require_user(user)
            room = self._repo.get(normalize_uuid(room_id, label="A sala"))
            if room is None:
                raise LookupError("Sala não encontrada.")
        else:
            room = self._admin_room(user, room_id)
        current = next(
            (item for item in room.participants if item.user_id == member), None
        )
        if current is None:
            raise LookupError("Participante não encontrado.")
        if current.role == PARTICIPANT_ROLE_OWNER:
            raise PermissionError("O owner não pode ser removido da sala.")
        self._repo.remove_participant(room_id=room.id, user_id=member)
        self._audit_log("remove_participant", room.id, user, participant=member)
        if self._repo.is_participant(room.id, member):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")

    def list_participants(
        self, user: Any, room_id: str, *, authorization: str | None = None
    ) -> list[dict[str, Any]]:
        room = self._authorized_room(user, room_id, authorization)
        return [item.to_dict() for item in room.participants]

    # --- governed delete / restore (D-04) -------------------------------------

    def delete_impact(self, user: Any, room_id: str) -> dict[str, Any]:
        """Safe administrative preview — counts and structural metadata
        only. Title, link keys and content never leak to an admin who
        cannot read the room (R-5)."""
        room = self._admin_room_raw(user, room_id)
        return {
            "room_id": room.id,
            "deleted": room.deleted_at is not None,
            "access_scope": room.access_scope,
            "protected_content_count": self._repo.protected_content_count(room.id),
            "participant_count": len(
                [p for p in room.participants if p.removed_at is None]
            ),
            "link_roles": sorted(
                {
                    f"{item.entity_type}:{item.link_role}"
                    for item in room.links
                    if item.active
                }
            ),
            # Opaque structural identifiers (uuids only — no entity_key,
            # no title) so governed transports can run authoritative
            # read-back without content access.
            "active_link_ids": sorted(
                item.id for item in room.links if item.active
            ),
            "participant_user_ids": sorted(
                item.user_id
                for item in room.participants
                if item.removed_at is None
            ),
        }

    def delete_room(self, user: Any, room_id: str) -> InteractionRoom:
        """Logical delete — history persists; primary claims release so a
        new room can claim the objects later (D-04). Owner or effective
        manager; never requires content read."""
        room = self._admin_room(user, room_id)
        actor = _actor(user)
        deleted = self._repo.soft_delete(room.id, actor_user_id=actor)
        if deleted is None or deleted.deleted_at is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        if self._repo.get(room.id) is not None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        if any(link.active for link in deleted.links):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        self._audit_log("delete", room.id, user)
        return deleted

    def restore_room(
        self, user: Any, room_id: str, *, authorization: str | None = None
    ) -> InteractionRoom:
        """Governed restore: fresh admin authz, link targets must still
        exist and be readable, active primary claims must be free.
        Atomic — a conflict aborts the whole transaction, nothing is
        partially revived, explicit link removals are not resurrected."""
        room = self._admin_room_raw(user, room_id)
        if room.deleted_at is None:
            raise ValueError("A sala não está excluída.")
        revivable = [
            item
            for item in room.links
            if item.deleted_cause == LINK_DELETED_ROOM_DELETED
        ]
        for link in revivable:
            state = self._resolve_link_state(link, authorization)
            if state != LINK_STATE_VISIBLE:
                message, status_code, error_code = deny_reason_for_state(state)
                raise RoomAuthorizationDenied(
                    message, status_code=status_code, error_code=error_code
                )
            if link.link_role == LINK_ROLE_PRIMARY:
                holder = self._repo.find_active_primary_room(
                    link.entity_type, link.entity_key
                )
                if holder is not None and holder.id != room.id:
                    raise PrimaryLinkConflict(
                        "O objeto já possui outra sala primária ativa."
                    )
        restored = self._repo.restore_room(room.id)
        if restored is None or restored.deleted_at is not None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        revived = {
            item.id
            for item in restored.links
            if item.active and item.deleted_cause is None
        }
        if any(link.id not in revived for link in revivable):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        self._audit_log("restore", room.id, user)
        return restored

    # --- existing surface ------------------------------------------------------

    def resolve_room_for_object(
        self,
        user: Any,
        entity_type: str,
        entity_key: str,
        *,
        authorization: str | None = None,
    ) -> InteractionRoom:
        """Read-only resolution of the canonical room holding the active
        primary claim for an object — never creates. The process entity
        also honors the legacy anchor (get_or_create fallback source)."""
        self._policy.require_access(user)
        entity = normalize_link_entity(entity_type)
        key = normalize_entity_key(entity, entity_key)
        room = self._repo.find_active_primary_room(entity, key)
        if room is None and entity == LINK_ENTITY_PROCESS:
            room = self._repo.get_by_process(key)
        if room is None:
            raise LookupError("Sala não encontrada.")
        return self._authorized_room(user, room.id, authorization)

    def get_room(
        self, user: Any, room_id: str, *, authorization: str | None = None
    ) -> InteractionRoom:
        return self._authorized_room(user, room_id, authorization)

    def list_rooms(
        self,
        user: Any,
        *,
        inbox_filter: str = "all",
        authorization: str | None = None,
    ) -> list[InteractionRoom]:
        """R-2/Q-09: the inbox only surfaces rooms the viewer is
        effectively authorized for — a room carrying an externally
        governed link is visible only to participants who satisfy the
        full intersection."""
        self._policy.require_access(user)
        actor = _actor(user)
        rooms = self._repo.list_rooms(
            viewer_user_id=actor,
            inbox_filter=normalize_inbox_filter(inbox_filter),
        )
        return [
            room
            for room in rooms
            if self._inbox_visible(room, actor, authorization)
        ]

    def _inbox_visible(
        self, room: InteractionRoom, actor: str, authorization: str | None
    ) -> bool:
        restricted = any(is_externally_governed(link) for link in room.links)
        participant = any(item.user_id == actor for item in room.participants)
        if room.access_scope == ROOM_ACCESS_SCOPE_MEMBERS and not participant:
            return False
        if restricted and not participant:
            return False
        try:
            check_room_access(
                room,
                is_participant=participant,
                resolve_link_state=lambda link: self._resolve_link_state(
                    link, authorization
                ),
            )
        except RoomAuthorizationDenied:
            return False
        return True

    def list_messages(
        self,
        user: Any,
        room_id: str,
        *,
        limit: int = DEFAULT_MESSAGE_LIMIT,
        before_id: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        self._policy.require_access(user)
        room = self._authorized_room(user, room_id, authorization)
        cursor = normalize_uuid(before_id, label="A mensagem âncora") if before_id else None
        messages, has_more = self._repo.list_messages(
            room.id,
            limit=_limit(limit),
            before_id=cursor,
        )
        return {
            "items": [item.to_dict() for item in messages],
            "has_more": has_more,
        }

    def post_message(
        self,
        user: Any,
        room_id: str,
        content: str,
        *,
        parent_id: str | None = None,
        mentions: list[dict] | None = None,
        authorization: str | None = None,
    ) -> InteractionMessage:
        self._policy.require_access(user)
        actor = _actor(user)
        text = normalize_message_content(content)
        room = self._authorized_room(user, room_id, authorization)
        parent = self._parent_in_room(room.id, parent_id)
        created = self._repo.add_message(
            room_id=room.id,
            author_user_id=actor,
            content=text,
            parent_id=parent,
            mentions=normalize_mentions(mentions),
            expected_room=room,
            mark_author_read=True,
        )
        confirmed = self._repo.get_message(created.id)
        if confirmed is None or confirmed.content != text or confirmed.author_user_id != actor:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        if parent and confirmed.parent_id != parent:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def edit_message(
        self,
        user: Any,
        room_id: str,
        message_id: str,
        content: str,
        *,
        authorization: str | None = None,
    ) -> InteractionMessage:
        actor = _actor(user)
        room, message = self._own_message(user, room_id, message_id, actor, authorization)
        if message.deleted_at is not None:
            raise ValueError("A mensagem foi removida.")
        text = normalize_message_content(content)
        updated = self._repo.update_message(
            message_id=message.id, content=text, expected_room=room,
            actor_user_id=actor,
        )
        if updated is None or updated.content != text or updated.edited_at is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return updated

    def delete_message(
        self,
        user: Any,
        room_id: str,
        message_id: str,
        *,
        authorization: str | None = None,
    ) -> InteractionMessage:
        actor = _actor(user)
        room, message = self._own_message(user, room_id, message_id, actor, authorization)
        if message.deleted_at is not None:
            return message
        deleted = self._repo.soft_delete_message(
            message.id, expected_room=room, actor_user_id=actor
        )
        if deleted is None or deleted.deleted_at is None or deleted.to_dict()["content"] != "":
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return deleted

    def toggle_reaction(
        self,
        user: Any,
        room_id: str,
        message_id: str,
        code: str,
        *,
        authorization: str | None = None,
    ) -> InteractionMessage:
        self._policy.require_access(user)
        actor = _actor(user)
        room, message = self._message_in_room(user, room_id, message_id, authorization)
        if message.deleted_at is not None:
            raise ValueError("A mensagem foi removida.")
        normalized = normalize_reaction_code(code)
        had = any(item.user_id == actor and item.code == normalized for item in message.reactions)
        self._repo.toggle_reaction(
            message_id=message.id, user_id=actor, code=normalized,
            expected_room=room,
        )
        confirmed = self._repo.get_message(message.id)
        has = confirmed is not None and any(
            item.user_id == actor and item.code == normalized for item in confirmed.reactions
        )
        if confirmed is None or has == had:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def pin_message(
        self,
        user: Any,
        room_id: str,
        message_id: str,
        *,
        authorization: str | None = None,
    ) -> InteractionMessage:
        self._policy.require_access(user)
        actor = _actor(user)
        room, message = self._message_in_room(user, room_id, message_id, authorization)
        if message.deleted_at is not None:
            raise ValueError("A mensagem foi removida.")
        self._repo.pin_message(
            room_id=message.room_id, message_id=message.id, user_id=actor,
            expected_room=room,
        )
        confirmed = self._repo.get_message(message.id)
        if confirmed is None or not confirmed.pinned:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def unpin_message(
        self,
        user: Any,
        room_id: str,
        message_id: str,
        *,
        authorization: str | None = None,
    ) -> InteractionMessage:
        self._policy.require_access(user)
        room, message = self._message_in_room(user, room_id, message_id, authorization)
        self._repo.unpin_message(
            room_id=message.room_id, message_id=message.id,
            expected_room=room, actor_user_id=_actor(user),
        )
        confirmed = self._repo.get_message(message.id)
        if confirmed is None or confirmed.pinned:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def mark_read(
        self, user: Any, room_id: str, *, authorization: str | None = None
    ) -> None:
        self._policy.require_access(user)
        room = self._authorized_room(user, room_id, authorization)
        self._repo.mark_read(
            room_id=room.id, user_id=_actor(user), expected_room=room
        )

    def get_message(
        self,
        user: Any,
        room_id: str,
        message_id: str,
        *,
        authorization: str | None = None,
    ) -> InteractionMessage:
        _room, message = self._message_in_room(user, room_id, message_id, authorization)
        return message

    def list_attachments(
        self, user: Any, room_id: str, *, authorization: str | None = None
    ) -> list[InteractionAttachment]:
        room = self._authorized_room(user, room_id, authorization)
        return self._repo.list_attachments(room.id)

    def add_attachment(
        self,
        user: Any,
        room_id: str,
        message_id: str,
        *,
        file_name: str,
        content: bytes,
        mime_type: str | None,
        authorization: str | None = None,
    ) -> InteractionAttachment:
        actor = _actor(user)
        room, message = self._own_message(user, room_id, message_id, actor, authorization)
        if message.deleted_at is not None:
            raise ValueError("A mensagem foi removida.")
        stored_name, safe_name = self._files().save(
            room_id=message.room_id,
            original_name=file_name,
            content=content,
            mime_type=mime_type,
        )
        try:
            created = self._repo.add_attachment(
                InteractionAttachment(
                    id=str(uuid4()),
                    message_id=message.id,
                    room_id=message.room_id,
                    file_name=safe_name,
                    content_type=(mime_type or "").split(";")[0].strip().lower(),
                    byte_size=len(content),
                    uploaded_by_user_id=actor,
                    created_at=None,
                    stored_name=stored_name,
                ),
                expected_room=room,
            )
        except Exception:
            # No orphaned bytes: a rejected insert (stale authz, rollback)
            # never leaves a file on disk without a persisted reference.
            orphan = self._files().base_dir / message.room_id / stored_name
            if orphan.is_file():
                orphan.unlink()
            raise
        confirmed = self._repo.get_attachment(created.id)
        if (
            confirmed is None
            or confirmed.message_id != message.id
            or confirmed.file_name != safe_name
            or confirmed.byte_size != len(content)
        ):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return confirmed

    def open_attachment(
        self,
        user: Any,
        room_id: str,
        attachment_id: str,
        *,
        authorization: str | None = None,
    ):
        self._policy.require_access(user)
        room = self._authorized_room(user, room_id, authorization)
        attachment = self._repo.get_attachment(normalize_uuid(attachment_id, label="O anexo"))
        if attachment is None or attachment.room_id != room.id:
            raise LookupError("Arquivo não encontrado.")
        path = self._files().resolve_file(room_id=room.id, stored_name=attachment.stored_name)
        return path, attachment.file_name, attachment.content_type

    def delete_attachment(
        self,
        user: Any,
        room_id: str,
        attachment_id: str,
        *,
        authorization: str | None = None,
    ) -> None:
        actor = _actor(user)
        self._policy.require_access(user)
        room = self._authorized_room(user, room_id, authorization)
        attachment = self._repo.get_attachment(normalize_uuid(attachment_id, label="O anexo"))
        if attachment is None or attachment.room_id != room.id:
            raise LookupError("Arquivo não encontrado.")
        if attachment.uploaded_by_user_id != actor:
            raise PermissionError("Só quem enviou pode remover este arquivo.")
        removed = self._repo.delete_attachment(
            attachment.id, expected_room=room, actor_user_id=actor
        )
        if removed is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        path = self._files().base_dir / room.id / removed.stored_name
        if path.is_file():
            path.unlink()

    def _files(self) -> InteractionAttachmentStorage:
        if self._storage is None:
            self._storage = InteractionAttachmentStorage()
        return self._storage

    def _parent_in_room(self, room_id: str, parent_id: str | None) -> str | None:
        if not parent_id:
            return None
        parent = self._repo.get_message(normalize_uuid(parent_id, label="A mensagem respondida"))
        if parent is None or parent.room_id != room_id or parent.deleted_at is not None:
            raise ValueError("A mensagem respondida não está nesta sala.")
        return parent.id

    def _message_in_room(
        self,
        user: Any,
        room_id: str,
        message_id: str,
        authorization: str | None = None,
    ) -> tuple[InteractionRoom, InteractionMessage]:
        room = self._authorized_room(user, room_id, authorization)
        message = self._repo.get_message(normalize_uuid(message_id, label="A mensagem"))
        if message is None or message.room_id != room.id:
            raise LookupError("Mensagem não encontrada.")
        return room, message

    def _own_message(
        self,
        user: Any,
        room_id: str,
        message_id: str,
        actor: str,
        authorization: str | None = None,
    ) -> tuple[InteractionRoom, InteractionMessage]:
        room, message = self._message_in_room(user, room_id, message_id, authorization)
        if message.author_user_id != actor:
            raise PermissionError("Só o autor pode alterar esta mensagem.")
        return room, message
