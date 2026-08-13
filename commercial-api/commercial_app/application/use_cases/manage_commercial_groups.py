from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Sequence
from uuid import uuid4

from commercial_app.domain.entities.commercial_group import (
    CommercialGroup,
    CommercialGroupMember,
)
from commercial_app.domain.ports.commercial_group_repository_port import (
    CommercialGroupRepositoryPort,
)
from commercial_app.domain.ports.customer_avatar_repository_port import AuditLogRepositoryPort
from commercial_app.domain.ports.portal_access_port import PortalAccessPort
from commercial_app.domain.services.commercial_groups_messages_content_service import (
    CommercialGroupsMessagesContentService,
)

_ENTITY_COMMERCIAL_GROUP = "commercial_group"
_KIND_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _normalize(value: str | None) -> str:
    return str(value or "").strip()


def _slug_kind_from_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = _KIND_SLUG_RE.sub("_", ascii_name.lower()).strip("_")
    if not slug:
        slug = "group"
    return slug[:48]


def group_to_dict(group: CommercialGroup) -> dict[str, Any]:
    return {
        "id": group.id,
        "kind": group.kind,
        "name": group.name,
        "active": group.active,
        "sort_order": group.sort_order,
        "member_count": group.member_count,
        "members": [{"user_id": member.user_id} for member in group.members],
    }


def group_summary_to_dict(group: CommercialGroup) -> dict[str, Any]:
    """Lightweight shape for roster/profile (no member list)."""
    return {
        "id": group.id,
        "kind": group.kind,
        "name": group.name,
        "active": group.active,
        "sort_order": group.sort_order,
    }


@dataclass(frozen=True, slots=True)
class CreateCommercialGroupRequest:
    name: str
    kind: str | None = None
    sort_order: int = 0
    active: bool = True
    created_by_user_id: str | None = None


class ManageCommercialGroupsUseCase:
    def __init__(
        self,
        repository: CommercialGroupRepositoryPort,
        *,
        audit_repository: AuditLogRepositoryPort | None = None,
        portal_access: PortalAccessPort | None = None,
    ) -> None:
        self._repository = repository
        self._audit = audit_repository
        self._portal_access = portal_access

    def list_groups(self, *, active_only: bool = False) -> list[CommercialGroup]:
        return self._repository.list_groups(active_only=active_only)

    def get_group(self, group_id: str) -> CommercialGroup:
        group = self._repository.get_by_id(_normalize(group_id))
        if group is None:
            raise LookupError(CommercialGroupsMessagesContentService.error("groupNotFound"))
        return group

    def get_group_by_kind(self, kind: str) -> CommercialGroup:
        group = self._repository.get_by_kind(_normalize(kind))
        if group is None:
            raise LookupError(CommercialGroupsMessagesContentService.error("groupNotFound"))
        return group

    def _allocate_kind(self, *, name: str, requested_kind: str | None) -> str:
        base = _normalize(requested_kind) or _slug_kind_from_name(name)
        if not base:
            base = "group"
        candidate = base
        if self._repository.get_by_kind(candidate) is None:
            return candidate
        suffix = uuid4().hex[:8]
        clipped = base[:39].rstrip("_")
        return f"{clipped}_{suffix}"

    def create_group(self, request: CreateCommercialGroupRequest) -> CommercialGroup:
        name = _normalize(request.name)
        if not name:
            raise ValueError(CommercialGroupsMessagesContentService.error("nameRequired"))
        kind = self._allocate_kind(name=name, requested_kind=request.kind)
        group = self._repository.create_group(
            kind=kind,
            name=name,
            sort_order=int(request.sort_order),
            active=bool(request.active),
        )
        self._append_audit(
            actor_user_id=request.created_by_user_id,
            action="commercial_group.create",
            entity_id=group.id,
            payload={"kind": group.kind, "name": group.name},
        )
        return group

    def delete_group(
        self,
        *,
        group_id: str,
        actor_user_id: str | None = None,
    ) -> None:
        gid = _normalize(group_id)
        if not gid:
            raise LookupError(CommercialGroupsMessagesContentService.error("groupNotFound"))
        existing = self._repository.get_by_id(gid)
        if existing is None:
            raise LookupError(CommercialGroupsMessagesContentService.error("groupNotFound"))
        deleted = self._repository.delete_group(gid)
        if not deleted:
            raise LookupError(CommercialGroupsMessagesContentService.error("groupNotFound"))
        self._append_audit(
            actor_user_id=actor_user_id,
            action="commercial_group.delete",
            entity_id=gid,
            payload={"kind": existing.kind, "name": existing.name},
        )

    def replace_members(
        self,
        *,
        group_id: str,
        user_ids: Sequence[str],
        actor_user_id: str | None = None,
    ) -> CommercialGroup:
        gid = _normalize(group_id)
        if not gid:
            raise LookupError(CommercialGroupsMessagesContentService.error("groupNotFound"))
        normalized: list[CommercialGroupMember] = []
        seen: set[str] = set()
        for raw in user_ids:
            uid = _normalize(raw)
            if not uid or uid in seen:
                continue
            seen.add(uid)
            normalized.append(CommercialGroupMember(user_id=uid))
        current = self._repository.get_by_id(gid)
        if current is None:
            raise LookupError(CommercialGroupsMessagesContentService.error("groupNotFound"))
        existing_ids = {member.user_id for member in current.members}
        new_ids = [item.user_id for item in normalized if item.user_id not in existing_ids]
        self._ensure_portal_access(new_ids)
        updated = self._repository.replace_members(group_id=gid, members=normalized)
        if updated is None:
            raise LookupError(CommercialGroupsMessagesContentService.error("groupNotFound"))
        self._append_audit(
            actor_user_id=actor_user_id,
            action="commercial_group.replace_members",
            entity_id=gid,
            payload={"user_ids": [item.user_id for item in normalized]},
        )
        return updated

    def add_member(
        self,
        *,
        group_id: str,
        user_id: str,
        actor_user_id: str | None = None,
    ) -> CommercialGroup:
        gid = _normalize(group_id)
        uid = _normalize(user_id)
        if not uid:
            raise ValueError(CommercialGroupsMessagesContentService.error("userIdRequired"))
        self._ensure_portal_access([uid])
        updated = self._repository.add_member(group_id=gid, user_id=uid)
        if updated is None:
            raise LookupError(CommercialGroupsMessagesContentService.error("groupNotFound"))
        self._append_audit(
            actor_user_id=actor_user_id,
            action="commercial_group.add_member",
            entity_id=gid,
            payload={"user_id": uid},
        )
        return updated

    def remove_member(
        self,
        *,
        group_id: str,
        user_id: str,
        actor_user_id: str | None = None,
    ) -> CommercialGroup:
        gid = _normalize(group_id)
        uid = _normalize(user_id)
        if not uid:
            raise ValueError(CommercialGroupsMessagesContentService.error("userIdRequired"))
        updated = self._repository.remove_member(group_id=gid, user_id=uid)
        if updated is None:
            raise LookupError(CommercialGroupsMessagesContentService.error("groupNotFound"))
        self._append_audit(
            actor_user_id=actor_user_id,
            action="commercial_group.remove_member",
            entity_id=gid,
            payload={"user_id": uid},
        )
        return updated

    def list_member_user_ids_by_group_id(self, group_id: str) -> list[str]:
        """Team-roster hook: filter directory by group membership."""
        return self._repository.list_member_user_ids_by_group_id(_normalize(group_id))

    def list_groups_by_user_id(self, user_id: str) -> list[CommercialGroup]:
        """Profile / roster hook: groups for one user (no nested members)."""
        return self._repository.list_groups_by_user_id(_normalize(user_id))

    def list_memberships_by_user_ids(
        self,
        user_ids: Sequence[str],
    ) -> list[tuple[str, CommercialGroup]]:
        """Team-roster hook: batch (user_id, group) for enrichment."""
        return self._repository.list_memberships_by_user_ids(user_ids)

    def serialize_group(self, group: CommercialGroup) -> dict[str, Any]:
        return group_to_dict(group)

    def serialize_groups(self, groups: Sequence[CommercialGroup]) -> list[dict[str, Any]]:
        return [group_to_dict(item) for item in groups]

    def _ensure_portal_access(self, user_ids: Sequence[str]) -> None:
        if self._portal_access is None:
            return
        access_map = self._portal_access.has_commercial_portal_access_batch(user_ids)
        for uid in user_ids:
            normalized = _normalize(uid)
            if not normalized:
                continue
            if not access_map.get(normalized, False):
                raise ValueError(
                    CommercialGroupsMessagesContentService.error("portalAccessDenied")
                )

    def _append_audit(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        entity_id: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if self._audit is None or not actor_user_id:
            return
        self._audit.append(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=_ENTITY_COMMERCIAL_GROUP,
            entity_id=entity_id,
            payload=payload or {},
        )
