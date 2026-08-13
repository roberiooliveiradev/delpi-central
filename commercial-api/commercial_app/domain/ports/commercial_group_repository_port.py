from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from commercial_app.domain.entities.commercial_group import (
    CommercialGroup,
    CommercialGroupMember,
)


class CommercialGroupRepositoryPort(ABC):
    @abstractmethod
    def get_by_id(self, group_id: str) -> CommercialGroup | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_kind(self, kind: str) -> CommercialGroup | None:
        raise NotImplementedError

    @abstractmethod
    def list_groups(self, *, active_only: bool = False) -> list[CommercialGroup]:
        raise NotImplementedError

    @abstractmethod
    def create_group(
        self,
        *,
        kind: str,
        name: str,
        sort_order: int = 0,
        active: bool = True,
    ) -> CommercialGroup:
        raise NotImplementedError

    @abstractmethod
    def delete_group(self, group_id: str) -> bool:
        """Hard-delete group (members cascade). False if missing."""
        raise NotImplementedError

    @abstractmethod
    def replace_members(
        self,
        *,
        group_id: str,
        members: Sequence[CommercialGroupMember],
    ) -> CommercialGroup | None:
        raise NotImplementedError

    @abstractmethod
    def add_member(
        self,
        *,
        group_id: str,
        user_id: str,
    ) -> CommercialGroup | None:
        raise NotImplementedError

    @abstractmethod
    def remove_member(
        self,
        *,
        group_id: str,
        user_id: str,
    ) -> CommercialGroup | None:
        raise NotImplementedError

    @abstractmethod
    def list_member_user_ids_by_group_id(self, group_id: str) -> list[str]:
        """Hook for team-roster filter by group_id."""
        raise NotImplementedError

    @abstractmethod
    def list_groups_by_user_id(self, user_id: str) -> list[CommercialGroup]:
        """Hook for profile groups[] / roster enrichment."""
        raise NotImplementedError

    @abstractmethod
    def list_memberships_by_user_ids(
        self,
        user_ids: Sequence[str],
    ) -> list[tuple[str, CommercialGroup]]:
        """
        Hook for team-roster batch join.

        Returns (user_id, group) for each membership of the given users.
        Groups are hydrated without member lists (roster only needs kind/name).
        """
        raise NotImplementedError
