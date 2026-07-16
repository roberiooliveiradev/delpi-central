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
    owner = row.get("owner_user_id") or row.get("created_by")
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
        "ownerUserId": owner,
        "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
        "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None,
        "dataDefaults": row.get("data_defaults") or {},
        "masterConfig": row.get("master_config") or {},
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
        "transitionStyle": row.get("transition_style"),
    }


class PlaylistRepository:
    @staticmethod
    def _touch_playlist_updated_at(cur, playlist_id: UUID) -> None:
        cur.execute(
            """
            UPDATE tv_dashboard.playlists
            SET updated_at = NOW()
            WHERE id = %s
            """,
            (str(playlist_id),),
        )

    def get_presentation_content_revision(self, playlist_id: UUID) -> str:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                      p.updated_at AS playlist_updated,
                      COUNT(s.id) AS slide_count,
                      COALESCE(MAX(s.updated_at), to_timestamp(0)) AS max_slide_updated
                    FROM tv_dashboard.playlists p
                    LEFT JOIN tv_dashboard.slides s ON s.playlist_id = p.id
                    WHERE p.id = %s
                    GROUP BY p.id, p.updated_at
                    """,
                    (str(playlist_id),),
                )
                row = cur.fetchone()
        if not row:
            return ""
        playlist_updated = (
            row["playlist_updated"].isoformat() if row["playlist_updated"] else ""
        )
        max_slide_updated = (
            row["max_slide_updated"].isoformat() if row["max_slide_updated"] else ""
        )
        return f"{playlist_updated}|{int(row['slide_count'])}|{max_slide_updated}"

    def list_playlists(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        user_id: str | None = None,
        include_all: bool = False,
    ) -> list[dict[str, Any]]:
        """Lista programações do usuário (dono ou share). `include_all` só para admin."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                if include_all:
                    cur.execute(
                        """
                        SELECT *
                        FROM tv_dashboard.playlists
                        ORDER BY updated_at DESC
                        LIMIT %s OFFSET %s
                        """,
                        (limit, offset),
                    )
                elif not user_id:
                    return []
                else:
                    cur.execute(
                        """
                        SELECT p.*
                        FROM tv_dashboard.playlists p
                        WHERE p.owner_user_id = %s
                           OR EXISTS (
                             SELECT 1
                             FROM tv_dashboard.playlist_shares s
                             WHERE s.playlist_id = p.id
                               AND s.target_user_id = %s
                           )
                        ORDER BY p.updated_at DESC
                        LIMIT %s OFFSET %s
                        """,
                        (user_id, user_id, limit, offset),
                    )
                rows = cur.fetchall()
        return [_row_to_playlist(row) for row in rows]

    def get_share_role(self, playlist_id: UUID, target_user_id: str) -> str | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role
                    FROM tv_dashboard.playlist_shares
                    WHERE playlist_id = %s AND target_user_id = %s
                    """,
                    (str(playlist_id), target_user_id.strip()),
                )
                row = cur.fetchone()
        if not row:
            return None
        return str(row["role"])

    def list_shares(self, playlist_id: UUID) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, playlist_id, target_user_id, role, created_by, created_at
                    FROM tv_dashboard.playlist_shares
                    WHERE playlist_id = %s
                    ORDER BY created_at ASC
                    """,
                    (str(playlist_id),),
                )
                rows = cur.fetchall()
        return [
            {
                "id": str(row["id"]),
                "playlistId": str(row["playlist_id"]),
                "targetUserId": row["target_user_id"],
                "role": row["role"],
                "createdBy": row["created_by"],
                "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
            }
            for row in rows
        ]

    def upsert_share(
        self,
        playlist_id: UUID,
        *,
        target_user_id: str,
        role: str,
        created_by: str | None,
    ) -> dict[str, Any]:
        role_norm = role if role in {"viewer", "editor"} else "editor"
        target = target_user_id.strip()
        if not target:
            raise ValueError("target_user_id obrigatório")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.playlist_shares
                      (playlist_id, target_user_id, role, created_by)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (playlist_id, target_user_id)
                    DO UPDATE SET role = EXCLUDED.role
                    RETURNING id, playlist_id, target_user_id, role, created_by, created_at
                    """,
                    (str(playlist_id), target, role_norm, created_by),
                )
                row = cur.fetchone()
            conn.commit()
        return {
            "id": str(row["id"]),
            "playlistId": str(row["playlist_id"]),
            "targetUserId": row["target_user_id"],
            "role": row["role"],
            "createdBy": row["created_by"],
            "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
        }

    def revoke_share(self, playlist_id: UUID, target_user_id: str) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM tv_dashboard.playlist_shares
                    WHERE playlist_id = %s AND target_user_id = %s
                    RETURNING id
                    """,
                    (str(playlist_id), target_user_id.strip()),
                )
                row = cur.fetchone()
            conn.commit()
        return row is not None

    def create_edit_invite(
        self,
        playlist_id: UUID,
        *,
        role: str,
        created_by: str,
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:
        token = secrets.token_urlsafe(32)
        role_norm = role if role in {"viewer", "editor"} else "editor"
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.playlist_edit_invites
                      (playlist_id, token, role, created_by, expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, playlist_id, token, role, created_by, expires_at, created_at
                    """,
                    (str(playlist_id), token, role_norm, created_by, expires_at),
                )
                row = cur.fetchone()
            conn.commit()
        return {
            "id": str(row["id"]),
            "playlistId": str(row["playlist_id"]),
            "token": row["token"],
            "role": row["role"],
            "createdBy": row["created_by"],
            "expiresAt": row["expires_at"].isoformat() if row["expires_at"] else None,
            "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
        }

    def get_edit_invite_by_token(self, token: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM tv_dashboard.playlist_edit_invites
                    WHERE token = %s
                    """,
                    (token.strip(),),
                )
                row = cur.fetchone()
        if not row:
            return None
        return {
            "id": str(row["id"]),
            "playlistId": str(row["playlist_id"]),
            "token": row["token"],
            "role": row["role"],
            "createdBy": row["created_by"],
            "expiresAt": row["expires_at"].isoformat() if row["expires_at"] else None,
            "revokedAt": row["revoked_at"].isoformat() if row["revoked_at"] else None,
            "redeemedAt": row["redeemed_at"].isoformat() if row["redeemed_at"] else None,
            "redeemedBy": row["redeemed_by"],
            "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
        }

    def redeem_edit_invite(self, token: str, *, redeemed_by: str) -> dict[str, Any] | None:
        """Cria/atualiza share para o usuário e marca o invite como resgatado (reutilizável até revoke)."""
        invite = self.get_edit_invite_by_token(token)
        if not invite:
            return None
        if invite.get("revokedAt"):
            return None
        expires = invite.get("expiresAt")
        if expires:
            exp = datetime.fromisoformat(expires)
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < _utcnow():
                return None
        share = self.upsert_share(
            UUID(invite["playlistId"]),
            target_user_id=redeemed_by,
            role=str(invite["role"]),
            created_by=invite.get("createdBy"),
        )
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tv_dashboard.playlist_edit_invites
                    SET redeemed_at = NOW(), redeemed_by = %s
                    WHERE token = %s AND revoked_at IS NULL
                    """,
                    (redeemed_by, token.strip()),
                )
            conn.commit()
        return {"share": share, "playlistId": invite["playlistId"], "role": invite["role"]}

    def revoke_edit_invites(self, playlist_id: UUID) -> int:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tv_dashboard.playlist_edit_invites
                    SET revoked_at = NOW()
                    WHERE playlist_id = %s AND revoked_at IS NULL
                    """,
                    (str(playlist_id),),
                )
                count = cur.rowcount
            conn.commit()
        return int(count or 0)

    def get_by_id(self, playlist_id: UUID) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM tv_dashboard.playlists WHERE id = %s",
                    (str(playlist_id),),
                )
                row = cur.fetchone()
        return _row_to_playlist(row) if row else None

    def try_claim_owner(self, playlist_id: UUID, user_id: str) -> dict[str, Any] | None:
        """Atribui dono só se ainda estiver órfã (owner e created_by vazios)."""
        actor = (user_id or "").strip()
        if not actor:
            return None
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tv_dashboard.playlists
                    SET owner_user_id = %s,
                        created_by = COALESCE(NULLIF(BTRIM(COALESCE(created_by, '')), ''), %s),
                        updated_at = NOW()
                    WHERE id = %s
                      AND (
                        owner_user_id IS NULL
                        OR BTRIM(owner_user_id) = ''
                      )
                      AND (
                        created_by IS NULL
                        OR BTRIM(created_by) = ''
                      )
                    RETURNING *
                    """,
                    (actor, actor, str(playlist_id)),
                )
                row = cur.fetchone()
            conn.commit()
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
        owner = (created_by or "").strip() or None
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.playlists
                      (public_token, name, description, created_by, owner_user_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (token, name.strip(), description, created_by, owner),
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
        data_defaults: dict[str, Any] | None = None,
        master_config: dict[str, Any] | None = None,
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
        if data_defaults is not None:
            fields.append("data_defaults = %s::jsonb")
            values.append(json.dumps(data_defaults))
        if master_config is not None:
            fields.append("master_config = %s::jsonb")
            values.append(json.dumps(master_config))
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
        owner = (created_by or "").strip() or None
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.playlists (
                      public_token, name, description, viewport_profile, transition_style,
                      default_duration_sec, global_refresh_sec, data_defaults, master_config,
                      is_active, created_by, owner_user_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, FALSE, %s, %s)
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
                        json.dumps(source.get("dataDefaults") or {}),
                        json.dumps(source.get("masterConfig") or {}),
                        created_by,
                        owner,
                    ),
                )
                new_row = cur.fetchone()
                new_id = new_row["id"]
                for slide in slides:
                    cur.execute(
                        """
                        INSERT INTO tv_dashboard.slides (
                          playlist_id, sort_order, slide_type, duration_sec, title,
                          native_screen_key, native_config, external_url, external_sandbox, is_active,
                          transition_style
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
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
                            slide.get("transitionStyle"),
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
                "transitionStyle": slide.get("transitionStyle"),
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
                      native_screen_key, native_config, external_url, external_sandbox, transition_style
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
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
                        payload.get("transitionStyle"),
                    ),
                )
                row = cur.fetchone()
                self._touch_playlist_updated_at(cur, playlist_id)
            conn.commit()
        return _row_to_slide(row)

    def update_slide(self, slide_id: UUID, payload: dict[str, Any]) -> dict[str, Any]:
        fields: list[str] = []
        values: list[Any] = []
        if "transitionStyle" in payload:
            if payload["transitionStyle"] is None:
                fields.append("transition_style = NULL")
            else:
                fields.append("transition_style = %s")
                values.append(payload["transitionStyle"])
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
                if row:
                    self._touch_playlist_updated_at(cur, UUID(str(row["playlist_id"])))
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
                    "DELETE FROM tv_dashboard.slides WHERE id = %s RETURNING playlist_id",
                    (str(slide_id),),
                )
                row = cur.fetchone()
                if row:
                    self._touch_playlist_updated_at(cur, UUID(str(row["playlist_id"])))
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
                self._touch_playlist_updated_at(cur, playlist_id)
            conn.commit()
        return self.list_slides(playlist_id)


def load_native_screens_catalog() -> list[dict[str, Any]]:
    data = json.loads(NATIVE_SCREENS_PATH.read_text(encoding="utf-8"))
    return list(data.get("screens") or [])
