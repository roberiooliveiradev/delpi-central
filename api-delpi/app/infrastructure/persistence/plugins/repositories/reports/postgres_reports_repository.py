from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None:
        return None
    return str(value)


def _as_dict(params: Any) -> dict[str, Any]:
    if params is None:
        return {}
    if isinstance(params, dict):
        return dict(params)
    if isinstance(params, str):
        loaded = json.loads(params)
        if isinstance(loaded, dict):
            return loaded
    return {}


class PostgresReportsRepository(PluginBaseRepository):
    """Persistência Delpi Reports (schema ``reports``)."""

    def list_definitions(self) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT id, name, provider_key, params, active,
                   created_by_user_id, created_at, updated_at
              FROM reports.report_definitions
             ORDER BY created_at DESC, name ASC
            """
        )
        return [self.definition_to_payload(row) for row in rows]

    def get_definition(self, definition_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            """
            SELECT id, name, provider_key, params, active,
                   created_by_user_id, created_at, updated_at
              FROM reports.report_definitions
             WHERE id = %s
            """,
            (definition_id,),
        )
        if row is None:
            return None
        return self.definition_to_payload(row)

    def create_definition(
        self,
        *,
        name: str,
        provider_key: str,
        params: dict[str, Any],
        active: bool,
        created_by_user_id: str | None,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO reports.report_definitions (
                name, provider_key, params, active, created_by_user_id
            ) VALUES (
                %s, %s, %s::jsonb, %s, %s
            )
            RETURNING id, name, provider_key, params, active,
                      created_by_user_id, created_at, updated_at
            """,
            (
                name,
                provider_key,
                json.dumps(params),
                active,
                created_by_user_id,
            ),
        )
        if row is None:
            raise PluginsRepositoryError("Falha ao criar definição de relatório.")
        return self.definition_to_payload(row)

    def update_definition(
        self,
        *,
        definition_id: str,
        name: str | None = None,
        provider_key: str | None = None,
        params: dict[str, Any] | None = None,
        active: bool | None = None,
    ) -> dict[str, Any] | None:
        current = self.fetch_one(
            """
            SELECT id, name, provider_key, params, active,
                   created_by_user_id, created_at, updated_at
              FROM reports.report_definitions
             WHERE id = %s
            """,
            (definition_id,),
        )
        if current is None:
            return None

        next_name = name if name is not None else current["name"]
        next_provider = (
            provider_key if provider_key is not None else current["provider_key"]
        )
        next_params = params if params is not None else _as_dict(current.get("params"))
        next_active = active if active is not None else bool(current["active"])

        row = self.execute_returning_one(
            """
            UPDATE reports.report_definitions
               SET name = %s,
                   provider_key = %s,
                   params = %s::jsonb,
                   active = %s,
                   updated_at = NOW()
             WHERE id = %s
            RETURNING id, name, provider_key, params, active,
                      created_by_user_id, created_at, updated_at
            """,
            (
                next_name,
                next_provider,
                json.dumps(next_params),
                next_active,
                definition_id,
            ),
        )
        if row is None:
            return None
        return self.definition_to_payload(row)

    def list_runs(
        self,
        *,
        definition_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 200))
        if definition_id:
            rows = self.fetch_all(
                """
                SELECT id, definition_id, trigger, status,
                       started_at, finished_at, summary, error, created_at
                  FROM reports.report_runs
                 WHERE definition_id = %s
                 ORDER BY created_at DESC
                 LIMIT %s
                """,
                (definition_id, limit),
            )
        else:
            rows = self.fetch_all(
                """
                SELECT id, definition_id, trigger, status,
                       started_at, finished_at, summary, error, created_at
                  FROM reports.report_runs
                 ORDER BY created_at DESC
                 LIMIT %s
                """,
                (limit,),
            )
        return [self.run_to_payload(row) for row in rows]

    def list_recipients(self, definition_id: str) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT id, definition_id, user_id, email, active,
                   created_at, updated_at
              FROM reports.report_recipients
             WHERE definition_id = %s
             ORDER BY email ASC
            """,
            (definition_id,),
        )
        return [self.recipient_to_payload(row) for row in rows]

    def list_active_recipients(self, definition_id: str) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT id, definition_id, user_id, email, active,
                   created_at, updated_at
              FROM reports.report_recipients
             WHERE definition_id = %s
               AND active = TRUE
             ORDER BY email ASC
            """,
            (definition_id,),
        )
        return [self.recipient_to_payload(row) for row in rows]

    def replace_recipients(
        self,
        *,
        definition_id: str,
        items: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        self.execute(
            "DELETE FROM reports.report_recipients WHERE definition_id = %s",
            (definition_id,),
        )
        for item in items:
            user_id = str(item.get("userId") or item.get("user_id") or "").strip()
            email = str(item.get("email") or "").strip()
            if not user_id or not email:
                continue
            self.execute(
                """
                INSERT INTO reports.report_recipients (
                    definition_id, user_id, email, active
                ) VALUES (%s, %s, %s, TRUE)
                """,
                (definition_id, user_id, email),
            )
        return self.list_recipients(definition_id)

    def get_schedule_for_definition(
        self,
        definition_id: str,
    ) -> dict[str, Any] | None:
        row = self.fetch_one(
            """
            SELECT id, definition_id, schedule_kind, cron_expression,
                   timezone, next_run_at, enabled, created_at, updated_at
              FROM reports.report_schedules
             WHERE definition_id = %s
             ORDER BY created_at ASC
             LIMIT 1
            """,
            (definition_id,),
        )
        if row is None:
            return None
        return self.schedule_to_payload(row)

    def upsert_schedule_for_definition(
        self,
        *,
        definition_id: str,
        schedule_kind: str,
        cron_expression: str,
        timezone: str,
        next_run_at: datetime,
        enabled: bool,
    ) -> dict[str, Any]:
        existing = self.fetch_one(
            """
            SELECT id FROM reports.report_schedules
             WHERE definition_id = %s
             ORDER BY created_at ASC
             LIMIT 1
            """,
            (definition_id,),
        )
        if existing is None:
            row = self.execute_returning_one(
                """
                INSERT INTO reports.report_schedules (
                    definition_id, schedule_kind, cron_expression,
                    timezone, next_run_at, enabled
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, definition_id, schedule_kind, cron_expression,
                          timezone, next_run_at, enabled, created_at, updated_at
                """,
                (
                    definition_id,
                    schedule_kind,
                    cron_expression,
                    timezone,
                    next_run_at,
                    enabled,
                ),
            )
        else:
            row = self.execute_returning_one(
                """
                UPDATE reports.report_schedules
                   SET schedule_kind = %s,
                       cron_expression = %s,
                       timezone = %s,
                       next_run_at = %s,
                       enabled = %s,
                       updated_at = NOW()
                 WHERE id = %s
                RETURNING id, definition_id, schedule_kind, cron_expression,
                          timezone, next_run_at, enabled, created_at, updated_at
                """,
                (
                    schedule_kind,
                    cron_expression,
                    timezone,
                    next_run_at,
                    enabled,
                    str(existing["id"]),
                ),
            )
        if row is None:
            raise PluginsRepositoryError("Falha ao gravar agenda do relatório.")
        return self.schedule_to_payload(row)

    def delete_schedule_for_definition(self, definition_id: str) -> bool:
        before = self.get_schedule_for_definition(definition_id)
        if before is None:
            return False
        self.execute(
            "DELETE FROM reports.report_schedules WHERE definition_id = %s",
            (definition_id,),
        )
        return True

    def list_due_schedules(
        self,
        *,
        limit: int = 20,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Lista agendas vencidas (somente leitura). Preferir ``claim_due_schedules``."""
        limit = max(1, min(int(limit), 100))
        now = now or datetime.now(timezone.utc)
        rows = self.fetch_all(
            """
            SELECT s.id, s.definition_id, s.schedule_kind, s.cron_expression,
                   s.timezone, s.next_run_at, s.enabled, s.last_claimed_at,
                   s.created_at, s.updated_at
              FROM reports.report_schedules s
              INNER JOIN reports.report_definitions d
                      ON d.id = s.definition_id
             WHERE s.enabled = TRUE
               AND d.active = TRUE
               AND s.next_run_at IS NOT NULL
               AND s.next_run_at <= %s
             ORDER BY s.next_run_at ASC
             LIMIT %s
            """,
            (now, limit),
        )
        return [self.schedule_to_payload(row) for row in rows]

    def claim_due_schedules(
        self,
        *,
        limit: int = 20,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Claim atômico: ``FOR UPDATE SKIP LOCKED`` + avança ``next_run_at`` no mesmo commit."""
        from app.domain.services.reports.report_schedule_next_run_service import (
            compute_next_run_from_cron,
        )

        limit = max(1, min(int(limit), 100))
        now = now or datetime.now(timezone.utc)
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT s.id, s.definition_id, s.schedule_kind, s.cron_expression,
                           s.timezone, s.next_run_at, s.enabled, s.last_claimed_at,
                           s.created_at, s.updated_at
                      FROM reports.report_schedules s
                      INNER JOIN reports.report_definitions d
                              ON d.id = s.definition_id
                     WHERE s.enabled = TRUE
                       AND d.active = TRUE
                       AND s.next_run_at IS NOT NULL
                       AND s.next_run_at <= %s
                     ORDER BY s.next_run_at ASC
                     FOR UPDATE OF s SKIP LOCKED
                     LIMIT %s
                    """,
                    (now, limit),
                )
                locked = [dict(row) for row in cursor.fetchall()]
                claimed: list[dict[str, Any]] = []
                for row in locked:
                    next_at = compute_next_run_from_cron(
                        schedule_kind=str(row.get("schedule_kind") or ""),
                        cron_expression=row.get("cron_expression"),
                        timezone_name=str(
                            row.get("timezone") or "America/Sao_Paulo"
                        ),
                        after=now,
                    )
                    cursor.execute(
                        """
                        UPDATE reports.report_schedules
                           SET next_run_at = %s,
                               last_claimed_at = %s,
                               updated_at = NOW()
                         WHERE id = %s
                        RETURNING id, definition_id, schedule_kind, cron_expression,
                                  timezone, next_run_at, enabled, last_claimed_at,
                                  created_at, updated_at
                        """,
                        (next_at, now, str(row["id"])),
                    )
                    updated = cursor.fetchone()
                    if updated is not None:
                        claimed.append(self.schedule_to_payload(dict(updated)))
            self.commit()
            return claimed
        except PluginsRepositoryError:
            raise
        except Exception as exc:
            self.rollback()
            raise PluginsRepositoryError(
                "Falha ao reivindicar agendas vencidas de relatórios."
            ) from exc

    def update_schedule_next_run(
        self,
        *,
        schedule_id: str,
        next_run_at: datetime,
    ) -> None:
        self.execute(
            """
            UPDATE reports.report_schedules
               SET next_run_at = %s,
                   updated_at = NOW()
             WHERE id = %s
            """,
            (next_run_at, schedule_id),
        )

    def create_run(
        self,
        *,
        definition_id: str,
        trigger: str,
        status: str = "running",
        summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO reports.report_runs (
                definition_id, trigger, status, started_at, summary
            ) VALUES (
                %s, %s, %s, NOW(), %s::jsonb
            )
            RETURNING id, definition_id, trigger, status,
                      started_at, finished_at, summary, error, created_at
            """,
            (
                definition_id,
                trigger,
                status,
                json.dumps(summary or {}),
            ),
        )
        if row is None:
            raise PluginsRepositoryError("Falha ao criar execução de relatório.")
        return self.run_to_payload(row)

    def finish_run(
        self,
        *,
        run_id: str,
        status: str,
        summary: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            """
            UPDATE reports.report_runs
               SET status = %s,
                   finished_at = NOW(),
                   summary = COALESCE(%s::jsonb, summary),
                   error = %s
             WHERE id = %s
            RETURNING id, definition_id, trigger, status,
                      started_at, finished_at, summary, error, created_at
            """,
            (
                status,
                json.dumps(summary) if summary is not None else None,
                error,
                run_id,
            ),
        )
        if row is None:
            return None
        return self.run_to_payload(row)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            """
            SELECT id, definition_id, trigger, status,
                   started_at, finished_at, summary, error, created_at
              FROM reports.report_runs
             WHERE id = %s
            """,
            (run_id,),
        )
        if row is None:
            return None
        return self.run_to_payload(row)

    def create_delivery(
        self,
        *,
        run_id: str,
        recipient_email: str,
        status: str = "pending",
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO reports.report_deliveries (
                run_id, recipient_email, status
            ) VALUES (%s, %s, %s)
            RETURNING id, run_id, recipient_email, status,
                      provider_message_id, error, sent_at, created_at
            """,
            (run_id, recipient_email, status),
        )
        if row is None:
            raise PluginsRepositoryError("Falha ao criar delivery de relatório.")
        return self.delivery_to_payload(row)

    def finish_delivery(
        self,
        *,
        delivery_id: str,
        status: str,
        error: str | None = None,
        provider_message_id: str | None = None,
    ) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            """
            UPDATE reports.report_deliveries
               SET status = %s,
                   error = %s,
                   provider_message_id = COALESCE(%s, provider_message_id),
                   sent_at = CASE WHEN %s = 'sent' THEN NOW() ELSE sent_at END
             WHERE id = %s
            RETURNING id, run_id, recipient_email, status,
                      provider_message_id, error, sent_at, created_at
            """,
            (status, error, provider_message_id, status, delivery_id),
        )
        if row is None:
            return None
        return self.delivery_to_payload(row)

    def list_deliveries_for_run(self, run_id: str) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT id, run_id, recipient_email, status,
                   provider_message_id, error, sent_at, created_at
              FROM reports.report_deliveries
             WHERE run_id = %s
             ORDER BY created_at ASC
            """,
            (run_id,),
        )
        return [self.delivery_to_payload(row) for row in rows]

    @staticmethod
    def recipient_to_payload(row: dict[str, Any]) -> dict[str, Any]:
        def _id(value: Any) -> str:
            return str(value) if value is not None else ""

        return {
            "id": _id(row.get("id")),
            "definitionId": _id(row.get("definition_id")),
            "userId": str(row.get("user_id") or ""),
            "email": str(row.get("email") or ""),
            "active": bool(row.get("active")),
            "createdAt": _iso(row.get("created_at")),
            "updatedAt": _iso(row.get("updated_at")),
        }

    @staticmethod
    def schedule_to_payload(row: dict[str, Any]) -> dict[str, Any]:
        from app.domain.services.reports.report_schedule_next_run_service import (
            parse_schedule_fields,
        )

        def _id(value: Any) -> str:
            return str(value) if value is not None else ""

        kind = str(row.get("schedule_kind") or "")
        cron = row.get("cron_expression")
        fields = parse_schedule_fields(schedule_kind=kind, cron_expression=cron)
        return {
            "id": _id(row.get("id")),
            "definitionId": _id(row.get("definition_id")),
            "scheduleKind": kind,
            "cronExpression": cron,
            "timezone": str(row.get("timezone") or "America/Sao_Paulo"),
            "nextRunAt": _iso(row.get("next_run_at")),
            "enabled": bool(row.get("enabled")),
            "lastClaimedAt": _iso(row.get("last_claimed_at")),
            "hour": fields.get("hour"),
            "minute": fields.get("minute"),
            "weekday": fields.get("weekday"),
            "createdAt": _iso(row.get("created_at")),
            "updatedAt": _iso(row.get("updated_at")),
        }

    @staticmethod
    def delivery_to_payload(row: dict[str, Any]) -> dict[str, Any]:
        def _id(value: Any) -> str:
            return str(value) if value is not None else ""

        return {
            "id": _id(row.get("id")),
            "runId": _id(row.get("run_id")),
            "recipientEmail": str(row.get("recipient_email") or ""),
            "status": str(row.get("status") or ""),
            "providerMessageId": row.get("provider_message_id"),
            "error": row.get("error"),
            "sentAt": _iso(row.get("sent_at")),
            "createdAt": _iso(row.get("created_at")),
        }

    @staticmethod
    def definition_to_payload(row: dict[str, Any]) -> dict[str, Any]:
        raw_id = row.get("id")
        if isinstance(raw_id, UUID):
            definition_id = str(raw_id)
        else:
            definition_id = str(raw_id)
        return {
            "id": definition_id,
            "name": row.get("name") or "",
            "providerKey": row.get("provider_key") or "",
            "params": _as_dict(row.get("params")),
            "active": bool(row.get("active")),
            "createdByUserId": row.get("created_by_user_id"),
            "createdAt": _iso(row.get("created_at")),
            "updatedAt": _iso(row.get("updated_at")),
        }

    @staticmethod
    def run_to_payload(row: dict[str, Any]) -> dict[str, Any]:
        def _id(value: Any) -> str:
            return str(value) if value is not None else ""

        summary = row.get("summary")
        if isinstance(summary, str):
            summary = json.loads(summary)
        if not isinstance(summary, dict):
            summary = {}

        return {
            "id": _id(row.get("id")),
            "definitionId": _id(row.get("definition_id")),
            "trigger": row.get("trigger") or "",
            "status": row.get("status") or "",
            "startedAt": _iso(row.get("started_at")),
            "finishedAt": _iso(row.get("finished_at")),
            "summary": summary,
            "error": row.get("error"),
            "createdAt": _iso(row.get("created_at")),
        }
