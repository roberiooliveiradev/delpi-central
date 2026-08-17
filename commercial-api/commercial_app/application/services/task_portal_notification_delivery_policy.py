"""Decide which task recipients should get Portal (sino) notifications."""

from __future__ import annotations

from typing import Sequence

from commercial_app.application.services.commercial_realtime_hub import (
    CommercialRealtimeHub,
    commercial_realtime_hub,
)
from commercial_app.domain.services.task_portal_notification_content_service import (
    EVENT_ASSIGNED,
    EVENT_COMPLETED,
    EVENT_GROUP_ASSIGNED,
)

# Mutations already toasted via commercial realtime WS while the MFE is open.
_PORTAL_SUPPRESS_WHEN_ONLINE = frozenset(
    {
        EVENT_ASSIGNED,
        EVENT_GROUP_ASSIGNED,
        EVENT_COMPLETED,
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
