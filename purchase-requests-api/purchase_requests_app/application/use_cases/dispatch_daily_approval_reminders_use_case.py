"""One bounded page per poll; retry leases without retaining yesterday's payload."""

from datetime import datetime
from zoneinfo import ZoneInfo

from purchase_requests_app.application.services.purchase_request_notification_preference_service import (
    PurchaseRequestNotificationPreferenceService,
)
from purchase_requests_app.application.services.purchase_requests_portal_notification_service import (
    PurchaseRequestsPortalNotificationService,
)
from purchase_requests_app.domain.services.purchase_request_pending_notification_content_service import (
    build_pending_notification,
)
from purchase_requests_app.infrastructure.gateways.delpi_purchase_requests_gateway import (
    DelpiPurchaseRequestsGateway,
)
from purchase_requests_app.infrastructure.persistence.repositories.daily_approval_reminder_repository import (
    DailyApprovalReminderRepository,
)


class DispatchDailyApprovalRemindersUseCase:
    def __init__(
        self,
        *,
        gateway=None,
        repository=None,
        identities=None,
        notifications=None,
        clock=None,
    ):
        self._gateway = gateway or DelpiPurchaseRequestsGateway()
        self._repository = repository or DailyApprovalReminderRepository()
        self._identities = identities or PurchaseRequestNotificationPreferenceService()
        self._notifications = (
            notifications or PurchaseRequestsPortalNotificationService()
        )
        self._clock = clock or (lambda: datetime.now(ZoneInfo("America/Sao_Paulo")))
        self._cursor = {}
        self._pruned_on = None

    def execute(self) -> dict:
        today = self._clock().astimezone(ZoneInfo("America/Sao_Paulo")).date()
        if self._pruned_on != today:
            self._repository.prune()
            self._pruned_on = today
        payload = self._gateway.list_pending_approvals(**self._cursor, limit=100)
        if not isinstance(payload.get("items"), list):
            raise ValueError("Invalid pending approval feed")
        counts = {
            "observed": len(payload["items"]),
            "dispatched": 0,
            "retry": 0,
            "unmapped": 0,
        }
        mappings = {}
        for document in payload["items"]:
            if not document.get("pending_approvers"):
                continue
            recipients = {
                "requester": {document.get("requester_protheus_user_id")},
                "approver": {
                    a.get("protheus_user_id") for a in document["pending_approvers"]
                },
            }
            for role, protheus_ids in recipients.items():
                portal_ids = set()
                for protheus_id in sorted(
                    str(value or "").strip() for value in protheus_ids
                ):
                    if not protheus_id:
                        counts["unmapped"] += 1
                        continue
                    if protheus_id not in mappings:
                        mappings[protheus_id] = (
                            self._identities.portal_users_for_mapped_requester(
                                protheus_id
                            )
                        )
                    users = mappings[protheus_id]
                    if not users:
                        counts["unmapped"] += 1
                    portal_ids.update(users)
                for user_id in sorted(portal_ids):
                    # Resolve current identity before claiming; unmapped users can
                    # become eligible on the next scan on the same business day.
                    token = self._repository.claim(
                        reminder_date=today,
                        branch=document["branch"],
                        request_number=document["request_number"],
                        user_id=user_id,
                        recipient_role=role,
                    )
                    if token is None:
                        continue
                    content = build_pending_notification(document, recipient_role=role)
                    outcome = self._notifications.send(
                        user_ids=[user_id],
                        notification_type="warning",
                        **content,
                        dedupe_key=f'purchase-requests:pending:{today}:{document["branch"]}:{document["request_number"]}:{role}:{user_id}',
                        event_type=content["category"],
                        metadata={
                            "branch": document["branch"],
                            "requestNumber": document["request_number"],
                            "reminderDate": today.isoformat(),
                            "recipientRole": role,
                        },
                    )
                    if outcome.retry:
                        counts["retry"] += 1
                    else:
                        self._repository.complete(
                            claim_token=token,
                            result="delivered" if outcome.delivered else "skipped",
                        )
                        counts["dispatched"] += int(outcome.delivered)
        self._cursor = payload.get("next_cursor") or {}
        return counts
