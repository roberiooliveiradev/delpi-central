from __future__ import annotations

from typing import Any

from psycopg.types.json import Json

from cx_app.infrastructure.persistence.plugins_postgres_connection import (
    CX_SCHEMA_NAME,
    get_connection,
)

_RESPONSES = f'"{CX_SCHEMA_NAME}".form_responses'
_ANSWERS = f'"{CX_SCHEMA_NAME}".form_answers'

_RESPONSE_COLUMNS = "id, form_id, respondent_name, respondent_company, created_at"
_ANSWER_COLUMNS = "id, response_id, question_id, answer_text, answer_rating, answer_choices"


class FormResponseRepository:
    def create(
        self, response: dict[str, Any], answers: list[dict[str, Any]]
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_RESPONSES}
                        (form_id, respondent_name, respondent_company)
                    VALUES (%(form_id)s, %(respondent_name)s, %(respondent_company)s)
                    RETURNING {_RESPONSE_COLUMNS}
                    """,
                    response,
                )
                row = cur.fetchone()
                response_id = row["id"]
                for a in answers:
                    cur.execute(
                        f"""
                        INSERT INTO {_ANSWERS}
                            (response_id, question_id, answer_text, answer_rating, answer_choices)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            response_id,
                            a["question_id"],
                            a.get("answer_text"),
                            a.get("answer_rating"),
                            Json(a["answer_choices"]) if a.get("answer_choices") else None,
                        ),
                    )
            conn.commit()
        return dict(row) if row else {}

    def count_by_form(self, form_id: str) -> int:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) AS total FROM {_RESPONSES} WHERE form_id = %s",
                    (form_id,),
                )
                row = cur.fetchone()
        return int(row["total"]) if row else 0

    def list_by_form(
        self, form_id: str, *, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_RESPONSE_COLUMNS} FROM {_RESPONSES}
                    WHERE form_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (form_id, limit, offset),
                )
                rows = cur.fetchall()
        return [dict(r) for r in rows]

    def answers_by_response_ids(
        self, response_ids: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        if not response_ids:
            return {}
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_ANSWER_COLUMNS} FROM {_ANSWERS}
                    WHERE response_id = ANY(%s::uuid[])
                    """,
                    (response_ids,),
                )
                rows = cur.fetchall()
        grouped: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            grouped.setdefault(str(r["response_id"]), []).append(dict(r))
        return grouped

    def answers_by_form(self, form_id: str) -> list[dict[str, Any]]:
        """Todas as respostas (answer rows) do formulário — base do dashboard."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT a.{_ANSWER_COLUMNS.replace(', ', ', a.')}
                    FROM {_ANSWERS} a
                    JOIN {_RESPONSES} r ON r.id = a.response_id
                    WHERE r.form_id = %s
                    """,
                    (form_id,),
                )
                rows = cur.fetchall()
        return [dict(r) for r in rows]
