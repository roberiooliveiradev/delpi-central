"""Decide which recipients should get Portal (sino) notifications."""

from __future__ import annotations

from typing import Sequence

from commercial_app.application.services.commercial_realtime_hub import (
    CommercialRealtimeHub,
    commercial_realtime_hub,
)
from commercial_app.domain.services.ready_to_invoice_notification_content_service import (
    ReadyToInvoiceNotificationContentService,
)
from commercial_app.domain.services.task_portal_notification_content_service import (
    TASK_PORTAL_EVENT_TYPES,
)

# When the user has the Commercial MFE open (WS online), they already get
# in-app toast — skip Minha Delpi portal channel for these events.
_PORTAL_SUPPRESS_WHEN_ONLINE = frozenset(
    {
        *TASK_PORTAL_EVENT_TYPES,
        ReadyToInvoiceNotificationContentService.event_type(),
    }
)


class TaskPortalNotificationDeliveryPolicy:
    """Skip Portal channel when the user already receives the in-app toast."""

    def __init__(self, *, hub: CommercialRealtimeHub | None = None) -> None:
        self._hub = hub or commercial_realtime_hub

    def suppresses_portal_when_online(self, event_type: str) -> bool:
        return event_type in _PORTAL_SUPPRESS_WHEN_ONLINE

    def filter_portal_recipients(
        self,
        event_type: str,
        user_ids: Sequence[str],
    ) -> list[str]:
        recipients = sorted(
            {str(uid).strip() for uid in user_ids if str(uid).strip()}
        )
        if not recipients or not self.suppresses_portal_when_online(event_type):
            return recipients
        return [uid for uid in recipients if not self._hub.is_user_online(uid)]

    def split_online_offline(
        self,
        event_type: str,
        user_ids: Sequence[str],
    ) -> tuple[list[str], list[str]]:
        """Return (online, offline) for events that suppress portal when online."""
        recipients = sorted(
            {str(uid).strip() for uid in user_ids if str(uid).strip()}
        )
        if not recipients or not self.suppresses_portal_when_online(event_type):
            return [], recipients
        online = [uid for uid in recipients if self._hub.is_user_online(uid)]
        offline = [uid for uid in recipients if uid not in set(online)]
        return online, offline
