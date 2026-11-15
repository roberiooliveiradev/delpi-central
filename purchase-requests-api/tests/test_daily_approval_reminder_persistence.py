"""Integration tests use the same isolated Plugins PostgreSQL as other repo tests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from uuid import uuid4

from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)
from purchase_requests_app.infrastructure.persistence.repositories.daily_approval_reminder_repository import (
    DailyApprovalReminderRepository,
)


def test_concurrent_workers_restart_next_day_and_stale_lease_fencing():
    repo = DailyApprovalReminderRepository()
    key = {
        "reminder_date": date.today(),
        "branch": "02",
        "request_number": str(uuid4()),
        "user_id": "test-user",
        "recipient_role": "approver",
    }
    with ThreadPoolExecutor(max_workers=8) as pool:
        tokens = list(pool.map(lambda _: repo.claim(**key), range(8)))
    token = next(t for t in tokens if t)
    assert len([t for t in tokens if t]) == 1
    with plugins_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE purchase_requests.daily_approval_reminders SET claimed_at = NOW() - INTERVAL '6 minutes' WHERE claim_token = %s",
                (token,),
            )
        conn.commit()
    retry_token = repo.claim(**key)
    assert retry_token and retry_token != token
    repo.complete(claim_token=token, result="delivered")
    with plugins_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT completed_at FROM purchase_requests.daily_approval_reminders WHERE claim_token = %s",
                (retry_token,),
            )
            assert cur.fetchone()["completed_at"] is None
    repo.complete(claim_token=retry_token, result="delivered")
    assert DailyApprovalReminderRepository().claim(**key) is None
    assert repo.claim(**{**key, "reminder_date": date.today() + timedelta(days=1)})
    assert repo.claim(**{**key, "user_id": "another-user"})
    assert repo.claim(**{**key, "branch": "01"})
    assert repo.claim(**{**key, "recipient_role": "requester"})


def test_prune_only_removes_old_days():
    repo = DailyApprovalReminderRepository()
    key = {
        "branch": "01",
        "request_number": str(uuid4()),
        "user_id": "test",
        "recipient_role": "requester",
    }
    old_token = repo.claim(**key, reminder_date=date.today() - timedelta(days=100))
    current_token = repo.claim(**key, reminder_date=date.today())
    repo.prune()
    with plugins_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT claim_token FROM purchase_requests.daily_approval_reminders WHERE request_number = %s",
                (key["request_number"],),
            )
            assert [str(row["claim_token"]) for row in cur.fetchall()] == [
                current_token
            ]
    assert old_token != current_token
