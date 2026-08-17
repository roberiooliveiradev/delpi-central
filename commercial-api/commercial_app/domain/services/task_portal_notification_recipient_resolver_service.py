"""Resolve portal notification recipients for commercial tasks."""

from __future__ import annotations

from typing import Sequence

from commercial_app.domain.entities.task import CommercialTask
from commercial_app.domain.ports.commercial_group_repository_port import (
    CommercialGroupRepositoryPort,
)


class TaskPortalNotificationRecipientResolverService:
    def __init__(self, *, groups: CommercialGroupRepositoryPort) -> None:
        self._groups = groups

    def expand_group_member_ids(self, group_ids: Sequence[str]) -> frozenset[str]:
        members: set[str] = set()
        for group_id in group_ids:
            gid = str(group_id or "").strip()
            if not gid:
                continue
            for user_id in self._groups.list_member_user_ids_by_group_id(gid):
                cleaned = str(user_id or "").strip()
                if cleaned:
                    members.add(cleaned)
        return frozenset(members)

    def resolve_interested_user_ids(
        self,
        task: CommercialTask,
        *,
        actor_user_id: str | None = None,
        include_creator: bool = True,
        only_user_ids: Sequence[str] | None = None,
        only_group_ids: Sequence[str] | None = None,
    ) -> frozenset[str]:
        recipients: set[str] = set()
        if only_user_ids is not None or only_group_ids is not None:
            for user_id in only_user_ids or ():
                cleaned = str(user_id or "").strip()
                if cleaned:
                    recipients.add(cleaned)
            recipients |= set(self.expand_group_member_ids(only_group_ids or ()))
        else:
            for user_id in task.resolved_assignee_user_ids():
                cleaned = str(user_id or "").strip()
                if cleaned:
                    recipients.add(cleaned)
            recipients |= set(
                self.expand_group_member_ids(task.resolved_assignee_group_ids())
            )
            if include_creator:
                creator = str(task.created_by_user_id or "").strip()
                if creator:
                    recipients.add(creator)

        actor = str(actor_user_id or "").strip()
        if actor:
            recipients.discard(actor)
        return frozenset(recipients)
