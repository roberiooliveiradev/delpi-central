from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from tv_app.infrastructure.persistence.plugins_postgres_connection import get_connection

NATIVE_SCREENS_PATH = Path(__file__).resolve().parents[3] / "content" / "native_screens.json"


class PlaylistNotFoundError(LookupError):
    pass


class SlideNotFoundError(LookupError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _row_to_playlist(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "publicToken": row["public_token"],
        "name": row["name"],
        "description": row["description"],
        "viewportProfile": row["viewport_profile"],
        "transitionStyle": row["transition_style"],
        "defaultDurationSec": row["default_duration_sec"],
        "globalRefreshSec": row["global_refresh_sec"],
        "isActive": row["is_active"],
        "viewCount": row["view_count"],
        "lastPresentedAt": row["last_presented_at"].isoformat() if row["last_presented_at"] else None,
        "createdBy": row["created_by"],
        "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
        "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


def _row_to_slide(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "playlistId": str(row["playlist_id"]),
        "sortOrder": row["sort_order"],
        "slideType": row["slide_type"],
        "durationSec": row["duration_sec"],
        "title": row["title"],
        "nativeScreenKey": row["native_screen_key"],
        "nativeConfig": row["native_config"] or {},
        "externalUrl": row["external_url"],
        "externalSandbox": row["external_sandbox"],
        "isActive": row["is_active"],
    }


class PlaylistRepository:
    def list_playlists(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM tv_dashboard.playlists
                    ORDER BY updated_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
                rows = cur.fetchall()
        return [_row_to_playlist(row) for row in rows]

    def get_by_id(self, playlist_id: UUID) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM tv_dashboard.playlists WHERE id = %s",
                    (str(playlist_id),),
                )
                row = cur.fetchone()
        return _row_to_playlist(row) if row else None

    def get_by_token(self, token: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM tv_dashboard.playlists WHERE public_token = %s",
                    (token.strip(),),
                )
                row = cur.fetchone()
        return _row_to_playlist(row) if row else None

    def create(self, *, name: str, description: str | None, created_by: str | None) -> dict[str, Any]:
        token = secrets.token_urlsafe(32)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.playlists (public_token, name, description, created_by)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                    """,
                    (token, name.strip(), description, created_by),
                )
                row = cur.fetchone()
            conn.commit()
        return _row_to_playlist(row)

    def update(
        self,
        playlist_id: UUID,
        *,
        name: str | None = None,
        description: str | None = None,
        viewport_profile: str | None = None,
        transition_style: str | None = None,
        default_duration_sec: int | None = None,
        global_refresh_sec: int | None = None,
    ) -> dict[str, Any]:
        fields: list[str] = []
        values: list[Any] = []
        mapping = {
            "name": name,
            "description": description,
            "viewport_profile": viewport_profile,
            "transition_style": transition_style,
            "default_duration_sec": default_duration_sec,
            "global_refresh_sec": global_refresh_sec,
        }
        for column, value in mapping.items():
            if value is not None:
                fields.append(f"{column} = %s")
                values.append(value)
        if not fields:
            existing = self.get_by_id(playlist_id)
            if not existing:
                raise PlaylistNotFoundError
            return existing
        fields.append("updated_at = NOW()")
        values.append(str(playlist_id))
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE tv_dashboard.playlists
                    SET {", ".join(fields)}
                    WHERE id = %s
                    RETURNING *
                    """,
                    tuple(values),
                )
                row = cur.fetchone()
            conn.commit()
        if not row:
            raise PlaylistNotFoundError
        return _row_to_playlist(row)

    def set_active(self, playlist_id: UUID, *, is_active: bool) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tv_dashboard.playlists
                    SET is_active = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (is_active, str(playlist_id)),
                )
                row = cur.fetchone()
            conn.commit()
        if not row:
            raise PlaylistNotFoundError
        return _row_to_playlist(row)

    def delete(self, playlist_id: UUID) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM tv_dashboard.playlists WHERE id = %s RETURNING id",
                    (str(playlist_id),),
                )
                row = cur.fetchone()
            conn.commit()
        if not row:
            raise PlaylistNotFoundError

    def regenerate_token(self, playlist_id: UUID) -> dict[str, Any]:
        token = secrets.token_urlsafe(32)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tv_dashboard.playlists
                    SET public_token = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (token, str(playlist_id)),
                )
                row = cur.fetchone()
            conn.commit()
        if not row:
            raise PlaylistNotFoundError
        return _row_to_playlist(row)

    def duplicate_playlist(
        self,
        playlist_id: UUID,
        *,
        created_by: str | None,
        name_suffix: str = " (cópia)",
    ) -> dict[str, Any]:
        source = self.get_by_id(playlist_id)
        if not source:
            raise PlaylistNotFoundError
        slides = self.list_slides(playlist_id)
        token = secrets.token_urlsafe(32)
        copy_name = f"{source['name']}{name_suffix}".strip()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.playlists (
                      public_token, name, description, viewport_profile, transition_style,
                      default_duration_sec, global_refresh_sec, is_active, created_by
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE, %s)
                    RETURNING *
                    """,
                    (
                        token,
                        copy_name,
                        source.get("description"),
                        source["viewportProfile"],
                        source["transitionStyle"],
                        source["defaultDurationSec"],
                        source["globalRefreshSec"],
                        created_by,
                    ),
                )
                new_row = cur.fetchone()
                new_id = new_row["id"]
                for slide in slides:
                    cur.execute(
                        """
                        INSERT INTO tv_dashboard.slides (
                          playlist_id, sort_order, slide_type, duration_sec, title,
                          native_screen_key, native_config, external_url, external_sandbox, is_active
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                        """,
                        (
                            str(new_id),
                            slide["sortOrder"],
                            slide["slideType"],
                            slide.get("durationSec"),
                            slide["title"],
                            slide.get("nativeScreenKey"),
                            json.dumps(slide.get("nativeConfig") or {}),
                            slide.get("externalUrl"),
                            slide.get("externalSandbox"),
                            slide.get("isActive", True),
                        ),
                    )
            conn.commit()
        return _row_to_playlist(new_row)

    def duplicate_slide(self, slide_id: UUID) -> dict[str, Any]:
        slide = self.get_slide(slide_id)
        playlist_id = UUID(slide["playlistId"])
        copy_title = f"{slide['title']} (cópia)".strip()
        return self.add_slide(
            playlist_id,
            {
                "slideType": slide["slideType"],
                "title": copy_title,
                "durationSec": slide.get("durationSec"),
                "sortOrder": self.next_sort_order(playlist_id),
                "nativeScreenKey": slide.get("nativeScreenKey"),
                "nativeConfig": slide.get("nativeConfig") or {},
                "externalUrl": slide.get("externalUrl"),
                "externalSandbox": slide.get("externalSandbox"),
            },
        )

    def touch_view(self, token: str) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tv_dashboard.playlists
                    SET view_count = view_count + 1,
                        last_presented_at = NOW(),
                        updated_at = updated_at
                    WHERE public_token = %s AND is_active = TRUE
                    """,
                    (token.strip(),),
                )
            conn.commit()

    def touch_heartbeat(self, token: str) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tv_dashboard.playlists
                    SET last_presented_at = NOW(),
                        updated_at = updated_at
                    WHERE public_token = %s AND is_active = TRUE
                    RETURNING id
                    """,
                    (token.strip(),),
                )
                row = cur.fetchone()
            conn.commit()
        return row is not None

    def list_slides(self, playlist_id: UUID) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM tv_dashboard.slides
                    WHERE playlist_id = %s
                    ORDER BY sort_order ASC
                    """,
                    (str(playlist_id),),
                )
                rows = cur.fetchall()
        return [_row_to_slide(row) for row in rows]

    def next_sort_order(self, playlist_id: UUID) -> int:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order
                    FROM tv_dashboard.slides
                    WHERE playlist_id = %s
                    """,
                    (str(playlist_id),),
                )
                row = cur.fetchone()
        return int(row["next_order"]) if row else 0

    def add_slide(self, playlist_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
        sort_order = payload.get("sortOrder")
        if sort_order is None:
            sort_order = self.next_sort_order(playlist_id)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.slides (
                      playlist_id, sort_order, slide_type, duration_sec, title,
                      native_screen_key, native_config, external_url, external_sandbox
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                    RETURNING *
                    """,
                    (
                        str(playlist_id),
                        sort_order,
                        payload["slideType"],
                        payload.get("durationSec"),
                        payload["title"].strip(),
                        payload.get("nativeScreenKey"),
                        json.dumps(payload.get("nativeConfig") or {}),
                        payload.get("externalUrl"),
                        payload.get("externalSandbox"),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _row_to_slide(row)

    def update_slide(self, slide_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
        fields: list[str] = []
        values: list[Any] = []
        mapping = {
            "sort_order": payload.get("sortOrder"),
            "duration_sec": payload.get("durationSec"),
            "title": payload.get("title"),
            "native_config": json.dumps(payload["nativeConfig"]) if "nativeConfig" in payload else None,
            "external_url": payload.get("externalUrl"),
            "external_sandbox": payload.get("externalSandbox"),
            "is_active": payload.get("isActive"),
        }
        for column, value in mapping.items():
            if value is not None:
                if column == "title" and isinstance(value, str):
                    value = value.strip()
                if column == "native_config":
                    fields.append(f"{column} = %s::jsonb")
                else:
                    fields.append(f"{column} = %s")
                values.append(value)
        if not fields:
            return self.get_slide(slide_id)
        fields.append("updated_at = NOW()")
        values.append(str(slide_id))
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE tv_dashboard.slides
                    SET {", ".join(fields)}
                    WHERE id = %s
                    RETURNING *
                    """,
                    tuple(values),
                )
                row = cur.fetchone()
            conn.commit()
        if not row:
            raise SlideNotFoundError
        return _row_to_slide(row)

    def get_slide(self, slide_id: UUID) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tv_dashboard.slides WHERE id = %s", (str(slide_id),))
                row = cur.fetchone()
        if not row:
            raise SlideNotFoundError
        return _row_to_slide(row)

    def delete_slide(self, slide_id: UUID) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM tv_dashboard.slides WHERE id = %s RETURNING id",
                    (str(slide_id),),
                )
                row = cur.fetchone()
            conn.commit()
        if not row:
            raise SlideNotFoundError

    def reorder_slides(self, playlist_id: UUID, items: list[dict[str, int | str]]) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Fase 1: ordens temporárias negativas — evita violar idx_slides_playlist_order ao trocar posições.
                for offset, item in enumerate(items):
                    cur.execute(
                        """
                        UPDATE tv_dashboard.slides
                        SET sort_order = %s, updated_at = NOW()
                        WHERE id = %s AND playlist_id = %s
                        """,
                        (-1000 - offset, str(item["id"]), str(playlist_id)),
                    )
                for item in items:
                    cur.execute(
                        """
                        UPDATE tv_dashboard.slides
                        SET sort_order = %s, updated_at = NOW()
                        WHERE id = %s AND playlist_id = %s
                        """,
                        (item["sortOrder"], str(item["id"]), str(playlist_id)),
                    )
            conn.commit()
        return self.list_slides(playlist_id)


def load_native_screens_catalog() -> list[dict[str, Any]]:
    data = json.loads(NATIVE_SCREENS_PATH.read_text(encoding="utf-8"))
    return list(data.get("screens") or [])
