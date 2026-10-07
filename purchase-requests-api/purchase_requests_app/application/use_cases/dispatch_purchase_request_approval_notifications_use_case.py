from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from purchase_requests_app.application.services.purchase_request_notification_preference_service import (
    PurchaseRequestNotificationPreferenceService,
)
from purchase_requests_app.application.services.purchase_requests_portal_notification_service import (
    PurchaseRequestsPortalNotificationService,
)
from purchase_requests_app.config import settings
from purchase_requests_app.domain.services.purchase_request_approval_state_service import (
    aggregate_request_approval_states,
    event_key_for_status,
    is_notifiable_status,
)
from purchase_requests_app.infrastructure.gateways.delpi_purchase_requests_gateway import (
    DelpiPurchaseRequestsGateway,
)
from purchase_requests_app.infrastructure.persistence.repositories.purchase_order_notification_cursor_repository import (
    PurchaseOrderNotificationCursorRepository,
)
from purchase_requests_app.infrastructure.persistence.repositories.purchase_request_approval_state_repository import (
    PurchaseRequestApprovalStateRepository,
)

logger = logging.getLogger("purchase_requests.approval_notification_dispatch")

JOB_KEY_PURCHASE_REQUEST_APPROVAL = "purchase_request_approval"


class DispatchPurchaseRequestApprovalNotificationsUseCase:
    """Detect SC approval-status changes (C1_APROV) and notify the requester.

    Unlike the order/receipt pollers, detection is state-diff based: the
    api-delpi feed returns the current approval state per SC item, the domain
    aggregates it to SC level, and the persisted snapshot tells whether the
    state actually changed. RECNO cannot be used here — C1_APROV mutates
    in place on the same row.
    """

    def __init__(
        self,
        *,
        gateway: DelpiPurchaseRequestsGateway | None = None,
        state_repository: PurchaseRequestApprovalStateRepository | None = None,
        cursor_repository: PurchaseOrderNotificationCursorRepository | None = None,
        preference_service: PurchaseRequestNotificationPreferenceService | None = None,
        notification_service: PurchaseRequestsPortalNotificationService | None = None,
        job_key: str = JOB_KEY_PURCHASE_REQUEST_APPROVAL,
        limit: int | None = None,
        lookback_days: int | None = None,
        claim_stale_seconds: int = 300,
    ) -> None:
        self._gateway = gateway or DelpiPurchaseRequestsGateway()
        self._states = state_repository or PurchaseRequestApprovalStateRepository()
        self._cursors = cursor_repository or PurchaseOrderNotificationCursorRepository()
        self._preferences = preference_service or PurchaseRequestNotificationPreferenceService()
        self._notifications = (
            notification_service or PurchaseRequestsPortalNotificationService()
        )
        self._job_key = job_key
        self._limit = int(
            limit
            if limit is not None
            else settings.PURCHASE_REQUESTS_APPROVAL_STATES_FEED_LIMIT
        )
        self._lookback_days = int(
            lookback_days
            if lookback_days is not None
            else settings.PURCHASE_REQUESTS_APPROVAL_STATES_LOOKBACK_DAYS
        )
        self._claim_stale_seconds = claim_stale_seconds

    def execute(self) -> dict[str, Any]:
        baseline_done = self._cursors.get_last_recno(self._job_key) is not None
        date_from = (
            date.today() - timedelta(days=self._lookback_days)
        ).isoformat()
        payload = self._gateway.list_approval_states(
            date_from=date_from,
            limit=self._limit,
        )
        items = list(payload.get("items") or [])
        truncated = bool(payload.get("truncated"))
        states = aggregate_request_approval_states(items)

        if not baseline_done:
            inserted = self._states.insert_baseline(states)
            self._cursors.upsert_last_recno(self._job_key, 1)
            logger.info(
                "purchase_request_approval_first_run baseline=%s observed=%s truncated=%s",
                inserted,
                len(states),
                truncated,
            )
            return {
                "first_run": True,
                "observed": len(states),
                "baseline": inserted,
                "dispatched": 0,
                "truncated": truncated,
            }

        counters = {
            "observed": len(states),
            "claimed": 0,
            "approved": 0,
            "rejected": 0,
            "dispatched": 0,
            "skipped": 0,
            "unmapped": 0,
            "retry": 0,
            "unchanged": 0,
        }
        ordered = sorted(
            states,
            key=lambda s: (str(s.get("branch")), str(s.get("request_number"))),
        )
        for state in ordered:
            branch = str(state.get("branch") or "").strip()
            request_number = str(state.get("request_number") or "").strip()
            status = str(state.get("approval_status") or "").strip()
            if not branch or not request_number:
                counters["skipped"] += 1
                continue
            claimed = self._states.observe_and_claim(
                branch=branch,
                request_number=request_number,
                approval_status=status,
                requester_protheus_user_id=state.get("requester_protheus_user_id"),
                approver_name=state.get("approver_name"),
                notifiable=is_notifiable_status(status),
                claim_stale_seconds=self._claim_stale_seconds,
            )
            if not claimed:
                counters["unchanged"] += 1
                continue
            event_key = event_key_for_status(status)
            if not event_key:
                counters["unchanged"] += 1
                continue
            counters["claimed"] += 1
            counters["approved" if status == "approved" else "rejected"] += 1

            requester = str(
                claimed.get("requester_protheus_user_id") or ""
            ).strip()
            user_ids = self._preferences.portal_users_for_mapped_requester(requester)
            if not user_ids:
                self._states.mark_skipped(
                    branch=branch,
                    request_number=request_number,
                    approval_status=status,
                    result="unmapped_requester",
                )
                counters["unmapped"] += 1
                logger.info(
                    "purchase_request_approval_unmapped_requester event=%s sc=%s:%s",
                    event_key,
                    branch,
                    request_number,
                )
                continue

            notify = (
                self._notifications.notify_purchase_request_approved
                if status == "approved"
                else self._notifications.notify_purchase_request_rejected
            )
            outcome = notify(
                user_ids=user_ids,
                branch=branch,
                request_number=request_number,
                approval_status=status,
                approver_name=claimed.get("approver_name"),
                requester_protheus_user_id=requester or None,
            )
            if outcome.delivered:
                self._states.mark_delivered(
                    branch=branch,
                    request_number=request_number,
                    approval_status=status,
                )
                counters["dispatched"] += 1
            elif outcome.retry:
                self._states.touch_dispatch_error(
                    branch=branch,
                    request_number=request_number,
                )
                counters["retry"] += 1
            else:
                self._states.mark_skipped(
                    branch=branch,
                    request_number=request_number,
                    approval_status=status,
                    result="permanent_rejection",
                )
                counters["skipped"] += 1

        if counters["claimed"] or counters["retry"]:
            logger.info(
                "purchase_request_approval_poll observed=%s claimed=%s approved=%s "
                "rejected=%s dispatched=%s unmapped=%s retry=%s truncated=%s",
                counters["observed"],
                counters["claimed"],
                counters["approved"],
                counters["rejected"],
                counters["dispatched"],
                counters["unmapped"],
                counters["retry"],
                truncated,
            )
        return {"first_run": False, "truncated": truncated, **counters}
