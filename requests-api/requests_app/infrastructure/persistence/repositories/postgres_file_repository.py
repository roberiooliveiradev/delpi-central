from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from requests_app.domain.entities.files import (
    RequestArtifact,
    RequestAttachment,
    RequestComment,
    RequestEvent,
)
from requests_app.domain.ports.file_repository_port import FileRepositoryPort
from requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

_SCHEMA = "my_requests"


def _attachment(row: dict[str, Any]) -> RequestAttachment:
    return RequestAttachment(
        id=row["id"],
        request_id=row["request_id"],
        original_name=row["original_name"],
        stored_name=row["stored_name"],
        storage_key=row["storage_key"],
        mime_type=row["mime_type"],
        size_bytes=int(row["size_bytes"]),
        checksum_sha256=row["checksum_sha256"],
        created_by_user_id=row["created_by_user_id"],
        created_by_name=row["created_by_name"],
        created_at=row.get("created_at"),
    )


def _artifact(row: dict[str, Any]) -> RequestArtifact:
    metadata = row.get("metadata") or {}
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    return RequestArtifact(
        id=row["id"],
        request_id=row["request_id"],
        artifact_kind=row["artifact_kind"],
        original_name=row["original_name"],
        stored_name=row["stored_name"],
        storage_key=row["storage_key"],
        mime_type=row["mime_type"],
        size_bytes=int(row["size_bytes"]),
        checksum_sha256=row["checksum_sha256"],
        produced_by_user_id=row["produced_by_user_id"],
        produced_by_name=row["produced_by_name"],
        metadata=metadata if isinstance(metadata, dict) else {},
        created_at=row.get("created_at"),
    )


def _event(row: dict[str, Any]) -> RequestEvent:
    payload = row.get("payload") or {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    return RequestEvent(
        id=row["id"],
        request_id=row["request_id"],
        event_type=row["event_type"],
        actor_user_id=row.get("actor_user_id"),
        actor_name=row.get("actor_name"),
        payload=payload if isinstance(payload, dict) else {},
        created_at=row.get("created_at"),
    )


def _comment(row: dict[str, Any]) -> RequestComment:
    return RequestComment(
        id=row["id"],
        request_id=row["request_id"],
        author_user_id=row["author_user_id"],
        author_name=row["author_name"],
        body=row["body"],
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


class PostgresFileRepository(FileRepositoryPort):
    def create_attachment(self, attachment: RequestAttachment) -> RequestAttachment:
        sql = f"""
        INSERT INTO {_SCHEMA}.request_attachments (
            id, request_id, original_name, stored_name, storage_key,
            mime_type, size_bytes, checksum_sha256,
            created_by_user_id, created_by_name
        ) VALUES (
            %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING *
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        str(attachment.id),
                        str(attachment.request_id),
                        attachment.original_name,
                        attachment.stored_name,
                        attachment.storage_key,
                        attachment.mime_type,
                        attachment.size_bytes,
                        attachment.checksum_sha256,
                        attachment.created_by_user_id,
                        attachment.created_by_name,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _attachment(dict(row))

    def get_attachment(self, attachment_id: UUID | str) -> RequestAttachment | None:
        sql = f"SELECT * FROM {_SCHEMA}.request_attachments WHERE id = %s::uuid"
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (str(attachment_id),))
                row = cur.fetchone()
        return _attachment(dict(row)) if row else None

    def list_attachments(self, request_id: UUID | str) -> list[RequestAttachment]:
        sql = f"""
        SELECT * FROM {_SCHEMA}.request_attachments
        WHERE request_id = %s::uuid
        ORDER BY created_at DESC
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (str(request_id),))
                rows = cur.fetchall()
        return [_attachment(dict(row)) for row in rows]

    def create_artifact(self, artifact: RequestArtifact) -> RequestArtifact:
        sql = f"""
        INSERT INTO {_SCHEMA}.request_artifacts (
            id, request_id, artifact_kind, original_name, stored_name, storage_key,
            mime_type, size_bytes, checksum_sha256,
            produced_by_user_id, produced_by_name, metadata
        ) VALUES (
            %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING *
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        str(artifact.id),
                        str(artifact.request_id),
                        artifact.artifact_kind,
                        artifact.original_name,
                        artifact.stored_name,
                        artifact.storage_key,
                        artifact.mime_type,
                        artifact.size_bytes,
                        artifact.checksum_sha256,
                        artifact.produced_by_user_id,
                        artifact.produced_by_name,
                        Jsonb(artifact.metadata or {}),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _artifact(dict(row))

    def get_artifact(self, artifact_id: UUID | str) -> RequestArtifact | None:
        sql = f"SELECT * FROM {_SCHEMA}.request_artifacts WHERE id = %s::uuid"
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (str(artifact_id),))
                row = cur.fetchone()
        return _artifact(dict(row)) if row else None

    def list_artifacts(self, request_id: UUID | str) -> list[RequestArtifact]:
        sql = f"""
        SELECT * FROM {_SCHEMA}.request_artifacts
        WHERE request_id = %s::uuid
        ORDER BY created_at DESC
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (str(request_id),))
                rows = cur.fetchall()
        return [_artifact(dict(row)) for row in rows]

    def append_event(self, event: RequestEvent) -> RequestEvent:
        sql = f"""
        INSERT INTO {_SCHEMA}.request_events (
            id, request_id, event_type, actor_user_id, actor_name, payload
        ) VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s)
        RETURNING *
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        str(event.id),
                        str(event.request_id),
                        event.event_type,
                        event.actor_user_id,
                        event.actor_name,
                        Jsonb(event.payload or {}),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _event(dict(row))

    def list_events(
        self,
        request_id: UUID | str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[RequestEvent], int]:
        count_sql = f"""
        SELECT COUNT(*) AS total FROM {_SCHEMA}.request_events
        WHERE request_id = %s::uuid
        """
        list_sql = f"""
        SELECT * FROM {_SCHEMA}.request_events
        WHERE request_id = %s::uuid
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        offset = max(page - 1, 0) * page_size
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(count_sql, (str(request_id),))
                total = int((cur.fetchone() or {}).get("total") or 0)
                cur.execute(list_sql, (str(request_id), page_size, offset))
                rows = cur.fetchall()
        return [_event(dict(row)) for row in rows], total

    def create_comment(self, comment: RequestComment) -> RequestComment:
        sql = f"""
        INSERT INTO {_SCHEMA}.request_comments (
            id, request_id, author_user_id, author_name, body
        ) VALUES (%s::uuid, %s::uuid, %s, %s, %s)
        RETURNING *
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        str(comment.id),
                        str(comment.request_id),
                        comment.author_user_id,
                        comment.author_name,
                        comment.body,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _comment(dict(row))

    def list_comments(
        self,
        request_id: UUID | str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[RequestComment], int]:
        count_sql = f"""
        SELECT COUNT(*) AS total FROM {_SCHEMA}.request_comments
        WHERE request_id = %s::uuid
        """
        list_sql = f"""
        SELECT * FROM {_SCHEMA}.request_comments
        WHERE request_id = %s::uuid
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        offset = max(page - 1, 0) * page_size
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(count_sql, (str(request_id),))
                total = int((cur.fetchone() or {}).get("total") or 0)
                cur.execute(list_sql, (str(request_id), page_size, offset))
                rows = cur.fetchall()
        return [_comment(dict(row)) for row in rows], total
