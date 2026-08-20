from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID

from commercial_app.domain.entities.attachment import CommercialAttachment
from commercial_app.domain.ports.attachment_repository_port import AttachmentRepositoryPort
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_COLUMNS = """
    id, owner_type, owner_id, file_name, storage_key, content_type,
    byte_size, uploaded_by_user_id, created_at
"""


def _row(row: dict[str, Any] | None) -> CommercialAttachment | None:
    if not row:
        return None
    return CommercialAttachment(
        id=row["id"],
        owner_type=row["owner_type"],
        owner_id=row["owner_id"],
        file_name=row["file_name"],
        storage_key=row["storage_key"],
        content_type=row["content_type"],
        byte_size=int(row["byte_size"]),
        uploaded_by_user_id=row["uploaded_by_user_id"],
        created_at=row["created_at"],
    )


class PostgresAttachmentRepository(PluginBaseRepository, AttachmentRepositoryPort):
    def list_for_owner(
        self,
        *,
        owner_type: str,
        owner_id: str,
        limit: int = 50,
    ) -> Sequence[CommercialAttachment]:
        rows = self.fetch_all(
            f"""
            SELECT {_COLUMNS}
              FROM commercial.attachments
             WHERE owner_type = %s AND owner_id = %s
             ORDER BY created_at DESC
             LIMIT %s
            """,
            (owner_type, owner_id, max(1, min(limit, 100))),
        )
        return [item for item in (_row(row) for row in rows) if item]

    def count_for_owners(
        self,
        *,
        owner_type: str,
        owner_ids: Sequence[str],
    ) -> dict[str, int]:
        ids = [str(item).strip() for item in owner_ids if str(item).strip()]
        if not ids:
            return {}
        rows = self.fetch_all(
            """
            SELECT owner_id, COUNT(*)::int AS total
              FROM commercial.attachments
             WHERE owner_type = %s AND owner_id = ANY(%s)
             GROUP BY owner_id
            """,
            (owner_type, ids),
        )
        return {str(row["owner_id"]): int(row["total"]) for row in rows}

    def get_by_id(self, attachment_id: UUID) -> CommercialAttachment | None:
        row = self.fetch_one(
            f"""
            SELECT {_COLUMNS}
              FROM commercial.attachments
             WHERE id = %s
            """,
            (str(attachment_id),),
        )
        return _row(row)

    def create(
        self,
        *,
        owner_type: str,
        owner_id: str,
        file_name: str,
        storage_key: str,
        content_type: str,
        byte_size: int,
        uploaded_by_user_id: str,
    ) -> CommercialAttachment:
        # INSERT precisa de execute_returning_one (commit). fetch_one não
        # confirma a transação — arquivo no disco ficava órfão e a strip vazia.
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.attachments (
                owner_type, owner_id, file_name, storage_key,
                content_type, byte_size, uploaded_by_user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING {_COLUMNS}
            """,
            (
                owner_type,
                owner_id,
                file_name,
                storage_key,
                content_type,
                byte_size,
                uploaded_by_user_id,
            ),
        )
        record = _row(row)
        if record is None:
            raise RuntimeError("Falha ao gravar anexo.")
        return record

    def delete(self, attachment_id: UUID) -> CommercialAttachment | None:
        row = self.execute_returning_one(
            f"""
            DELETE FROM commercial.attachments
             WHERE id = %s
         RETURNING {_COLUMNS}
            """,
            (str(attachment_id),),
        )
        return _row(row)
