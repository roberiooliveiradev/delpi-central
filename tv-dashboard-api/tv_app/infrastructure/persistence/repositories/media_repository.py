from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.infrastructure.persistence.plugins_postgres_connection import get_connection


class MediaAssetNotFoundError(LookupError):
    pass


def _row_to_asset(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "playlistId": str(row["playlist_id"]),
        "storedName": row["stored_name"],
        "originalName": row["original_name"],
        "mimeType": row["mime_type"],
        "mediaKind": row["media_kind"],
        "fileSizeBytes": row["file_size_bytes"],
        "createdBy": row["created_by"],
        "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
    }


class MediaRepository:
    def create(
        self,
        *,
        playlist_id: UUID,
        stored_name: str,
        original_name: str | None,
        mime_type: str,
        media_kind: str,
        file_size_bytes: int,
        created_by: str | None,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.media_assets (
                        playlist_id, stored_name, original_name, mime_type,
                        media_kind, file_size_bytes, created_by
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        str(playlist_id),
                        stored_name,
                        original_name,
                        mime_type,
                        media_kind,
                        file_size_bytes,
                        created_by,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _row_to_asset(row)

    def get(self, asset_id: UUID) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM tv_dashboard.media_assets WHERE id = %s",
                    (str(asset_id),),
                )
                row = cur.fetchone()
        return _row_to_asset(row) if row else None

    def get_for_playlist(self, playlist_id: UUID, asset_id: UUID) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM tv_dashboard.media_assets
                    WHERE id = %s AND playlist_id = %s
                    """,
                    (str(asset_id), str(playlist_id)),
                )
                row = cur.fetchone()
        return _row_to_asset(row) if row else None

    def get_for_token(self, token: str, asset_id: UUID) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ma.*
                    FROM tv_dashboard.media_assets ma
                    INNER JOIN tv_dashboard.playlists p ON p.id = ma.playlist_id
                    WHERE ma.id = %s AND p.public_token = %s AND p.is_active = TRUE
                    """,
                    (str(asset_id), token.strip()),
                )
                row = cur.fetchone()
        return _row_to_asset(row) if row else None
