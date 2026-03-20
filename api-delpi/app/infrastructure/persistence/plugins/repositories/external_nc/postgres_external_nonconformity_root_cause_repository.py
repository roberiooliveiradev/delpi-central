# app/infrastructure/persistence/plugins/repositories/external_nc/postgres_external_nonconformity_root_cause_repository.py
from __future__ import annotations

from typing import Any

from app.domain.entities.external_nc.external_nonconformity_root_cause import (
    ExternalNonconformityRootCause,
)
from app.domain.ports.external_nc.external_nonconformity_root_cause_repository import (
    ExternalNonconformityRootCauseRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresExternalNonconformityRootCauseRepository(
    PluginBaseRepository,
    ExternalNonconformityRootCauseRepositoryPort,
):
    def create(
        self,
        entity: ExternalNonconformityRootCause,
    ) -> ExternalNonconformityRootCause:
        row = self.execute_returning_one(
            """
            INSERT INTO quality.external_nc_root_causes (
                id,
                nonconformity_id,
                analysis_method,
                cause_dimension,
                category,
                why_level,
                description,
                is_root_cause,
                created_by_user_id,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING
                id,
                nonconformity_id,
                analysis_method,
                cause_dimension,
                category,
                why_level,
                description,
                is_root_cause,
                created_by_user_id,
                created_at
            """,
            (
                entity.id,
                entity.nonconformity_id,
                entity.analysis_method,
                entity.cause_dimension,
                entity.category,
                entity.why_level,
                entity.description,
                entity.is_root_cause,
                entity.created_by_user_id,
                entity.created_at,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def list_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> list[ExternalNonconformityRootCause]:
        rows = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                analysis_method,
                cause_dimension,
                category,
                why_level,
                description,
                is_root_cause,
                created_by_user_id,
                created_at
            FROM quality.external_nc_root_causes
            WHERE nonconformity_id = %s
            ORDER BY
                is_root_cause DESC,
                created_at ASC
            """,
            (nonconformity_id,),
        )
        return [self._to_entity(row) for row in rows]

    def exists_for_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> bool:
        row = self.fetch_one(
            """
            SELECT EXISTS (
                SELECT 1
                FROM quality.external_nc_root_causes
                WHERE nonconformity_id = %s
            ) AS exists_flag
            """,
            (nonconformity_id,),
        )
        return bool(row and row["exists_flag"])

    def _to_entity(
        self,
        row: dict[str, Any],
    ) -> ExternalNonconformityRootCause:
        return ExternalNonconformityRootCause(
            id=str(row["id"]),
            nonconformity_id=str(row["nonconformity_id"]),
            analysis_method=row.get("analysis_method"),
            cause_dimension=row.get("cause_dimension"),
            category=row.get("category"),
            why_level=row.get("why_level"),
            description=row["description"],
            is_root_cause=bool(row["is_root_cause"]),
            created_by_user_id=row["created_by_user_id"],
            created_at=row["created_at"],
        )