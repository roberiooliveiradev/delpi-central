"""Outbox durável para eventos de solução GLPI. Chave única por solução.

Concorrência entre réplicas: SELECT FOR UPDATE SKIP LOCKED. A entrega
é at-least-once em falha após HTTP 2xx e antes do commit local.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Protocol

from helpdesk_app.application.solved_ticket_notification_service import (
    CoreHelpdeskNotificationGateway,
    SolvedTicketNotice,
)
from helpdesk_app.infrastructure.persistence.postgres import connect

logger = logging.getLogger("helpdesk.solved_notifications.outbox")


class SolvedTicketNotificationOutbox(Protocol):
    def enqueue(self, notice: SolvedTicketNotice) -> bool: ...


class PostgresSolvedTicketNotificationOutbox:
    def enqueue(self, notice: SolvedTicketNotice) -> bool:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO helpdesk.solved_ticket_notification_outbox
                        (event_key, ticket_id, solution_id, recipient_user_id, ticket_title)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (event_key) DO NOTHING
                    RETURNING event_key
                    """,
                    (
                        notice.event_key, notice.ticket_id, notice.solution_id,
                        notice.recipient_user_id, notice.ticket_title,
                    ),
                )
                inserted = cur.fetchone() is not None
            conn.commit()
        return inserted

    def process_due(
        self,
        gateway: CoreHelpdeskNotificationGateway,
        *,
        limit: int = 10,
    ) -> int:
        processed = 0
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_key, ticket_id, solution_id,
                           recipient_user_id, ticket_title, attempt_count
                    FROM helpdesk.solved_ticket_notification_outbox
                    WHERE status = 'pending' AND next_attempt_at <= NOW()
                    ORDER BY created_at, event_key
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                    """,
                    (max(1, min(limit, 50)),),
                )
                rows = cur.fetchall()
                for row in rows:
                    notice = SolvedTicketNotice(
                        ticket_id=int(row["ticket_id"]),
                        solution_id=int(row["solution_id"]),
                        recipient_user_id=str(row["recipient_user_id"]),
                        ticket_title=str(row["ticket_title"]),
                    )
                    outcome = gateway.send(notice)
                    if outcome in ("sent", "ignored"):
                        cur.execute(
                            """
                            UPDATE helpdesk.solved_ticket_notification_outbox
                            SET status = %s, attempt_count = attempt_count + 1,
                                delivered_at = CASE WHEN %s = 'sent' THEN NOW() ELSE delivered_at END,
                                last_attempt_at = NOW()
                            WHERE event_key = %s
                            """,
                            (outcome, outcome, notice.event_key),
                        )
                    else:
                        next_attempt = datetime.now(timezone.utc) + timedelta(
                            seconds=min(3600, 30 * (2 ** min(int(row["attempt_count"]), 7)))
                        )
                        cur.execute(
                            """
                            UPDATE helpdesk.solved_ticket_notification_outbox
                            SET attempt_count = attempt_count + 1,
                                last_attempt_at = NOW(), next_attempt_at = %s
                            WHERE event_key = %s
                            """,
                            (next_attempt, notice.event_key),
                        )
                    processed += 1
            conn.commit()
        if processed:
            logger.info("helpdesk_solved_notification_processed count=%s", processed)
        return processed
