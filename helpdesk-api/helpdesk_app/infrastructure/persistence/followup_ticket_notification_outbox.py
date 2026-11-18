"""Fila PostgreSQL de retornos: mesma semântica do outbox de soluções (#1616)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Protocol

from helpdesk_app.application.followup_ticket_notification_service import FollowupTicketNotice
from helpdesk_app.application.solved_ticket_notification_service import CoreHelpdeskNotificationGateway
from helpdesk_app.infrastructure.persistence.postgres import connect

logger = logging.getLogger("helpdesk.followup_notifications.outbox")


class FollowupTicketNotificationOutbox(Protocol):
    def enqueue(self, notice: FollowupTicketNotice) -> bool: ...


class PostgresFollowupTicketNotificationOutbox:
    def enqueue(self, notice: FollowupTicketNotice) -> bool:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO helpdesk.followup_ticket_notification_outbox
                        (event_key, ticket_id, followup_id, recipient_user_id,
                         ticket_title, preview)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_key) DO NOTHING
                    RETURNING event_key
                    """,
                    (notice.event_key, notice.ticket_id, notice.followup_id,
                     notice.recipient_user_id, notice.ticket_title, notice.preview),
                )
                inserted = cur.fetchone() is not None
            conn.commit()
        return inserted

    def process_due(self, gateway: CoreHelpdeskNotificationGateway, *, limit: int = 10) -> int:
        processed = 0
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_key, ticket_id, followup_id, recipient_user_id,
                           ticket_title, preview, attempt_count
                    FROM helpdesk.followup_ticket_notification_outbox
                    WHERE status = 'pending' AND next_attempt_at <= NOW()
                    ORDER BY created_at, event_key
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                    """,
                    (max(1, min(limit, 50)),),
                )
                for row in cur.fetchall():
                    notice = FollowupTicketNotice(
                        ticket_id=int(row["ticket_id"]),
                        followup_id=int(row["followup_id"]),
                        recipient_user_id=str(row["recipient_user_id"]),
                        ticket_title=str(row["ticket_title"]),
                        preview=str(row["preview"]),
                    )
                    outcome = gateway.send(notice)
                    if outcome in ("sent", "ignored"):
                        cur.execute(
                            """
                            UPDATE helpdesk.followup_ticket_notification_outbox
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
                            UPDATE helpdesk.followup_ticket_notification_outbox
                            SET attempt_count = attempt_count + 1,
                                last_attempt_at = NOW(), next_attempt_at = %s
                            WHERE event_key = %s
                            """,
                            (next_attempt, notice.event_key),
                        )
                    processed += 1
            conn.commit()
        if processed:
            logger.info("helpdesk_followup_notification_processed count=%s", processed)
        return processed
