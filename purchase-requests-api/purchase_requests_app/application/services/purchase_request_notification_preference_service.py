"""Resolução de destinatários Minha DELPI a partir de usuários Protheus.

O dispatcher converte ``C1_USER``/solicitante Protheus em ``user_id`` do
portal via ``user_protheus_mappings``. Preferências de recebimento
(mute/destaque/e-mail por categoria) são decididas exclusivamente pela
Core API no dispatch — este serviço resolve apenas identidade.
"""

from __future__ import annotations

from purchase_requests_app.infrastructure.persistence.repositories.user_protheus_mapping_repository import (
    UserProtheusMappingRepository,
)


class PurchaseRequestNotificationPreferenceService:
    def __init__(
        self,
        *,
        mapping_repository: UserProtheusMappingRepository | None = None,
    ) -> None:
        self._mappings = mapping_repository or UserProtheusMappingRepository()

    def portal_users_for_mapped_requester(self, protheus_user_id: str) -> list[str]:
        mapping = self._mappings.get_mapping_by_protheus_user_id(protheus_user_id)
        if not mapping:
            return []
        user_id = str(mapping.get("user_id") or "").strip()
        return [user_id] if user_id else []
