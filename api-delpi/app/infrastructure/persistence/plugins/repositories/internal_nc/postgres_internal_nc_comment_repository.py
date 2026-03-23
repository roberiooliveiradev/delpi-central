# app/infrastructure/persistence/plugins/repositories/internal_nc/postgres_internal_nc_comment_repository.py
from __future__ import annotations

from typing import Any

from app.domain.entities.shared_quality.nonconformity_comment import (
    NonconformityComment,
)
from app.domain.ports.shared_quality.comment_repository import (
    CommentRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresInternalNcCommentRepository(
    PluginBaseRepository,
    CommentRepositoryPort,
):
    def create(self, comment: NonconformityComment) -> NonconformityComment:
        row = self.execute_returning_one(
            """
            INSERT INTO quality.internal_nc_comments (
                id,
                nonconformity_id,
                comment_type,
                content,
                is_internal,
                created_by_user_id,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING
                id,
                nonconformity_id,
                comment_type,
                content,
                is_internal,
                created_by_user_id,
                created_at
            """,
            (
                comment.id,
                comment.nc_id,
                comment.comment_type,
                comment.content,
                comment.is_internal,
                comment.created_by_user_id,
                comment.created_at,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def list_by_nc(self, *, nc_type: str, nc_id: str) -> list[NonconformityComment]:
        rows = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                comment_type,
                content,
                is_internal,
                created_by_user_id,
                created_at
            FROM quality.internal_nc_comments
            WHERE nonconformity_id = %s
            ORDER BY created_at ASC
            """,
            (nc_id,),
        )
        return [self._to_entity(row) for row in rows]

    def _to_entity(self, row: dict[str, Any]) -> NonconformityComment:
        return NonconformityComment(
            id=str(row["id"]),
            nc_type="internal_nonconformity",
            nc_id=str(row["nonconformity_id"]),
            comment_type=row["comment_type"],
            content=row["content"],
            is_internal=bool(row["is_internal"]),
            created_by_user_id=row["created_by_user_id"],
            created_at=row["created_at"],
        )