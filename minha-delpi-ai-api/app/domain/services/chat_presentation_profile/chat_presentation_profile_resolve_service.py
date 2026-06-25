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



class ChatPresentationProfileResolveService:
    @classmethod
    def resolve_profile_key(cls, path: str | None, entity: str | None = None) -> str:
        entity_token = str(entity or "").strip() or presentation_profile_service().resolve_entity_from_path(path)

        if entity_token:
            mapped = presentation_profile_service().mapping("entityProfiles").get(entity_token)

            if mapped:
                return str(mapped)

            if OpenApiPresentationProfileDeriverService.is_openapi_backed_entity(entity_token):
                return "generic"

        lowered = presentation_profile_service().path_lowered(path)

        for rule in presentation_profile_service().node("pathRules") or []:
            if not isinstance(rule, dict):
                continue

            fragment = str(rule.get("contains") or "").strip().lower()

            if fragment and fragment in lowered:
                if ChatPresentationProfileResolveService._path_rule_suppressed(fragment, lowered):
                    continue

                return str(rule.get("profile") or "generic")

        return "generic"

    @classmethod
    def _path_rule_suppressed(cls, fragment: str, lowered_path: str) -> bool:
        """Evita colisões de fragmentos genéricos com rotas KPI de outros domínios."""
        if fragment == "/stock" and "/supplies/" in lowered_path:
            return True

        return False

    @classmethod
    def commentary_profile_key(
        cls,
        profile_key: str | None = None,
        *,
        path: str | None = None,
        entity: str | None = None,
    ) -> str | None:
        key = str(profile_key or "").strip()

        if not key:
            key = presentation_profile_service().resolve_profile_key(path, entity)

        profile = cls.profile(key)
        explicit = str(profile.get("commentaryProfileKey") or "").strip()

        if explicit:
            return explicit

        operational_keys = {
            "factory_status",
            "stock",
            "production_status",
            "shipping_status",
            "sale_pricing",
            "analyser",
        }

        if key in operational_keys:
            return key

        if key in {"table_list", "generic"}:
            return "generic_list"

        return None

    @classmethod
    def profile(cls, profile_key: str | None = None) -> dict[str, Any]:
        key = str(profile_key or "generic").strip() or "generic"
        resolved = presentation_profile_service().node("profiles", key)

        if isinstance(resolved, dict):
            return resolved

        defaults = presentation_profile_service().node("defaults")

        return defaults if isinstance(defaults, dict) else {}

    @classmethod
    def resolve_profile(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        shape: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if isinstance(metadata, dict):
            cached = metadata.get("presentationProfile")

            if isinstance(cached, dict) and cached.get("profileKey"):
                return dict(cached)

            api_meta = metadata.get("apiDelpiResponseMeta")

            if isinstance(api_meta, dict):
                shape = shape or str(api_meta.get("shape") or "").strip() or None
                entity = entity or str(api_meta.get("entity") or "").strip() or None

            delpi_metadata = delpi_metadata or metadata.get("delpiMetadata")

        return presentation_profile_service().build_resolved_profile(
            path=path,
            entity=entity,
            shape=shape,
            delpi_metadata=delpi_metadata,
        )

    @classmethod
    def build_resolved_profile(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        shape: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entity_token = str(entity or "").strip() or None
        key = presentation_profile_service().resolve_profile_key(path, entity_token)

        if OpenApiPresentationProfileDeriverService.should_use_derived_profile(
            profile_key=key,
            entity=entity_token,
            shape=shape,
            delpi_metadata=delpi_metadata,
        ):
            profile = OpenApiPresentationProfileDeriverService.build_profile(
                entity=entity_token,
                shape=shape,
                delpi_metadata=delpi_metadata,
            )

            return presentation_profile_service()._stamp_openapi_presentation_strategy(profile, delpi_metadata)

        merged = dict(presentation_profile_service().node("defaults") or {})
        merged.update(cls.profile(key))
        merged["profileKey"] = key

        return presentation_profile_service()._stamp_openapi_presentation_strategy(merged, delpi_metadata)

    @classmethod
    def cache_presentation_profile(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        api_meta = metadata.get("apiDelpiResponseMeta")
        entity = None
        shape = None

        if isinstance(api_meta, dict):
            entity = str(api_meta.get("entity") or "").strip() or None
            shape = str(api_meta.get("shape") or "").strip() or None

        metadata["presentationProfile"] = presentation_profile_service().build_resolved_profile(
            path=metadata.get("path"),
            entity=entity,
            shape=shape,
            delpi_metadata=metadata.get("delpiMetadata"),
        )

    @classmethod
    def resolve_effective_profile_key(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        shape: str | None = None,
        operation_id: str | None = None,
    ) -> str:
        entity_token = str(entity or "").strip() or None
        shape_token = str(shape or "").strip() or None

        if not shape_token and operation_id:
            shape_token = OpenApiOperationContractService.shape_for_operation(operation_id)

        if not shape_token and entity_token:
            shape_token = OpenApiOperationContractService.shape_for_entity(entity_token)

        profile = presentation_profile_service().build_resolved_profile(
            path=path,
            entity=entity_token,
            shape=shape_token,
        )

        if profile.get("openapiDerived"):
            return OpenApiPresentationProfileDeriverService.json_profile_equivalent_for_shape(
                str(profile.get("openapiShape") or shape_token or ""),
            )

        return str(profile.get("profileKey") or presentation_profile_service().resolve_profile_key(path, entity_token))

