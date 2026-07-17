from __future__ import annotations

import json
import math
from typing import Any
from uuid import UUID

from tv_app.infrastructure.persistence.plugins_postgres_connection import get_connection

HISTORY_LIMIT_PER_PLAYLIST = 500


class PlaylistHistoryNotFoundError(LookupError):
    pass


class PlaylistRevisionConflictError(RuntimeError):
    def __init__(self, current_revision: int) -> None:
        self.current_revision = current_revision
        super().__init__(f"Revisão atual: {current_revision}")


def _history_summary(row: dict[str, Any]) -> dict[str, Any]:
    result = {
        "snapshotId": str(row["id"]),
        "playlistId": str(row["playlist_id"]),
        "revision": int(row["revision"]),
        "authorId": row["actor_user_id"],
        "authorName": None,
        "reason": row["reason"],
        "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
    }
    snapshot = row.get("snapshot")
    if snapshot:
        if isinstance(snapshot, str):
            snapshot = json.loads(snapshot)
        playlist = dict(snapshot.get("playlist") or {})
        slides = list(snapshot.get("slides") or [])
        result["preview"] = {
            "playlistName": playlist.get("name"),
            "slideCount": len(slides),
            "slideTitles": [
                str(slide.get("title"))
                for slide in slides[:3]
                if isinstance(slide, dict) and slide.get("title")
            ],
            "selectedSlideId": None,
        }
    elif "slide_count" in row:
        result["preview"] = {
            "playlistName": row.get("playlist_name"),
            "slideCount": int(row.get("slide_count") or 0),
            "slideTitles": list(row.get("slide_titles") or []),
            "selectedSlideId": None,
        }
    else:
        result["preview"] = None
    return result


class PlaylistHistoryRepository:
    @staticmethod
    def capture_before_mutation(
        cur: Any,
        playlist_id: UUID,
        *,
        actor_user_id: str,
        reason: str,
    ) -> None:
        """Captura o estado bloqueado e poda versões antigas na transação chamadora."""
        cur.execute(
            """
            INSERT INTO tv_dashboard.playlist_history (
              playlist_id, revision, actor_user_id, reason, snapshot
            )
            SELECT
              p.id,
              p.revision,
              %s,
              %s,
              jsonb_build_object(
                'playlist', jsonb_build_object(
                  'id', p.id,
                  'name', p.name,
                  'description', p.description,
                  'viewportProfile', p.viewport_profile,
                  'transitionStyle', p.transition_style,
                  'defaultDurationSec', p.default_duration_sec,
                  'globalRefreshSec', p.global_refresh_sec,
                  'dataDefaults', p.data_defaults,
                  'masterConfig', p.master_config,
                  'isActive', p.is_active
                ),
                'slides', COALESCE((
                  SELECT jsonb_agg(
                    jsonb_build_object(
                      'id', s.id,
                      'playlistId', s.playlist_id,
                      'sortOrder', s.sort_order,
                      'slideType', s.slide_type,
                      'durationSec', s.duration_sec,
                      'title', s.title,
                      'nativeScreenKey', s.native_screen_key,
                      'nativeConfig', s.native_config,
                      'externalUrl', s.external_url,
                      'externalSandbox', s.external_sandbox,
                      'isActive', s.is_active,
                      'transitionStyle', s.transition_style,
                      'createdAt', s.created_at,
                      'updatedAt', s.updated_at
                    )
                    ORDER BY s.sort_order ASC, s.id ASC
                  )
                  FROM tv_dashboard.slides s
                  WHERE s.playlist_id = p.id
                ), '[]'::jsonb)
              )
            FROM tv_dashboard.playlists p
            WHERE p.id = %s
            FOR UPDATE
            """,
            (actor_user_id.strip(), reason.strip(), str(playlist_id)),
        )
        if cur.rowcount != 1:
            raise PlaylistHistoryNotFoundError
        cur.execute(
            """
            DELETE FROM tv_dashboard.playlist_history h
            WHERE h.playlist_id = %s
              AND h.id IN (
                SELECT old.id
                FROM tv_dashboard.playlist_history old
                WHERE old.playlist_id = %s
                ORDER BY old.revision DESC, old.created_at DESC, old.id DESC
                OFFSET %s
              )
            """,
            (str(playlist_id), str(playlist_id), HISTORY_LIMIT_PER_PLAYLIST),
        )

    def list_history(
        self,
        playlist_id: UUID,
        *,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        safe_page = max(int(page), 1)
        safe_page_size = min(max(int(page_size), 1), 100)
        safe_offset = (safe_page - 1) * safe_page_size
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                      h.id,
                      h.playlist_id,
                      h.revision,
                      h.actor_user_id,
                      h.reason,
                      h.created_at,
                      h.snapshot #>> '{playlist,name}' AS playlist_name,
                      jsonb_array_length(COALESCE(h.snapshot -> 'slides', '[]'::jsonb))
                        AS slide_count,
                      COALESCE((
                        SELECT jsonb_agg(item.value ->> 'title' ORDER BY item.ordinality)
                        FROM jsonb_array_elements(
                          COALESCE(h.snapshot -> 'slides', '[]'::jsonb)
                        ) WITH ORDINALITY AS item(value, ordinality)
                        WHERE item.ordinality <= 3
                      ), '[]'::jsonb) AS slide_titles
                    FROM tv_dashboard.playlist_history h
                    WHERE h.playlist_id = %s
                    ORDER BY h.revision DESC, h.created_at DESC, h.id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (str(playlist_id), safe_page_size, safe_offset),
                )
                rows = cur.fetchall()
                cur.execute(
                    """
                    SELECT
                      p.revision AS current_revision,
                      COUNT(h.id) AS total,
                      (
                        SELECT latest.id
                        FROM tv_dashboard.playlist_history latest
                        WHERE latest.playlist_id = p.id
                        ORDER BY latest.revision DESC, latest.created_at DESC, latest.id DESC
                        LIMIT 1
                      ) AS current_snapshot_id
                    FROM tv_dashboard.playlists p
                    LEFT JOIN tv_dashboard.playlist_history h ON h.playlist_id = p.id
                    WHERE p.id = %s
                    GROUP BY p.id, p.revision
                    """,
                    (str(playlist_id),),
                )
                metadata = cur.fetchone()
        total = int(metadata["total"]) if metadata else 0
        return {
            "items": [_history_summary(row) for row in rows],
            "page": safe_page,
            "pageSize": safe_page_size,
            "total": total,
            "totalPages": math.ceil(total / safe_page_size) if total else 0,
            "currentRevision": int(metadata["current_revision"]) if metadata else None,
            "currentSnapshotId": (
                str(metadata["current_snapshot_id"])
                if metadata and metadata["current_snapshot_id"]
                else None
            ),
        }

    def get_history(self, playlist_id: UUID, history_id: UUID) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, playlist_id, revision, actor_user_id, reason, snapshot, created_at
                    FROM tv_dashboard.playlist_history
                    WHERE id = %s AND playlist_id = %s
                    """,
                    (str(history_id), str(playlist_id)),
                )
                row = cur.fetchone()
        if not row:
            raise PlaylistHistoryNotFoundError
        result = _history_summary(row)
        snapshot = row["snapshot"]
        if isinstance(snapshot, str):
            snapshot = json.loads(snapshot)
        playlist = dict(snapshot.get("playlist") or {})
        playlist["slides"] = list(snapshot.get("slides") or [])
        result["playlist"] = playlist
        result["selectedSlideId"] = None
        return result

    def restore(
        self,
        playlist_id: UUID,
        history_id: UUID,
        *,
        expected_revision: int,
        actor_user_id: str,
        reason: str,
    ) -> int:
        """Restaura playlist e slides, preservando UUIDs e ordem, em uma transação."""
        with get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT revision
                        FROM tv_dashboard.playlists
                        WHERE id = %s
                        FOR UPDATE
                        """,
                        (str(playlist_id),),
                    )
                    current = cur.fetchone()
                    if not current:
                        raise PlaylistHistoryNotFoundError
                    current_revision = int(current["revision"])
                    if current_revision != int(expected_revision):
                        raise PlaylistRevisionConflictError(current_revision)

                    cur.execute(
                        """
                        SELECT snapshot
                        FROM tv_dashboard.playlist_history
                        WHERE id = %s AND playlist_id = %s
                        """,
                        (str(history_id), str(playlist_id)),
                    )
                    history = cur.fetchone()
                    if not history:
                        raise PlaylistHistoryNotFoundError
                    snapshot = history["snapshot"]
                    if isinstance(snapshot, str):
                        snapshot = json.loads(snapshot)
                    playlist = dict(snapshot.get("playlist") or {})
                    slides = list(snapshot.get("slides") or [])

                    self.capture_before_mutation(
                        cur,
                        playlist_id,
                        actor_user_id=actor_user_id,
                        reason=reason,
                    )
                    cur.execute(
                        """
                        UPDATE tv_dashboard.playlists
                        SET name = %s,
                            description = %s,
                            viewport_profile = %s,
                            transition_style = %s,
                            default_duration_sec = %s,
                            global_refresh_sec = %s,
                            data_defaults = %s::jsonb,
                            master_config = %s::jsonb,
                            is_active = %s,
                            revision = revision + 1,
                            updated_at = NOW()
                        WHERE id = %s
                        RETURNING revision
                        """,
                        (
                            playlist["name"],
                            playlist.get("description"),
                            playlist["viewportProfile"],
                            playlist["transitionStyle"],
                            playlist["defaultDurationSec"],
                            playlist["globalRefreshSec"],
                            json.dumps(playlist.get("dataDefaults") or {}),
                            json.dumps(playlist.get("masterConfig") or {}),
                            bool(playlist.get("isActive", True)),
                            str(playlist_id),
                        ),
                    )
                    restored = cur.fetchone()
                    cur.execute(
                        "DELETE FROM tv_dashboard.slides WHERE playlist_id = %s",
                        (str(playlist_id),),
                    )
                    for slide in slides:
                        cur.execute(
                            """
                            INSERT INTO tv_dashboard.slides (
                              id, playlist_id, sort_order, slide_type, duration_sec, title,
                              native_screen_key, native_config, external_url, external_sandbox,
                              is_active, transition_style, created_at, updated_at
                            )
                            VALUES (
                              %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s,
                              %s, %s, %s, %s
                            )
                            """,
                            (
                                str(slide["id"]),
                                str(playlist_id),
                                slide["sortOrder"],
                                slide["slideType"],
                                slide.get("durationSec"),
                                slide["title"],
                                slide.get("nativeScreenKey"),
                                json.dumps(slide.get("nativeConfig") or {}),
                                slide.get("externalUrl"),
                                slide.get("externalSandbox"),
                                bool(slide.get("isActive", True)),
                                slide.get("transitionStyle"),
                                slide.get("createdAt"),
                                slide.get("updatedAt"),
                            ),
                        )
                conn.commit()
                return int(restored["revision"])
            except Exception:
                conn.rollback()
                raise
