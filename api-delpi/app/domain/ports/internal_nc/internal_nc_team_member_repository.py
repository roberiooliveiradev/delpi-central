# app/domain/ports/internal_nc/internal_nc_team_member_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.internal_nc.internal_nc_team_member import (
    InternalNcTeamMember,
)


class InternalNcTeamMemberRepositoryPort(ABC):
    @abstractmethod
    def create(self, entity: InternalNcTeamMember) -> InternalNcTeamMember:
        raise NotImplementedError

    @abstractmethod
    def list_by_nonconformity_id(self, nonconformity_id: str) -> list[InternalNcTeamMember]:
        raise NotImplementedError

    @abstractmethod
    def get_by_nonconformity_and_role(
        self,
        nonconformity_id: str,
        user_id: str,
        role_in_case: str,
    ) -> Optional[InternalNcTeamMember]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, member_id: str) -> None:
        raise NotImplementedError