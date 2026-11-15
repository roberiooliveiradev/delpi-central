"""Durable per-day, document, recipient and role leases across workers/restarts."""

from uuid import uuid4

from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)


class DailyApprovalReminderRepository:
    def claim(self, *, reminder_date, branch, request_number, user_id, recipient_role):
        token = str(uuid4())
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO purchase_requests.daily_approval_reminders
                        (reminder_date, branch, request_number, user_id, recipient_role, claim_token)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (reminder_date, branch, request_number, user_id, recipient_role)
                    DO UPDATE SET claim_token = EXCLUDED.claim_token, claimed_at = NOW()
                    WHERE daily_approval_reminders.completed_at IS NULL
                      AND daily_approval_reminders.claimed_at < NOW() - INTERVAL '5 minutes'
                    RETURNING claim_token
                """,
                    (
                        reminder_date,
                        branch,
                        request_number,
                        user_id,
                        recipient_role,
                        token,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return str(row["claim_token"]) if row else None

    def complete(self, *, claim_token, result):
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE purchase_requests.daily_approval_reminders
                    SET completed_at = NOW(), result = %s
                    WHERE claim_token = %s AND completed_at IS NULL
                """,
                    (result, claim_token),
                )
            conn.commit()

    def prune(self):
        # A reminder never needs to be replayed for a previous business day.
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM purchase_requests.daily_approval_reminders
                    WHERE reminder_date < CURRENT_DATE - 90
                """)
            conn.commit()
