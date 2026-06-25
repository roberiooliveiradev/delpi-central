"""Perfil mínimo de apresentação derivado do OpenAPI — Playbook 22 Fase D."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class OpenApiPresentationProfileDeriverService(ChatAssistantVocabularyService):
    BUNDLE = "presentation_profiles"

    @classmethod
    def replaceable_profile_keys(cls) -> frozenset[str]:
        raw = cls.node("openapiReplaceableProfileKeys")

        if not isinstance(raw, list):
            return frozenset()

        return frozenset(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def can_derive(
        cls,
        *,
        entity: str | None,
        shape: str | None,
        delpi_metadata: dict[str, Any] | None = None,
    ) -> bool:
        meta = delpi_metadata if isinstance(delpi_metadata, dict) else {}
        entity_token = str(entity or meta.get("entity") or "").strip()
        shape_token = str(shape or meta.get("shape") or "").strip()

        return bool(entity_token and shape_token)

    @classmethod
    def build_profile(
        cls,
        *,
        entity: str | None = None,
        shape: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        meta = dict(delpi_metadata) if isinstance(delpi_metadata, dict) else {}
        entity_token = str(entity or meta.get("entity") or "").strip()
        shape_token = str(shape or meta.get("shape") or "").strip()
        presentation = meta.get("presentation")
        presentation_block = dict(presentation) if isinstance(presentation, dict) else {}

        strategy_token = str(
            presentation_block.get("strategy") or "as_delivered"
        ).strip().lower()

        shape_defaults = cls.node("openapiShapeDefaults") or {}
        shape_profile = dict(shape_defaults.get(shape_token) or {})

        merged = dict(cls.node("defaults") or {})
        merged.update(shape_profile)
        merged["presentationStrategy"] = "as_delivered"
        merged["openapiDerived"] = True
        merged["openapiEntity"] = entity_token
        merged["openapiShape"] = shape_token
        merged["profileKey"] = f"openapi:{entity_token}"

        if strategy_token == "enriched":
            merged["openapiPresentationStrategy"] = "enriched"
            entity_profiles = cls.mapping("entityProfiles")
            profile_key = str(entity_profiles.get(entity_token) or "").strip()

            if profile_key:
                from app.domain.services.chat_presentation_profile_service import (
                    ChatPresentationProfileService,
                )

                json_profile = ChatPresentationProfileService.profile(profile_key)
                merged.update(json_profile)
                merged["profileKey"] = profile_key

        if presentation_block:
            merged["openapiPresentation"] = presentation_block

        return merged

    @classmethod
    def should_use_derived_profile(
        cls,
        *,
        profile_key: str,
        entity: str | None,
        shape: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
    ) -> bool:
        if not cls.can_derive(
            entity=entity,
            shape=shape,
            delpi_metadata=delpi_metadata,
        ):
            return False

        key = str(profile_key or "").strip() or "generic"

        if key in cls.replaceable_profile_keys():
            return True

        entity_token = str(entity or "").strip()

        if key != "generic" or not entity_token:
            return False

        return entity_token not in cls.mapping("entityProfiles")

    @classmethod
    def json_profile_equivalent_for_shape(cls, shape: str | None) -> str:
        token = str(shape or "").strip()
        equivalents = cls.node("openapiShapeProfileEquivalents") or {}

        if not token or not isinstance(equivalents, dict):
            return "generic"

        return str(equivalents.get(token) or "generic").strip() or "generic"

    @classmethod
    def is_openapi_backed_entity(cls, entity: str | None) -> bool:
        entity_token = str(entity or "").strip()

        if not entity_token:
            return False

        return entity_token not in cls.mapping("entityProfiles")
