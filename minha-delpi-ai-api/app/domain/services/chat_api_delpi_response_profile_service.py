"""Compatibilidade — preferir `chat_operational_response_profile_service`."""

from __future__ import annotations

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
    OperationalResponseProfile,
)

ApiDelpiResponseProfile = OperationalResponseProfile
ChatApiDelpiResponseProfileService = ChatOperationalResponseProfileService

_MODULE_ENTITY_SET_ALIASES = {
    "CHAT_CRITICAL_ENTITIES": "chatCritical",
    "PLAYBOOK_OPERATIONAL_ENTITIES": "playbookOperational",
    "PROFILE_PRESENT_ENTITIES": "profilePresent",
    "PRODUCT_LIST_PRESENT_ENTITIES": "productListPresent",
    "KPI_PRESENT_ENTITIES": "kpiPresent",
    "LMP_PRESENT_ENTITIES": "lmpPresent",
    "SQL_PRESENT_ENTITIES": "sqlPresent",
    "SYSTEM_PRESENT_ENTITIES": "systemPresent",
    "SALE_ORDER_PRESENT_ENTITIES": "saleOrderPresent",
}


def __getattr__(name: str):
    if name == "ENTITY_ROUTED_FOR_PRESENT":
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        return ChatPresentationProfileService.entity_routed_for_present()

    set_key = _MODULE_ENTITY_SET_ALIASES.get(name)

    if set_key:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        return ChatPresentationProfileService.entity_set(set_key)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ApiDelpiResponseProfile",
    "CHAT_CRITICAL_ENTITIES",
    "ChatApiDelpiResponseProfileService",
    "ChatOperationalResponseProfileService",
    "ENTITY_ROUTED_FOR_PRESENT",
    "KPI_PRESENT_ENTITIES",
    "LMP_PRESENT_ENTITIES",
    "OperationalResponseProfile",
    "PLAYBOOK_OPERATIONAL_ENTITIES",
    "PRODUCT_LIST_PRESENT_ENTITIES",
    "PROFILE_PRESENT_ENTITIES",
    "SALE_ORDER_PRESENT_ENTITIES",
    "SQL_PRESENT_ENTITIES",
    "SYSTEM_PRESENT_ENTITIES",
]
