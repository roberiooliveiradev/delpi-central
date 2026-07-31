from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from tv_app.infrastructure.persistence.plugins_postgres_connection import get_connection

_KEY_SAFE = re.compile(r"[^a-zA-Z0-9_-]+")


def slugify_template_key(raw: str, *, fallback: str = "template") -> str:
    cleaned = _KEY_SAFE.sub("_", (raw or "").strip()).strip("_").lower()
    return cleaned or fallback


def _row_to_template(row: dict[str, Any]) -> dict[str, Any]:
    native_config = row.get("native_config")
    if isinstance(native_config, str):
        native_config = json.loads(native_config)
    thumbnail = row.get("thumbnail_json")
    if isinstance(thumbnail, str):
        thumbnail = json.loads(thumbnail)
    return {
        "id": str(row["id"]),
        "key": row["key"],
        "label": row["label"],
        "description": row.get("description"),
        "nativeScreenKey": row.get("native_screen_key") or "custom_message",
        "nativeConfig": dict(native_config or {}),
        "durationSec": row.get("duration_sec"),
        "status": row["status"],
        "isSystem": bool(row.get("is_system")),
        "version": int(row.get("version") or 1),
        "thumbnailJson": thumbnail,
        "ownerUserId": row.get("owner_user_id"),
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
        "updatedAt": row["updated_at"].isoformat() if row.get("updated_at") else None,
        "updatedBy": row.get("updated_by"),
        "slideType": "native",
        "title": row["label"],
        "source": "library",
    }


class SlideTemplateRepository:
    def list(
        self,
        *,
        status: str | None = None,
        q: str | None = None,
        is_system: bool | None = None,
        exclude_archived_by_default: bool = True,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = %s")
            params.append(status)
        elif exclude_archived_by_default:
            clauses.append("status <> %s")
            params.append("archived")
        if is_system is not None:
            clauses.append("is_system = %s")
            params.append(is_system)
        if q and q.strip():
            clauses.append("(label ILIKE %s OR key ILIKE %s OR COALESCE(description, '') ILIKE %s)")
            like = f"%{q.strip()}%"
            params.extend([like, like, like])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT * FROM tv_dashboard.slide_templates
            {where}
            ORDER BY label ASC, key ASC
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        return [_row_to_template(row) for row in rows]

    def get(self, template_id: UUID) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM tv_dashboard.slide_templates WHERE id = %s",
                    (str(template_id),),
                )
                row = cur.fetchone()
        return _row_to_template(row) if row else None

    def get_by_key(self, key: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM tv_dashboard.slide_templates WHERE key = %s",
                    (key,),
                )
                row = cur.fetchone()
        return _row_to_template(row) if row else None

    def create(
        self,
        *,
        key: str,
        label: str,
        description: str | None,
        native_screen_key: str,
        native_config: dict[str, Any],
        duration_sec: int | None,
        status: str,
        is_system: bool,
        owner_user_id: str | None,
        updated_by: str | None,
        thumbnail_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.slide_templates (
                        key, label, description, native_screen_key, native_config,
                        duration_sec, status, is_system, owner_user_id, updated_by,
                        thumbnail_json
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING *
                    """,
                    (
                        key,
                        label,
                        description,
                        native_screen_key,
                        json.dumps(native_config or {}),
                        duration_sec,
                        status,
                        is_system,
                        owner_user_id,
                        updated_by,
                        json.dumps(thumbnail_json) if thumbnail_json is not None else None,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _row_to_template(row)

    def upsert_system(
        self,
        *,
        key: str,
        label: str,
        description: str | None,
        native_screen_key: str,
        native_config: dict[str, Any],
        duration_sec: int | None,
        updated_by: str | None = "system-seed",
    ) -> dict[str, Any]:
        """Idempotent seed: insert or update system row by key (preserves id/version bump)."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tv_dashboard.slide_templates (
                        key, label, description, native_screen_key, native_config,
                        duration_sec, status, is_system, updated_by
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, 'published', TRUE, %s)
                    ON CONFLICT (key) DO UPDATE SET
                        label = EXCLUDED.label,
                        description = EXCLUDED.description,
                        native_screen_key = EXCLUDED.native_screen_key,
                        native_config = EXCLUDED.native_config,
                        duration_sec = EXCLUDED.duration_sec,
                        status = 'published',
                        is_system = TRUE,
                        updated_at = NOW(),
                        updated_by = EXCLUDED.updated_by,
                        version = tv_dashboard.slide_templates.version + 1
                    WHERE tv_dashboard.slide_templates.is_system = TRUE
                    RETURNING *
                    """,
                    (
                        key,
                        label,
                        description,
                        native_screen_key,
                        json.dumps(native_config or {}),
                        duration_sec,
                        updated_by,
                    ),
                )
                row = cur.fetchone()
                if row is None:
                    # Key exists as non-system — leave alone; fetch existing
                    cur.execute(
                        "SELECT * FROM tv_dashboard.slide_templates WHERE key = %s",
                        (key,),
                    )
                    row = cur.fetchone()
            conn.commit()
        return _row_to_template(row)

    def update(
        self,
        template_id: UUID,
        *,
        expected_version: int,
        label: str | None = None,
        description: str | None = None,
        native_screen_key: str | None = None,
        native_config: dict[str, Any] | None = None,
        duration_sec: int | None = None,
        status: str | None = None,
        thumbnail_json: dict[str, Any] | None = None,
        clear_thumbnail: bool = False,
        content_changed: bool = False,
        updated_by: str | None = None,
    ) -> dict[str, Any] | None:
        """Returns updated row, raises nothing; None if not found; empty dict sentinel for conflict.

        Conflict: returns {"_conflict": True}.
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM tv_dashboard.slide_templates WHERE id = %s FOR UPDATE",
                    (str(template_id),),
                )
                row = cur.fetchone()
                if not row:
                    conn.commit()
                    return None
                if int(row["version"]) != int(expected_version):
                    conn.commit()
                    return {"_conflict": True, "current": _row_to_template(row)}

                sets: list[str] = ["updated_at = NOW()", "version = version + 1"]
                params: list[Any] = []
                if label is not None:
                    sets.append("label = %s")
                    params.append(label)
                if description is not None:
                    sets.append("description = %s")
                    params.append(description)
                if native_screen_key is not None:
                    sets.append("native_screen_key = %s")
                    params.append(native_screen_key)
                if native_config is not None:
                    sets.append("native_config = %s::jsonb")
                    params.append(json.dumps(native_config))
                if duration_sec is not None:
                    sets.append("duration_sec = %s")
                    params.append(duration_sec)
                if clear_thumbnail:
                    sets.append("thumbnail_json = NULL")
                elif thumbnail_json is not None:
                    sets.append("thumbnail_json = %s::jsonb")
                    params.append(json.dumps(thumbnail_json))
                if updated_by is not None:
                    sets.append("updated_by = %s")
                    params.append(updated_by)

                next_status = status
                if content_changed and row["status"] == "published" and status is None:
                    next_status = "draft"
                if next_status is not None:
                    sets.append("status = %s")
                    params.append(next_status)

                params.append(str(template_id))
                cur.execute(
                    f"""
                    UPDATE tv_dashboard.slide_templates
                    SET {', '.join(sets)}
                    WHERE id = %s
                    RETURNING *
                    """,
                    params,
                )
                updated = cur.fetchone()
            conn.commit()
        return _row_to_template(updated)

    def set_status(
        self,
        template_id: UUID,
        *,
        status: str,
        updated_by: str | None,
    ) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tv_dashboard.slide_templates
                    SET status = %s, updated_at = NOW(), updated_by = %s, version = version + 1
                    WHERE id = %s
                    RETURNING *
                    """,
                    (status, updated_by, str(template_id)),
                )
                row = cur.fetchone()
            conn.commit()
        return _row_to_template(row) if row else None

    def delete(self, template_id: UUID) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM tv_dashboard.slide_templates
                    WHERE id = %s
                    RETURNING *
                    """,
                    (str(template_id),),
                )
                row = cur.fetchone()
            conn.commit()
        return _row_to_template(row) if row else None

    def allocate_unique_key(self, base: str) -> str:
        candidate = slugify_template_key(base)
        with get_connection() as conn:
            with conn.cursor() as cur:
                for index in range(0, 50):
                    key = candidate if index == 0 else f"{candidate}_{index}"
                    cur.execute(
                        "SELECT 1 FROM tv_dashboard.slide_templates WHERE key = %s",
                        (key,),
                    )
                    if cur.fetchone() is None:
                        return key
        from uuid import uuid4

        return f"{candidate}_{uuid4().hex[:8]}"
