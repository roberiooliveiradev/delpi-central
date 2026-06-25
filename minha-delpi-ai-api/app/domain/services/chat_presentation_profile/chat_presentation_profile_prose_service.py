"""Delegate — perfis declarativos de apresentação."""

from __future__ import annotations

from typing import Any

from app.domain.services.openapi_presentation_profile_deriver_service import (
    OpenApiPresentationProfileDeriverService,
)
from app.domain.services.openapi_operation_contract_service import (
    OpenApiOperationContractService,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_facade_access import (
    presentation_profile_service,
)



class ChatPresentationProfileProseService:
    @classmethod
    def prose_delivery_mode(
        cls,
        *,
        entity: str | None = None,
        path: str | None = None,
    ) -> str | None:
        """P3.2 — modo canônico de prosa por entidade ou perfil declarativo."""
        allowed = frozenset({"template", "llm", "direct"})
        token = str(entity or "").strip()
        by_entity = presentation_profile_service().node("proseDeliveryByEntity")

        if isinstance(by_entity, dict) and token:
            mode = str(by_entity.get(token) or "").strip().lower()

            if mode in allowed:
                return mode

        if not path and not token:
            return None

        profile_key = presentation_profile_service().resolve_profile_key(path, entity)
        by_profile = presentation_profile_service().node("proseDeliveryByProfile")

        if isinstance(by_profile, dict):
            mode = str(by_profile.get(profile_key) or "").strip().lower()

            if mode in allowed:
                return mode

        if token:
            by_entity_set = presentation_profile_service().node("proseDeliveryByEntitySet")

            if isinstance(by_entity_set, dict):
                for set_key, configured in by_entity_set.items():
                    if token not in presentation_profile_service().entity_set(str(set_key or "")):
                        continue

                    mode = str(configured or "").strip().lower()

                    if mode in allowed:
                        return mode

        if token or path:
            from app.domain.services.chat_presentation_coverage_service import (
                ChatPresentationCoverageService,
            )
            from app.domain.services.chat_presentation_prose_delivery_content_service import (
                ChatPresentationProseDeliveryContentService,
            )

            tier = ChatPresentationCoverageService.classify_tier(
                entity=token or None,
                path=str(path or ""),
            )
            tier_mode = ChatPresentationProseDeliveryContentService.prose_delivery_mode_for_tier(
                tier,
            )

            if tier_mode in allowed:
                return tier_mode

        return None

