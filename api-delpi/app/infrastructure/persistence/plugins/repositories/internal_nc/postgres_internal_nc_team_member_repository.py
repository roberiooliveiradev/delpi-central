# app/infrastructure/persistence/plugins/repositories/internal_nc/postgres_internal_nc_team_member_repository.py
from __future__ import annotations

from typing import Any, Optional

from app.domain.entities.internal_nc.internal_nc_team_member import InternalNcTeamMember
from app.domain.ports.internal_nc.internal_nc_team_member_repository import (
    InternalNcTeamMemberRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository


class PostgresInternalNcTeamMemberRepository(
    PluginBaseRepository,
    InternalNcTeamMemberRepositoryPort,
):
    def create(self, entity: InternalNcTeamMember) -> InternalNcTeamMember:
        row = self.execute_returning_one(
            """
            INSERT INTO quality.internal_nc_team_members (
                id, nonconformity_id, user_id, role_in_case, joined_at
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id, nonconformity_id, user_id, role_in_case, joined_at
            """,
            (
                entity.id,
                entity.nonconformity_id,
                entity.user_id,
                entity.role_in_case,
                entity.joined_at,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def list_by_nonconformity_id(self, nonconformity_id: str) -> list[InternalNcTeamMember]:
        rows = self.fetch_all(
            """
            SELECT id, nonconformity_id, user_id, role_in_case, joined_at
            FROM quality.internal_nc_team_members
            WHERE nonconformity_id = %s
            ORDER BY joined_at ASC
            """,
            (nonconformity_id,),
        )
        return [self._to_entity(row) for row in rows]

    def get_by_nonconformity_and_role(
        self,
        nonconformity_id: str,
        user_id: str,
        role_in_case: str,
    ) -> Optional[InternalNcTeamMember]:
        row = self.fetch_one(
            """
            SELECT id, nonconformity_id, user_id, role_in_case, joined_at
            FROM quality.internal_nc_team_members
            WHERE nonconformity_id = %s
              AND user_id = %s
              AND role_in_case = %s
            """,
            (nonconformity_id, user_id, role_in_case),
        )
        return self._to_entity(row) if row else None

    def delete(self, member_id: str) -> None:
        self.execute(
            "DELETE FROM quality.internal_nc_team_members WHERE id = %s",
            (member_id,),
            auto_commit=True,
        )

    def _to_entity(self, row: dict[str, Any]) -> InternalNcTeamMember:
        return InternalNcTeamMember(
            id=str(row["id"]),
            nonconformity_id=str(row["nonconformity_id"]),
            user_id=row["user_id"],
            role_in_case=row["role_in_case"],
            joined_at=row["joined_at"],
        )