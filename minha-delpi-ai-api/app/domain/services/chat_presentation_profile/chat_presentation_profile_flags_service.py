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



class ChatPresentationProfileFlagsService:
    @classmethod
    def flags(cls, path: str | None, entity: str | None = None) -> frozenset[str]:
        profile = presentation_profile_service().resolve_profile(path, entity)
        raw = profile.get("flags") or []

        return frozenset(str(item).strip().lower() for item in raw if str(item).strip())

    @classmethod
    def has_flag(
        cls,
        path: str | None,
        flag: str,
        *,
        entity: str | None = None,
    ) -> bool:
        return str(flag or "").strip().lower() in presentation_profile_service().flags(path, entity)

