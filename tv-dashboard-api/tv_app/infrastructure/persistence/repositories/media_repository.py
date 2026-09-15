from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from tv_app.infrastructure.persistence.plugins_postgres_connection import get_connection


def _row_to_asset(row: dict[str, Any]) -> dict[str, Any]:
    optimized_at = row.get("video_optimized_at")
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
        "posterStoredName": row.get("poster_stored_name"),
        "durationMs": row.get("duration_ms"),
        "widthPx": row.get("width_px"),
        "heightPx": row.get("height_px"),
        "videoOptimizedAt": optimized_at.isoformat() if optimized_at else None,
        "hasPoster": bool(row.get("poster_stored_name")),
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
        poster_stored_name: str | None = None,
        duration_ms: int | None = None,
        width_px: int | None = None,
        height_px: int | None = None,
        video_optimized_at: datetime | None = None,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.media_assets (
                        playlist_id, stored_name, original_name, mime_type,
                        media_kind, file_size_bytes, created_by,
                        poster_stored_name, duration_ms, width_px, height_px,
                        video_optimized_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        poster_stored_name,
                        duration_ms,
                        width_px,
                        height_px,
                        video_optimized_at,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _row_to_asset(row)

    def update_video_optimize(
        self,
        *,
        asset_id: UUID,
        poster_stored_name: str | None,
        duration_ms: int | None,
        width_px: int | None,
        height_px: int | None,
        file_size_bytes: int | None = None,
        mark_optimized: bool = True,
    ) -> dict[str, Any] | None:
        optimized_at = datetime.now(timezone.utc) if mark_optimized else None
        with get_connection() as conn:
            with conn.cursor() as cur:
                if file_size_bytes is not None:
                    cur.execute(
                        """
                        UPDATE tv_dashboard.media_assets
                        SET poster_stored_name = %s,
                            duration_ms = %s,
                            width_px = %s,
                            height_px = %s,
                            file_size_bytes = %s,
                            video_optimized_at = COALESCE(%s, video_optimized_at)
                        WHERE id = %s
                        RETURNING *
                        """,
                        (
                            poster_stored_name,
                            duration_ms,
                            width_px,
                            height_px,
                            file_size_bytes,
                            optimized_at,
                            str(asset_id),
                        ),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE tv_dashboard.media_assets
                        SET poster_stored_name = %s,
                            duration_ms = %s,
                            width_px = %s,
                            height_px = %s,
                            video_optimized_at = COALESCE(%s, video_optimized_at)
                        WHERE id = %s
                        RETURNING *
                        """,
                        (
                            poster_stored_name,
                            duration_ms,
                            width_px,
                            height_px,
                            optimized_at,
                            str(asset_id),
                        ),
                    )
                row = cur.fetchone()
            conn.commit()
        return _row_to_asset(row) if row else None

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

    def list_for_playlist(
        self,
        playlist_id: UUID,
        *,
        media_kind: str | None = None,
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if media_kind:
                    cur.execute(
                        """
                        SELECT * FROM tv_dashboard.media_assets
                        WHERE playlist_id = %s AND media_kind = %s
                        ORDER BY created_at DESC
                        """,
                        (str(playlist_id), media_kind),
                    )
                else:
                    cur.execute(
                        """
                        SELECT * FROM tv_dashboard.media_assets
                        WHERE playlist_id = %s
                        ORDER BY created_at DESC
                        """,
                        (str(playlist_id),),
                    )
                rows = cur.fetchall()
        return [_row_to_asset(row) for row in rows]

    def list_videos_needing_optimize(self, playlist_id: UUID) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM tv_dashboard.media_assets
                    WHERE playlist_id = %s
                      AND media_kind = 'video'
                      AND video_optimized_at IS NULL
                    ORDER BY created_at ASC
                    """,
                    (str(playlist_id),),
                )
                rows = cur.fetchall()
        return [_row_to_asset(row) for row in rows]

    def delete(self, playlist_id: UUID, asset_id: UUID) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM tv_dashboard.media_assets
                    WHERE id = %s AND playlist_id = %s
                    RETURNING *
                    """,
                    (str(asset_id), str(playlist_id)),
                )
                row = cur.fetchone()
            conn.commit()
        return _row_to_asset(row) if row else None

    def get_for_token(self, token: str, asset_id: UUID) -> dict[str, Any] | None:
        """Mídia pelo token público — capability URL, independente de is_active.

        O payload `/public/present/{token}` continua exigindo programação ativa.
        `<img>`/CSS da home e do filmstrip não enviam JWT; desativar o deck
        não pode 404 nas capas autenticadas nem nas URLs já emitidas.
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ma.*
                    FROM tv_dashboard.media_assets ma
                    INNER JOIN tv_dashboard.playlists p ON p.id = ma.playlist_id
                    WHERE ma.id = %s AND p.public_token = %s
                    """,
                    (str(asset_id), token.strip()),
                )
                row = cur.fetchone()
        return _row_to_asset(row) if row else None
