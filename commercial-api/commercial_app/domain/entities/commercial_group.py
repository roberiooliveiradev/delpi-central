from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommercialGroupMember:
    user_id: str


@dataclass(frozen=True, slots=True)
class CommercialGroup:
    id: str
    kind: str
    name: str
    active: bool
    sort_order: int
    members: tuple[CommercialGroupMember, ...] = ()

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def member_user_ids(self) -> tuple[str, ...]:
        return tuple(member.user_id for member in self.members)
