"""Preferências de notificação — leitura para futuro dispatcher de eventos.

O disparo automático (pedido emitido, recebimento, etc.) deve consultar
`NotificationSubscriptionRepository` + `UserProtheusMappingRepository`
antes de enfileirar notificações no canal do portal.
"""

from __future__ import annotations

from purchase_requests_app.infrastructure.persistence.repositories.notification_subscription_repository import (
    NotificationSubscriptionRepository,
)
from purchase_requests_app.infrastructure.persistence.repositories.user_protheus_mapping_repository import (
    UserProtheusMappingRepository,
)


class PurchaseRequestNotificationPreferenceService:
    def __init__(
        self,
        *,
        subscription_repository: NotificationSubscriptionRepository | None = None,
        mapping_repository: UserProtheusMappingRepository | None = None,
    ) -> None:
        self._subscriptions = subscription_repository or NotificationSubscriptionRepository()
        self._mappings = mapping_repository or UserProtheusMappingRepository()

    def portal_users_for_mapped_requester(self, protheus_user_id: str) -> list[str]:
        mapping = self._mappings.get_mapping_by_protheus_user_id(protheus_user_id)
        if not mapping:
            return []
        user_id = str(mapping.get("user_id") or "").strip()
        return [user_id] if user_id else []

    def portal_users_for_protheus_event(
        self,
        *,
        protheus_user_id: str,
        event_key: str,
    ) -> list[str]:
        normalized_totvs = (protheus_user_id or "").strip()
        if not normalized_totvs:
            return []
        portal_user_ids: list[str] = []
        for mapping in self._mappings.list_mappings():
            if (mapping.get("protheus_user_id") or "").strip() != normalized_totvs:
                continue
            user_id = str(mapping.get("user_id") or "").strip()
            if not user_id:
                continue
            subs = self._subscriptions.list_for_user(user_id)
            if any(
                row.get("event_key") == event_key and bool(row.get("enabled"))
                for row in subs
            ):
                portal_user_ids.append(user_id)
        return portal_user_ids
