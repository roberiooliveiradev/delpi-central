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



class ChatPresentationProfileContractService:
    @classmethod
    def entity_set_profile_contracts(cls) -> dict[str, dict[str, Any]]:
        raw = presentation_profile_service().node("entitySetProfileContracts")

        if not isinstance(raw, dict):
            return {}

        resolved: dict[str, dict[str, Any]] = {}

        for contract_key, contract in raw.items():
            if not isinstance(contract, dict):
                continue

            set_key = str(contract.get("entitySetKey") or contract_key).strip()
            profile_key = str(contract.get("profileKey") or "").strip()
            allowed = [
                str(item).strip()
                for item in (contract.get("allowedProfileKeys") or [profile_key])
                if str(item).strip()
            ]
            disallowed = [
                str(item).strip()
                for item in (contract.get("disallowedProfileKeys") or [])
                if str(item).strip()
            ]

            if not set_key or not profile_key:
                continue

            resolved[str(contract_key).strip()] = {
                "entitySetKey": set_key,
                "profileKey": profile_key,
                "allowedProfileKeys": tuple(allowed or [profile_key]),
                "disallowedProfileKeys": tuple(disallowed),
                "validatePathWithoutEntity": contract.get("validatePathWithoutEntity") is True,
                "entitySet": presentation_profile_service().entity_set(set_key),
            }

        return resolved

    @classmethod
    def resolve_profile_contract(
        cls,
        entity: str | None,
        *,
        path: str | None = None,
    ) -> dict[str, Any] | None:
        token = str(entity or "").strip()

        if not token:
            return None

        for contract in cls.entity_set_profile_contracts().values():
            if token in contract.get("entitySet") or frozenset():
                resolved_key = presentation_profile_service().resolve_profile_key(path, token)

                return {
                    **contract,
                    "entity": token,
                    "resolvedProfileKey": resolved_key,
                    "matchesExpected": resolved_key in set(contract.get("allowedProfileKeys") or ()),
                    "isDisallowed": resolved_key in set(contract.get("disallowedProfileKeys") or ()),
                }

        return None

