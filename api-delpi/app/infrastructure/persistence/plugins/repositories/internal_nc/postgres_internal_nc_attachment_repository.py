# app/infrastructure/persistence/plugins/repositories/internal_nc/postgres_internal_nc_attachment_repository.py
from __future__ import annotations

from typing import Any

from app.domain.entities.shared_quality.nonconformity_attachment import (
    NonconformityAttachment,
)
from app.domain.ports.shared_quality.attachment_repository import (
    AttachmentRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresInternalNcAttachmentRepository(
    PluginBaseRepository,
    AttachmentRepositoryPort,
):
    def create(self, attachment: NonconformityAttachment) -> NonconformityAttachment:
        row = self.execute_returning_one(
            """
            INSERT INTO quality.internal_nc_attachments (
                id,
                nonconformity_id,
                action_id,
                effectiveness_check_id,
                file_name,
                original_name,
                mime_type,
                size_bytes,
                storage_provider,
                storage_path,
                checksum,
                uploaded_by_user_id,
                uploaded_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING
                id,
                nonconformity_id,
                action_id,
                effectiveness_check_id,
                file_name,
                original_name,
                mime_type,
                size_bytes,
                storage_provider,
                storage_path,
                checksum,
                uploaded_by_user_id,
                uploaded_at
            """,
            (
                attachment.id,
                attachment.nc_id,
                attachment.action_id,
                attachment.effectiveness_check_id,
                attachment.file_name,
                attachment.original_name,
                attachment.mime_type,
                attachment.size_bytes,
                attachment.storage_provider,
                attachment.storage_path,
                attachment.checksum,
                attachment.uploaded_by_user_id,
                attachment.uploaded_at,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def _to_entity(self, row: dict[str, Any]) -> NonconformityAttachment:
        return NonconformityAttachment(
            id=str(row["id"]),
            nc_type="internal_nonconformity" if row.get("nonconformity_id") else None,
            nc_id=str(row["nonconformity_id"]) if row.get("nonconformity_id") else None,
            action_id=str(row["action_id"]) if row.get("action_id") else None,
            effectiveness_check_id=(
                str(row["effectiveness_check_id"])
                if row.get("effectiveness_check_id")
                else None
            ),
            file_name=row["file_name"],
            original_name=row["original_name"],
            mime_type=row.get("mime_type"),
            size_bytes=int(row["size_bytes"]),
            storage_provider=row["storage_provider"],
            storage_path=row["storage_path"],
            checksum=row.get("checksum"),
            uploaded_by_user_id=row["uploaded_by_user_id"],
            uploaded_at=row["uploaded_at"],
        )