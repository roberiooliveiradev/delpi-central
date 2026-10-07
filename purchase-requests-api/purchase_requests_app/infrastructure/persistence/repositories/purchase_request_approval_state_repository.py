"""Persisted snapshot of SC approval states + idempotent dispatch claim.

Grain: ``(branch, request_number)`` — one row per SC, not per item.
Concurrency: the claim is a conditional ``UPDATE`` on the row itself, so two
``purchase-requests-api`` instances cannot both own the same transition —
whoever commits first sets ``notify_pending`` and the loser's ``WHERE``
no longer matches.
"""

from __future__ import annotations

from typing import Any, Iterable

from purchase_requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

DEFAULT_CLAIM_STALE_SECONDS = 300


class PurchaseRequestApprovalStateRepository:
    def insert_baseline(self, states: Iterable[dict[str, Any]]) -> int:
        """First-run snapshot: records current state without claiming anything."""
        rows = [
            (
                state["branch"],
                state["request_number"],
                state.get("requester_protheus_user_id"),
                state["approval_status"],
                state.get("approver_name"),
            )
            for state in states
        ]
        if not rows:
            return 0
        sql = """
        INSERT INTO purchase_requests.purchase_request_approval_states
            (branch, request_number, requester_protheus_user_id,
             approval_status, approver_name)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (branch, request_number) DO NOTHING
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, rows)
                inserted = cur.rowcount
            conn.commit()
        return int(inserted)

    def observe_and_claim(
        self,
        *,
        branch: str,
        request_number: str,
        approval_status: str,
        requester_protheus_user_id: str | None,
        approver_name: str | None,
        notifiable: bool,
        claim_stale_seconds: int = DEFAULT_CLAIM_STALE_SECONDS,
    ) -> dict[str, Any] | None:
        """Sync the observed state and, when it is a notifiable transition,
        atomically claim it for dispatch.

        Returns the claimed row (dispatch owed) or ``None`` when nothing is
        owed (baseline insert, unchanged state, in-flight claim).
        """
        inserted = self._insert_observed(
            branch=branch,
            request_number=request_number,
            approval_status=approval_status,
            requester_protheus_user_id=requester_protheus_user_id,
            approver_name=approver_name,
            notify_pending=notifiable,
        )
        if inserted is not None:
            return inserted if notifiable else None
        if notifiable:
            claimed = self._claim_transition(
                branch=branch,
                request_number=request_number,
                approval_status=approval_status,
                requester_protheus_user_id=requester_protheus_user_id,
                approver_name=approver_name,
                claim_stale_seconds=claim_stale_seconds,
            )
            if claimed is not None:
                return claimed
        self._sync_quietly(
            branch=branch,
            request_number=request_number,
            approval_status=approval_status,
            requester_protheus_user_id=requester_protheus_user_id,
            approver_name=approver_name,
        )
        return None

    def mark_delivered(
        self,
        *,
        branch: str,
        request_number: str,
        approval_status: str,
    ) -> None:
        self._resolve_claim(
            branch=branch,
            request_number=request_number,
            approval_status=approval_status,
            result="delivered",
        )

    def mark_skipped(
        self,
        *,
        branch: str,
        request_number: str,
        approval_status: str,
        result: str = "skipped",
    ) -> None:
        self._resolve_claim(
            branch=branch,
            request_number=request_number,
            approval_status=approval_status,
            result=result,
        )

    def touch_dispatch_error(
        self,
        *,
        branch: str,
        request_number: str,
    ) -> None:
        """Keep the claim pending so a later cycle retries the dispatch."""
        sql = """
        UPDATE purchase_requests.purchase_request_approval_states
        SET dispatch_result = 'retry_pending',
            updated_at = NOW()
        WHERE branch = %s
          AND request_number = %s
          AND notify_pending
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (branch, request_number))
            conn.commit()

    def _insert_observed(
        self,
        *,
        branch: str,
        request_number: str,
        approval_status: str,
        requester_protheus_user_id: str | None,
        approver_name: str | None,
        notify_pending: bool,
    ) -> dict[str, Any] | None:
        sql = """
        INSERT INTO purchase_requests.purchase_request_approval_states
            (branch, request_number, requester_protheus_user_id,
             approval_status, approver_name, observed_at,
             notify_pending, notify_claimed_at, dispatch_attempts)
        VALUES (%s, %s, %s, %s, %s, NOW(), %s,
                CASE WHEN %s THEN NOW() END,
                CASE WHEN %s THEN 1 ELSE 0 END)
        ON CONFLICT (branch, request_number) DO NOTHING
        RETURNING branch, request_number, approval_status,
                  requester_protheus_user_id, approver_name
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        branch,
                        request_number,
                        requester_protheus_user_id,
                        approval_status,
                        approver_name,
                        notify_pending,
                        notify_pending,
                        notify_pending,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else None

    def _claim_transition(
        self,
        *,
        branch: str,
        request_number: str,
        approval_status: str,
        requester_protheus_user_id: str | None,
        approver_name: str | None,
        claim_stale_seconds: int,
    ) -> dict[str, Any] | None:
        sql = """
        UPDATE purchase_requests.purchase_request_approval_states
        SET approval_status = %(status)s,
            approver_name = %(approver)s,
            requester_protheus_user_id = %(requester)s,
            observed_at = NOW(),
            notify_pending = TRUE,
            notify_claimed_at = NOW(),
            dispatch_attempts = dispatch_attempts + 1,
            updated_at = NOW()
        WHERE branch = %(branch)s
          AND request_number = %(request)s
          AND (
               approval_status IS DISTINCT FROM %(status)s
               OR (
                    notify_pending
                    AND notify_claimed_at <= NOW() - make_interval(secs => %(stale)s)
                  )
              )
        RETURNING branch, request_number, approval_status,
                  requester_protheus_user_id, approver_name
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    {
                        "status": approval_status,
                        "approver": approver_name,
                        "requester": requester_protheus_user_id,
                        "branch": branch,
                        "request": request_number,
                        "stale": int(claim_stale_seconds),
                    },
                )
                row = cur.fetchone()
            conn.commit()
        return dict(row) if row else None

    def _sync_quietly(
        self,
        *,
        branch: str,
        request_number: str,
        approval_status: str,
        requester_protheus_user_id: str | None,
        approver_name: str | None,
    ) -> None:
        """Refresh snapshot without claiming; supersedes a stale pending when
        the observed status moved to a non-notifiable value."""
        sql = """
        UPDATE purchase_requests.purchase_request_approval_states
        SET approval_status = %(status)s,
            approver_name = %(approver)s,
            requester_protheus_user_id = %(requester)s,
            observed_at = CASE
                WHEN approval_status IS DISTINCT FROM %(status)s THEN NOW()
                ELSE observed_at
            END,
            dispatch_result = CASE
                WHEN approval_status IS DISTINCT FROM %(status)s
                     AND notify_pending THEN 'superseded'
                ELSE dispatch_result
            END,
            notify_pending = CASE
                WHEN approval_status IS DISTINCT FROM %(status)s THEN FALSE
                ELSE notify_pending
            END,
            updated_at = NOW()
        WHERE branch = %(branch)s
          AND request_number = %(request)s
          AND (
               approval_status IS DISTINCT FROM %(status)s
               OR requester_protheus_user_id IS DISTINCT FROM %(requester)s
               OR approver_name IS DISTINCT FROM %(approver)s
              )
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    {
                        "status": approval_status,
                        "approver": approver_name,
                        "requester": requester_protheus_user_id,
                        "branch": branch,
                        "request": request_number,
                    },
                )
            conn.commit()

    def _resolve_claim(
        self,
        *,
        branch: str,
        request_number: str,
        approval_status: str,
        result: str,
    ) -> None:
        sql = """
        UPDATE purchase_requests.purchase_request_approval_states
        SET notify_pending = FALSE,
            notified_at = CASE WHEN %(result)s = 'delivered' THEN NOW() ELSE notified_at END,
            dispatch_result = %(result)s,
            updated_at = NOW()
        WHERE branch = %(branch)s
          AND request_number = %(request)s
          AND notify_pending
          AND approval_status = %(status)s
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    {
                        "result": result,
                        "branch": branch,
                        "request": request_number,
                        "status": approval_status,
                    },
                )
            conn.commit()
