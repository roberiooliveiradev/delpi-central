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



class ChatPresentationProfileOpenApiService:
    @classmethod
    def is_enriched_openapi_presentation(
        cls,
        *,
        delpi_metadata: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> bool:
        if isinstance(profile, dict):
            if str(profile.get("openapiPresentationStrategy") or "").strip().lower() == "enriched":
                return True

        if not isinstance(delpi_metadata, dict):
            return False

        presentation = delpi_metadata.get("presentation")

        if not isinstance(presentation, dict):
            return False

        return str(presentation.get("strategy") or "").strip().lower() == "enriched"

    @classmethod
    def allows_automatic_rich_stack(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        if isinstance(metadata, dict):
            cached = metadata.get("presentationProfile")

            if isinstance(cached, dict) and cls.is_enriched_openapi_presentation(profile=cached):
                profile = cached
            else:
                profile = presentation_profile_service().resolve_profile(
                    path,
                    entity,
                    delpi_metadata=delpi_metadata or metadata.get("delpiMetadata"),
                    metadata=metadata,
                )
        else:
            profile = presentation_profile_service().resolve_profile(
                path,
                entity,
                delpi_metadata=delpi_metadata,
            )

        if not cls.is_enriched_openapi_presentation(
            delpi_metadata=delpi_metadata,
            profile=profile,
        ):
            return False

        stack_policy = str(profile.get("stackLayoutPolicy") or "on_demand").strip().lower()

        return stack_policy == "always"

    @classmethod
    def _stamp_openapi_presentation_strategy(
        cls,
        profile: dict[str, Any],
        delpi_metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if cls.is_enriched_openapi_presentation(delpi_metadata=delpi_metadata):
            profile["openapiPresentationStrategy"] = "enriched"

        return profile

    @classmethod
    def uses_schema_first_presentation(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> bool:
        """Playbook 22 — default global: API as-delivered; legacy só com flag explícita."""
        profile_key = str(presentation_profile_service().resolve_profile_key(path, entity)).strip()
        profile_only = presentation_profile_service().profile(profile_key)
        explicit = str(profile_only.get("presentationStrategy") or "").strip().lower()

        return explicit != "legacy"

    @classmethod
    def is_rich_stack_profile(cls, profile_key: str | None) -> bool:
        key = str(profile_key or "").strip()

        if not key:
            return False

        profile_only = presentation_profile_service().profile(key)
        defaults = presentation_profile_service().node("defaults") or {}
        strategy = str(
            profile_only.get("presentationStrategy")
            or defaults.get("presentationStrategy")
            or "as_delivered"
        ).strip().lower()

        if strategy != "legacy":
            return False

        if key in presentation_profile_service().entity_set("richStackProfiles"):
            return True

        merged = dict(defaults)
        merged.update(profile_only)

        return str(merged.get("stackLayoutPolicy") or "on_demand").strip().lower() == "always"

    @classmethod
    def uses_presentation_table_assembly(cls, entity: str | None) -> bool:
        """Deprecated — table assembly removido; mantido para compat de gates legados."""
        return False

