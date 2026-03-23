# app/application/use_cases/internal_nc/list_internal_nc_team_members_use_case.py
from __future__ import annotations

from app.domain.ports.internal_nc.internal_nc_team_member_repository import (
    InternalNcTeamMemberRepositoryPort,
)
from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)


class ListInternalNcTeamMembersUseCase:
    def __init__(
        self,
        nonconformity_repository: InternalNonconformityRepositoryPort,
        team_member_repository: InternalNcTeamMemberRepositoryPort,
    ) -> None:
        self._nonconformity_repository = nonconformity_repository
        self._team_member_repository = team_member_repository

    def execute(self, nonconformity_id: str):
        if not nonconformity_id or not nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        nc = self._nonconformity_repository.get_by_id(nonconformity_id.strip())
        if nc is None:
            raise ValueError("Não conformidade interna não encontrada.")

        return self._team_member_repository.list_by_nonconformity_id(nc.id)