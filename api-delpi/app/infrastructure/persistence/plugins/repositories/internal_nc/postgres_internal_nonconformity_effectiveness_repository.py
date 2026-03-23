# app/infrastructure/persistence/plugins/repositories/internal_nc/postgres_internal_nonconformity_effectiveness_repository.py
from __future__ import annotations

from typing import Any, Optional

from app.domain.entities.internal_nc.internal_nonconformity_effectiveness_check import (
    InternalNonconformityEffectivenessCheck,
)
from app.domain.ports.internal_nc.internal_nonconformity_effectiveness_repository import (
    InternalNonconformityEffectivenessRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresInternalNonconformityEffectivenessRepository(
    PluginBaseRepository,
    InternalNonconformityEffectivenessRepositoryPort,
):
    def create(
        self,
        entity: InternalNonconformityEffectivenessCheck,
    ) -> InternalNonconformityEffectivenessCheck:
        row = self.execute_returning_one(
            """
            INSERT INTO quality.internal_nc_effectiveness_checks (
                id,
                nonconformity_id,
                action_id,
                checked_by_user_id,
                checked_at,
                criteria,
                result,
                notes,
                next_action,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING
                id,
                nonconformity_id,
                action_id,
                checked_by_user_id,
                checked_at,
                criteria,
                result,
                notes,
                next_action,
                created_at
            """,
            (
                entity.id,
                entity.nonconformity_id,
                entity.action_id,
                entity.checked_by_user_id,
                entity.checked_at,
                entity.criteria,
                entity.result,
                entity.notes,
                entity.next_action,
                entity.created_at,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def list_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> list[InternalNonconformityEffectivenessCheck]:
        rows = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                action_id,
                checked_by_user_id,
                checked_at,
                criteria,
                result,
                notes,
                next_action,
                created_at
            FROM quality.internal_nc_effectiveness_checks
            WHERE nonconformity_id = %s
            ORDER BY checked_at DESC, created_at DESC
            """,
            (nonconformity_id,),
        )
        return [self._to_entity(row) for row in rows]

    def get_latest_approved_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> Optional[InternalNonconformityEffectivenessCheck]:
        row = self.fetch_one(
            """
            SELECT
                id,
                nonconformity_id,
                action_id,
                checked_by_user_id,
                checked_at,
                criteria,
                result,
                notes,
                next_action,
                created_at
            FROM quality.internal_nc_effectiveness_checks
            WHERE nonconformity_id = %s
              AND result = 'approved'
            ORDER BY checked_at DESC, created_at DESC
            LIMIT 1
            """,
            (nonconformity_id,),
        )
        return self._to_entity(row) if row else None

    def _to_entity(
        self,
        row: dict[str, Any],
    ) -> InternalNonconformityEffectivenessCheck:
        return InternalNonconformityEffectivenessCheck(
            id=str(row["id"]),
            nonconformity_id=str(row["nonconformity_id"]),
            action_id=str(row["action_id"]) if row.get("action_id") else None,
            checked_by_user_id=row["checked_by_user_id"],
            checked_at=row["checked_at"],
            criteria=row["criteria"],
            result=row["result"],
            notes=row.get("notes"),
            next_action=row.get("next_action"),
            created_at=row["created_at"],
        )