from __future__ import annotations

from typing import Any

from psycopg.types.json import Json

from cx_app.infrastructure.persistence.plugins_postgres_connection import (
    CX_SCHEMA_NAME,
    get_connection,
)

_FORMS = f'"{CX_SCHEMA_NAME}".forms'
_QUESTIONS = f'"{CX_SCHEMA_NAME}".form_questions'
_PAGES = f'"{CX_SCHEMA_NAME}".form_pages'

_FORM_COLUMNS = (
    "id, public_token, title, description, qr_filename, is_active, response_count, "
    "one_question_per_page, background_image_filename, background_fit, "
    "created_by, created_by_name, created_at, updated_at"
)
_QUESTION_COLUMNS = (
    "id, form_id, page_id, position, question_type, label, help_text, is_required, "
    "options, point_image_filename, is_active, created_at, updated_at"
)
_PAGE_COLUMNS = (
    "id, form_id, position, title, background_image_filename, point_image_filename, "
    "created_at, updated_at"
)


class FormRepository:
    # ----- formulários -----------------------------------------------------

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_FORMS}
                        (public_token, title, description, qr_filename,
                         one_question_per_page, background_fit,
                         created_by, created_by_name)
                    VALUES
                        (%(public_token)s, %(title)s, %(description)s, %(qr_filename)s,
                         %(one_question_per_page)s, %(background_fit)s,
                         %(created_by)s, %(created_by_name)s)
                    RETURNING {_FORM_COLUMNS}
                    """,
                    {
                        "public_token": data["public_token"],
                        "title": data["title"],
                        "description": data.get("description"),
                        "qr_filename": data.get("qr_filename"),
                        "one_question_per_page": bool(data.get("one_question_per_page", False)),
                        "background_fit": data.get("background_fit") or "scale",
                        "created_by": data.get("created_by"),
                        "created_by_name": data.get("created_by_name"),
                    },
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else {}

    def get_by_id(self, form_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_FORM_COLUMNS} FROM {_FORMS} WHERE id = %s", (form_id,)
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def get_by_token(self, token: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_FORM_COLUMNS} FROM {_FORMS} WHERE public_token = %s",
                    (token,),
                )
                row = cur.fetchone()
        return dict(row) if row else None

    def list(self) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT {_FORM_COLUMNS} FROM {_FORMS} ORDER BY created_at DESC")
                rows = cur.fetchall()
        return [dict(r) for r in rows]

    def update(self, form_id: str, fields: dict[str, Any]) -> dict[str, Any] | None:
        if not fields:
            return self.get_by_id(form_id)
        sets = ", ".join(f"{key} = %({key})s" for key in fields)
        params = {**fields, "id": form_id}
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_FORMS}
                    SET {sets}, updated_at = NOW()
                    WHERE id = %(id)s
                    RETURNING {_FORM_COLUMNS}
                    """,
                    params,
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else None

    def set_active(self, form_id: str, is_active: bool) -> dict[str, Any] | None:
        return self.update(form_id, {"is_active": is_active})

    def increment_response_count(self, form_id: str) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE {_FORMS} SET response_count = response_count + 1 WHERE id = %s",
                    (form_id,),
                )
            conn.commit()

    def delete(self, form_id: str) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {_FORMS} WHERE id = %s", (form_id,))
                deleted = cur.rowcount > 0
            conn.commit()
        return deleted

    # ----- páginas ---------------------------------------------------------

    def list_pages(self, form_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_PAGE_COLUMNS} FROM {_PAGES}
                    WHERE form_id = %s
                    ORDER BY position ASC, created_at ASC
                    """,
                    (form_id,),
                )
                rows = cur.fetchall()
        return [dict(r) for r in rows]

    def replace_pages(
        self, form_id: str, pages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        keep_ids: list[str] = []
        with get_connection() as conn:
            with conn.cursor() as cur:
                for position, page in enumerate(pages):
                    bg = page.get("background_image_filename")
                    point = page.get("point_image_filename")
                    title = page.get("title")
                    if page.get("id"):
                        cur.execute(
                            f"""
                            UPDATE {_PAGES}
                            SET position = %s, title = %s,
                                background_image_filename = %s,
                                point_image_filename = %s,
                                updated_at = NOW()
                            WHERE id = %s AND form_id = %s
                            RETURNING id
                            """,
                            (position, title, bg, point, page["id"], form_id),
                        )
                        updated = cur.fetchone()
                        if updated:
                            keep_ids.append(str(updated["id"]))
                            continue
                    cur.execute(
                        f"""
                        INSERT INTO {_PAGES}
                            (form_id, position, title,
                             background_image_filename, point_image_filename)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (form_id, position, title, bg, point),
                    )
                    inserted = cur.fetchone()
                    keep_ids.append(str(inserted["id"]))

                if keep_ids:
                    cur.execute(
                        f"""
                        DELETE FROM {_PAGES}
                        WHERE form_id = %s AND id <> ALL(%s::uuid[])
                        """,
                        (form_id, keep_ids),
                    )
                else:
                    cur.execute(f"DELETE FROM {_PAGES} WHERE form_id = %s", (form_id,))
            conn.commit()
        return self.list_pages(form_id)

    # ----- perguntas -------------------------------------------------------

    def list_questions(
        self, form_id: str, *, active_only: bool = False
    ) -> list[dict[str, Any]]:
        clause = "AND is_active = TRUE" if active_only else ""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_QUESTION_COLUMNS} FROM {_QUESTIONS}
                    WHERE form_id = %s {clause}
                    ORDER BY position ASC, created_at ASC
                    """,
                    (form_id,),
                )
                rows = cur.fetchall()
        return [dict(r) for r in rows]

    def replace_questions(
        self, form_id: str, questions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Faz upsert das perguntas informadas e desativa (soft-delete) as
        que sumiram — preserva as respostas já coletadas."""
        keep_ids: list[str] = []
        with get_connection() as conn:
            with conn.cursor() as cur:
                for position, q in enumerate(questions):
                    options = Json(q["options"]) if q.get("options") else None
                    page_id = q.get("page_id")
                    point_image = q.get("point_image_filename")
                    if q.get("id"):
                        cur.execute(
                            f"""
                            UPDATE {_QUESTIONS}
                            SET position = %s, page_id = %s, question_type = %s, label = %s,
                                help_text = %s, is_required = %s, options = %s,
                                point_image_filename = %s,
                                is_active = TRUE, updated_at = NOW()
                            WHERE id = %s AND form_id = %s
                            RETURNING id
                            """,
                            (
                                position,
                                page_id,
                                q["question_type"],
                                q["label"],
                                q.get("help_text"),
                                bool(q.get("is_required")),
                                options,
                                point_image,
                                q["id"],
                                form_id,
                            ),
                        )
                        updated = cur.fetchone()
                        if updated:
                            keep_ids.append(str(updated["id"]))
                            continue
                    cur.execute(
                        f"""
                        INSERT INTO {_QUESTIONS}
                            (form_id, page_id, position, question_type, label, help_text,
                             is_required, options, point_image_filename)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            form_id,
                            page_id,
                            position,
                            q["question_type"],
                            q["label"],
                            q.get("help_text"),
                            bool(q.get("is_required")),
                            options,
                            point_image,
                        ),
                    )
                    inserted = cur.fetchone()
                    keep_ids.append(str(inserted["id"]))

                if keep_ids:
                    cur.execute(
                        f"""
                        UPDATE {_QUESTIONS}
                        SET is_active = FALSE, updated_at = NOW()
                        WHERE form_id = %s AND id <> ALL(%s::uuid[])
                        """,
                        (form_id, keep_ids),
                    )
                else:
                    cur.execute(
                        f"UPDATE {_QUESTIONS} SET is_active = FALSE WHERE form_id = %s",
                        (form_id,),
                    )
            conn.commit()
        return self.list_questions(form_id, active_only=True)
