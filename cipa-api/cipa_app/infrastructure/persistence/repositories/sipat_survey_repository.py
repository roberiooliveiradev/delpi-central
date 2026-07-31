from __future__ import annotations

from typing import Any

from psycopg.types.json import Json

from cipa_app.infrastructure.persistence.repositories.meeting_minute_repository import (
    _uuid,
    get_connection,
)


class SipatSurveyRepository:
    def list_surveys(self, *, unit_code: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM cipa.sipat_surveys
                    WHERE unit_code = %s AND deleted_at IS NULL
                    ORDER BY created_at DESC
                    """,
                    (unit_code,),
                )
                return cur.fetchall()

    def get_survey(self, survey_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM cipa.sipat_surveys
                    WHERE id = %s AND deleted_at IS NULL
                    """,
                    (_uuid(survey_id),),
                )
                return cur.fetchone()

    def get_by_token(self, token: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM cipa.sipat_surveys
                    WHERE public_token = %s AND deleted_at IS NULL
                    """,
                    (token,),
                )
                return cur.fetchone()

    def create_survey(self, fields: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cipa.sipat_surveys (
                        unit_code, title, description, status,
                        opens_at, closes_at, created_by_user_id, updated_by_user_id
                    ) VALUES (%s,%s,%s,'draft',%s,%s,%s,%s)
                    RETURNING *
                    """,
                    (
                        fields["unit_code"],
                        fields["title"],
                        fields.get("description"),
                        fields.get("opens_at"),
                        fields.get("closes_at"),
                        _uuid(fields["created_by_user_id"])
                        if fields.get("created_by_user_id")
                        else None,
                        _uuid(fields["created_by_user_id"])
                        if fields.get("created_by_user_id")
                        else None,
                    ),
                )
                row = cur.fetchone()
                conn.commit()
                return row

    def update_survey(self, survey_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "title",
            "description",
            "status",
            "public_token",
            "qr_filename",
            "opens_at",
            "closes_at",
            "updated_by_user_id",
            "response_count",
        }
        sets: list[str] = ["updated_at = NOW()"]
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = %s")
            if key == "updated_by_user_id" and value:
                params.append(_uuid(value))
            else:
                params.append(value)
        params.append(_uuid(survey_id))
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE cipa.sipat_surveys
                    SET {", ".join(sets)}
                    WHERE id = %s AND deleted_at IS NULL
                    RETURNING *
                    """,
                    params,
                )
                row = cur.fetchone()
                conn.commit()
                return row

    def soft_delete(self, survey_id: str, *, actor_user_id: str | None) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE cipa.sipat_surveys
                    SET deleted_at = NOW(),
                        updated_at = NOW(),
                        updated_by_user_id = %s
                    WHERE id = %s AND deleted_at IS NULL
                    RETURNING *
                    """,
                    (
                        _uuid(actor_user_id) if actor_user_id else None,
                        _uuid(survey_id),
                    ),
                )
                row = cur.fetchone()
                conn.commit()
                return row

    def list_questions(self, survey_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM cipa.sipat_questions
                    WHERE survey_id = %s
                    ORDER BY position ASC, created_at ASC
                    """,
                    (_uuid(survey_id),),
                )
                return cur.fetchall()

    def replace_questions(
        self, survey_id: str, questions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM cipa.sipat_questions WHERE survey_id = %s",
                    (_uuid(survey_id),),
                )
                rows: list[dict[str, Any]] = []
                for index, item in enumerate(questions):
                    options = item.get("options")
                    cur.execute(
                        """
                        INSERT INTO cipa.sipat_questions (
                            survey_id, position, question_type, label,
                            help_text, is_required, options
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                        RETURNING *
                        """,
                        (
                            _uuid(survey_id),
                            int(item.get("position", index)),
                            item["question_type"],
                            item["label"],
                            item.get("help_text"),
                            bool(item.get("is_required", True)),
                            Json(options) if options is not None else None,
                        ),
                    )
                    rows.append(cur.fetchone())
                conn.commit()
                return rows

    def create_response_with_answers(
        self,
        *,
        survey_id: str,
        answers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cipa.sipat_responses (survey_id)
                    VALUES (%s)
                    RETURNING *
                    """,
                    (_uuid(survey_id),),
                )
                response = cur.fetchone()
                response_id = response["id"]
                for answer in answers:
                    cur.execute(
                        """
                        INSERT INTO cipa.sipat_answers (
                            response_id, question_id, value_text, value_json
                        ) VALUES (%s,%s,%s,%s)
                        """,
                        (
                            response_id,
                            _uuid(answer["question_id"]),
                            answer.get("value_text"),
                            Json(answer["value_json"])
                            if answer.get("value_json") is not None
                            else None,
                        ),
                    )
                cur.execute(
                    """
                    UPDATE cipa.sipat_surveys
                    SET response_count = response_count + 1, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (_uuid(survey_id),),
                )
                conn.commit()
                return response

    def list_answers_for_survey(self, survey_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT a.question_id, a.value_text, a.value_json
                    FROM cipa.sipat_answers a
                    INNER JOIN cipa.sipat_responses r ON r.id = a.response_id
                    WHERE r.survey_id = %s
                    """,
                    (_uuid(survey_id),),
                )
                return cur.fetchall()

    def list_response_answer_rows(self, survey_id: str) -> list[dict[str, Any]]:
        """Linhas planas para export (ordem cronológica, sem PII)."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        r.id AS response_id,
                        r.created_at,
                        a.question_id,
                        a.value_text,
                        a.value_json
                    FROM cipa.sipat_responses r
                    LEFT JOIN cipa.sipat_answers a ON a.response_id = r.id
                    WHERE r.survey_id = %s
                    ORDER BY r.created_at ASC, r.id ASC
                    """,
                    (_uuid(survey_id),),
                )
                return cur.fetchall()
