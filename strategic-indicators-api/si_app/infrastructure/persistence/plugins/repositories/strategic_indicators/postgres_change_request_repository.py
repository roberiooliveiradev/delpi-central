from __future__ import annotations

import json
from uuid import uuid4

from si_app.application.services.strategic_indicators.admin_write_conflict_error import (
    StrategicIndicatorsAdminConflictError,
)
from si_app.domain.ports.strategic_indicators.change_request_repository_port import (
    StrategicIndicatorsChangeRequestRepositoryPort,
)
from si_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_CR_RETURNING = """
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
        updated_at,
        xmin::text AS row_xmin
"""


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
                updated_at,
                xmin::text AS row_xmin
            FROM strategic_indicators.settings_change_requests
            ORDER BY created_at DESC
        """
        params: list = []

        if limit is not None:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

        rows = self.fetch_all(query, tuple(params))
        return rows, total

    def get_change_request(
        self,
        *,
        change_request_id: str,
    ) -> dict | None:
        return self.fetch_one(
            """
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
                updated_at,
                xmin::text AS row_xmin
            FROM strategic_indicators.settings_change_requests
            WHERE id = %s
            """,
            (change_request_id,),
        )

    def create_change_request(
        self,
        *,
        title: str,
        description: str,
        target_block: str,
        proposed_payload: dict,
        actor_user_id: str | None,
        idempotency_key: str | None = None,
    ) -> dict:
        # Replay protection: a retried create carrying the same idempotency
        # key returns the already committed row instead of duplicating the
        # request after an ambiguous timeout.
        if idempotency_key:
            existing = self.fetch_one(
                """
                SELECT id
                FROM strategic_indicators.settings_change_requests
                WHERE idempotency_key = %s
                """,
                (idempotency_key,),
            )
            if existing:
                row = self.get_change_request(change_request_id=str(existing["id"]))
                if row is not None:
                    return row

        request_code = f"SI-CR-{str(uuid4())[:8].upper()}"

        row = self.execute_returning_one(
            f"""
            INSERT INTO strategic_indicators.settings_change_requests (
                request_code,
                title,
                description,
                target_block,
                proposed_payload,
                created_by_user_id,
                created_by_email,
                idempotency_key
            )
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)
            ON CONFLICT (idempotency_key)
                WHERE idempotency_key IS NOT NULL
            DO NOTHING
            {_CR_RETURNING}
            """,
            (
                request_code,
                title,
                description,
                target_block,
                json.dumps(proposed_payload, ensure_ascii=False),
                actor_user_id,
                None,
                idempotency_key,
            ),
        )
        if row is None and idempotency_key:
            # Lost the insert race to a concurrent replay: read the winner.
            existing = self.fetch_one(
                """
                SELECT id
                FROM strategic_indicators.settings_change_requests
                WHERE idempotency_key = %s
                """,
                (idempotency_key,),
            )
            if existing:
                row = self.get_change_request(change_request_id=str(existing["id"]))
        return row

    def add_comment(
        self,
        *,
        change_request_id: str,
        comment_text: str,
        actor_user_id: str | None,
        idempotency_key: str | None = None,
    ) -> dict:
        # Replay protection: same idempotency key returns the committed
        # comment instead of inserting a duplicate.
        if idempotency_key:
            existing = self.fetch_one(
                """
                SELECT
                    id,
                    change_request_id,
                    comment_text,
                    created_by_user_id,
                    created_by_email,
                    created_at,
                    xmin::text AS row_xmin
                FROM strategic_indicators.settings_change_request_comments
                WHERE idempotency_key = %s
                """,
                (idempotency_key,),
            )
            if existing:
                return existing

        row = self.execute_returning_one(
            """
            INSERT INTO strategic_indicators.settings_change_request_comments (
                change_request_id,
                comment_text,
                created_by_user_id,
                created_by_email,
                idempotency_key
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (idempotency_key)
                WHERE idempotency_key IS NOT NULL
            DO NOTHING
            RETURNING
                id,
                change_request_id,
                comment_text,
                created_by_user_id,
                created_by_email,
                created_at,
                xmin::text AS row_xmin
            """,
            (
                change_request_id,
                comment_text,
                actor_user_id,
                None,
                idempotency_key,
            ),
        )
        if row is None and idempotency_key:
            existing = self.fetch_one(
                """
                SELECT
                    id,
                    change_request_id,
                    comment_text,
                    created_by_user_id,
                    created_by_email,
                    created_at,
                    xmin::text AS row_xmin
                FROM strategic_indicators.settings_change_request_comments
                WHERE idempotency_key = %s
                """,
                (idempotency_key,),
            )
            if existing:
                return existing
        return row

    def submit_change_request(
        self,
        *,
        change_request_id: str,
        actor_user_id: str | None,
        expected_xmin: str | None = None,
    ) -> dict:
        # Guarded transition: the status precondition is evaluated in the
        # same atomic statement as the mutation — resubmitting an already
        # submitted request is a typed conflict, not a silent re-stamp.
        current = self.get_change_request(change_request_id=change_request_id)
        if current is None:
            raise ValueError("Solicitação de alteração não encontrada.")

        row = self.execute_returning_one(
            f"""
            UPDATE strategic_indicators.settings_change_requests
            SET
                status = 'submitted',
                submitted_by_user_id = %s,
                submitted_by_email = %s,
                submitted_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
              AND status = 'draft'
              AND (%s::text IS NULL OR xmin::text = %s)
            {_CR_RETURNING}
            """,
            (
                actor_user_id,
                None,
                change_request_id,
                expected_xmin,
                expected_xmin,
            ),
        )
        if row is None:
            fresh = self.get_change_request(change_request_id=change_request_id)
            if fresh is not None and fresh.get("status") == "submitted":
                if expected_xmin is not None and str(
                    fresh.get("row_xmin")
                ) != str(expected_xmin):
                    raise StrategicIndicatorsAdminConflictError(
                        "A solicitação foi alterada desde a leitura "
                        "(expected_xmin desatualizado)."
                    )
                # Idempotent replay: the transition already happened.
                return fresh
            if expected_xmin is not None and (
                fresh is None or str(fresh.get("row_xmin")) != str(expected_xmin)
            ):
                raise StrategicIndicatorsAdminConflictError(
                    "A solicitação foi alterada desde a leitura "
                    "(expected_xmin desatualizado)."
                )
            raise StrategicIndicatorsAdminConflictError(
                f"A solicitação não está em estado 'draft' "
                f"(status atual: {fresh.get('status') if fresh else 'desconhecido'})."
            )
        return row
