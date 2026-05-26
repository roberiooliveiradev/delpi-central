from __future__ import annotations

import json
from uuid import uuid4

from si_app.domain.ports.strategic_indicators.change_request_repository_port import (
    StrategicIndicatorsChangeRequestRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresStrategicIndicatorsChangeRequestRepository(
    PluginBaseRepository, StrategicIndicatorsChangeRequestRepositoryPort
):
    def list_change_requests(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        count_row = self.fetch_one(
            """
            SELECT COUNT(*) AS total
            FROM strategic_indicators.settings_change_requests
            """
        )
        total = int((count_row or {}).get("total") or 0)

        query = """
            SELECT
                id,
                request_code,
                title,
                description,
                target_block,
                proposed_payload,
                status,
                created_by_user_id,
                created_by_email,
                submitted_by_user_id,
                submitted_by_email,
                submitted_at,
                created_at,
                updated_at
            FROM strategic_indicators.settings_change_requests
            ORDER BY created_at DESC
        """
        params: list = []

        if limit is not None:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

        rows = self.fetch_all(query, tuple(params))
        return rows, total

    def create_change_request(
        self,
        *,
        title: str,
        description: str,
        target_block: str,
        proposed_payload: dict,
        actor_user_id: str | None,
    ) -> dict:
        request_code = f"SI-CR-{str(uuid4())[:8].upper()}"

        query = """
            INSERT INTO strategic_indicators.settings_change_requests (
                request_code,
                title,
                description,
                target_block,
                proposed_payload,
                created_by_user_id,
                created_by_email
            )
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
            RETURNING
                id,
                request_code,
                title,
                description,
                target_block,
                proposed_payload,
                status,
                created_by_user_id,
                created_by_email,
                submitted_by_user_id,
                submitted_by_email,
                submitted_at,
                created_at,
                updated_at
        """

        return self.execute_returning_one(
            query,
            (
                request_code,
                title,
                description,
                target_block,
                json.dumps(proposed_payload, ensure_ascii=False),
                actor_user_id,
                None,
            ),
        )

    def add_comment(
        self,
        *,
        change_request_id: str,
        comment_text: str,
        actor_user_id: str | None,
    ) -> dict:
        query = """
            INSERT INTO strategic_indicators.settings_change_request_comments (
                change_request_id,
                comment_text,
                created_by_user_id,
                created_by_email
            )
            VALUES (%s, %s, %s, %s)
            RETURNING
                id,
                change_request_id,
                comment_text,
                created_by_user_id,
                created_by_email,
                created_at
        """

        return self.execute_returning_one(
            query,
            (
                change_request_id,
                comment_text,
                actor_user_id,
                None,
            ),
        )

    def submit_change_request(
        self,
        *,
        change_request_id: str,
        actor_user_id: str | None,
    ) -> dict:
        query = """
            UPDATE strategic_indicators.settings_change_requests
            SET
                status = 'submitted',
                submitted_by_user_id = %s,
                submitted_by_email = %s,
                submitted_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            RETURNING
                id,
                request_code,
                title,
                description,
                target_block,
                proposed_payload,
                status,
                created_by_user_id,
                created_by_email,
                submitted_by_user_id,
                submitted_by_email,
                submitted_at,
                created_at,
                updated_at
        """

        return self.execute_returning_one(
            query,
            (
                actor_user_id,
                None,
                change_request_id,
            ),
        )