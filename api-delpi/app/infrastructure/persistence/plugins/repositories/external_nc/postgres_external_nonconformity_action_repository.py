# app/infrastructure/persistence/plugins/repositories/external_nc/postgres_external_nonconformity_action_repository.py
from __future__ import annotations

from typing import Any, Optional

from app.domain.entities.external_nc.external_nonconformity_action import (
    ExternalNonconformityAction,
)
from app.domain.ports.external_nc.external_nonconformity_action_repository import (
    ExternalNonconformityActionRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresExternalNonconformityActionRepository(
    PluginBaseRepository,
    ExternalNonconformityActionRepositoryPort,
):
    def create(
        self,
        entity: ExternalNonconformityAction,
    ) -> ExternalNonconformityAction:
        row = self.execute_returning_one(
            """
            INSERT INTO quality.external_nc_actions (
                id,
                nonconformity_id,
                root_cause_id,
                action_type,
                title,
                description,
                responsible_user_id,
                responsible_external_name,
                responsible_external_email,
                start_date,
                due_date,
                completed_at,
                status,
                verification_required,
                effectiveness_due_date,
                completion_notes,
                created_by_user_id,
                created_at,
                updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING
                id,
                nonconformity_id,
                root_cause_id,
                action_type,
                title,
                description,
                responsible_user_id,
                responsible_external_name,
                responsible_external_email,
                start_date,
                due_date,
                completed_at,
                status,
                verification_required,
                effectiveness_due_date,
                completion_notes,
                created_by_user_id,
                created_at,
                updated_at
            """,
            (
                entity.id,
                entity.nonconformity_id,
                entity.root_cause_id,
                entity.action_type,
                entity.title,
                entity.description,
                entity.responsible_user_id,
                entity.responsible_external_name,
                entity.responsible_external_email,
                entity.start_date,
                entity.due_date,
                entity.completed_at,
                entity.status,
                entity.verification_required,
                entity.effectiveness_due_date,
                entity.completion_notes,
                entity.created_by_user_id,
                entity.created_at,
                entity.updated_at,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def get_by_id(
        self,
        action_id: str,
    ) -> Optional[ExternalNonconformityAction]:
        row = self.fetch_one(
            """
            SELECT
                id,
                nonconformity_id,
                root_cause_id,
                action_type,
                title,
                description,
                responsible_user_id,
                responsible_external_name,
                responsible_external_email,
                start_date,
                due_date,
                completed_at,
                status,
                verification_required,
                effectiveness_due_date,
                completion_notes,
                created_by_user_id,
                created_at,
                updated_at
            FROM quality.external_nc_actions
            WHERE id = %s
            """,
            (action_id,),
        )
        return self._to_entity(row) if row else None

    def list_by_nonconformity_id(
        self,
        nonconformity_id: str,
    ) -> list[ExternalNonconformityAction]:
        rows = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                root_cause_id,
                action_type,
                title,
                description,
                responsible_user_id,
                responsible_external_name,
                responsible_external_email,
                start_date,
                due_date,
                completed_at,
                status,
                verification_required,
                effectiveness_due_date,
                completion_notes,
                created_by_user_id,
                created_at,
                updated_at
            FROM quality.external_nc_actions
            WHERE nonconformity_id = %s
            ORDER BY created_at ASC
            """,
            (nonconformity_id,),
        )
        return [self._to_entity(row) for row in rows]

    def update(
        self,
        entity: ExternalNonconformityAction,
    ) -> ExternalNonconformityAction:
        row = self.execute_returning_one(
            """
            UPDATE quality.external_nc_actions
               SET root_cause_id = %s,
                   action_type = %s,
                   title = %s,
                   description = %s,
                   responsible_user_id = %s,
                   responsible_external_name = %s,
                   responsible_external_email = %s,
                   start_date = %s,
                   due_date = %s,
                   completed_at = %s,
                   status = %s,
                   verification_required = %s,
                   effectiveness_due_date = %s,
                   completion_notes = %s
             WHERE id = %s
         RETURNING
                id,
                nonconformity_id,
                root_cause_id,
                action_type,
                title,
                description,
                responsible_user_id,
                responsible_external_name,
                responsible_external_email,
                start_date,
                due_date,
                completed_at,
                status,
                verification_required,
                effectiveness_due_date,
                completion_notes,
                created_by_user_id,
                created_at,
                updated_at
            """,
            (
                entity.root_cause_id,
                entity.action_type,
                entity.title,
                entity.description,
                entity.responsible_user_id,
                entity.responsible_external_name,
                entity.responsible_external_email,
                entity.start_date,
                entity.due_date,
                entity.completed_at,
                entity.status,
                entity.verification_required,
                entity.effectiveness_due_date,
                entity.completion_notes,
                entity.id,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def _to_entity(self, row: dict[str, Any]) -> ExternalNonconformityAction:
        return ExternalNonconformityAction(
            id=str(row["id"]),
            nonconformity_id=str(row["nonconformity_id"]),
            root_cause_id=str(row["root_cause_id"]) if row.get("root_cause_id") else None,
            action_type=row["action_type"],
            title=row["title"],
            description=row["description"],
            responsible_user_id=row.get("responsible_user_id"),
            responsible_external_name=row.get("responsible_external_name"),
            responsible_external_email=row.get("responsible_external_email"),
            start_date=row.get("start_date"),
            due_date=row["due_date"],
            completed_at=row.get("completed_at"),
            status=row["status"],
            verification_required=bool(row["verification_required"]),
            effectiveness_due_date=row.get("effectiveness_due_date"),
            completion_notes=row.get("completion_notes"),
            created_by_user_id=row["created_by_user_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )