"""Perfil mínimo de apresentação derivado do OpenAPI — Playbook 22 Fase D / E7.S3."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)

_UNKNOWN_ENTITY = "unknown"
_FALLBACK_SHAPE = "unknown"


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
        """E7.S3 — shape sozinho basta; entity opcional (unknown schema / provider externo)."""

        meta = delpi_metadata if isinstance(delpi_metadata, dict) else {}
        shape_token = str(shape or meta.get("shape") or "").strip()
        return bool(shape_token)

    @classmethod
    def normalize_shape(cls, shape: str | None) -> str:
        token = str(shape or "").strip()
        if not token:
            return _FALLBACK_SHAPE
        defaults = cls.node("openapiShapeDefaults") or {}
        if isinstance(defaults, dict) and token in defaults:
            return token
        return _FALLBACK_SHAPE

    @classmethod
    def infer_shape_from_rows(
        cls,
        rows: list[dict[str, Any]] | None,
    ) -> str:
        """Mapeia analyzer.viewIntent → openapiShapeDefaults (schema desconhecido)."""

        from app.domain.services.chat_presentation_data_shape_analyzer import (
            ChatPresentationDataShapeAnalyzer,
        )

        analysis = ChatPresentationDataShapeAnalyzer.analyze(rows=rows)
        view_intent = str(analysis.get("viewIntent") or "unknown").strip()
        mapping = cls.node("openapiShapeFromAnalyzer") or {}
        if isinstance(mapping, dict):
            mapped = str(mapping.get(view_intent) or "").strip()
            if mapped:
                return cls.normalize_shape(mapped)
        recommended = str(analysis.get("recommended") or "").strip().casefold()
        if recommended == "tree" or analysis.get("hasHierarchy"):
            return "hierarchy"
        if recommended == "kpi":
            return "scalar"
        if recommended in {"table", "bar", "donut", "line"}:
            return "list"
        return _FALLBACK_SHAPE

    @classmethod
    def build_profile(
        cls,
        *,
        entity: str | None = None,
        shape: str | None = None,
        delpi_metadata: dict[str, Any] | None = None,
        rows: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        meta = dict(delpi_metadata) if isinstance(delpi_metadata, dict) else {}
        entity_token = str(entity or meta.get("entity") or "").strip() or _UNKNOWN_ENTITY
        shape_token = str(shape or meta.get("shape") or "").strip()
        if not shape_token and rows is not None:
            shape_token = cls.infer_shape_from_rows(rows)
        shape_token = cls.normalize_shape(shape_token)

        presentation = meta.get("presentation")
        presentation_block = dict(presentation) if isinstance(presentation, dict) else {}

        strategy_token = str(
            presentation_block.get("strategy") or "as_delivered"
        ).strip().lower()

        shape_defaults = cls.node("openapiShapeDefaults") or {}
        shape_profile = dict(shape_defaults.get(shape_token) or {})
        if not shape_profile and isinstance(shape_defaults, dict):
            shape_profile = dict(shape_defaults.get(_FALLBACK_SHAPE) or {})

        merged = dict(cls.node("defaults") or {})

        # Herda viewOrder/stack do perfil JSON equivalente ao shape (ex.: playbook_report
        # → tabela primeiro). Sem isso, defaults.text-first oculta evidência tabular.
        equivalent_key = cls.json_profile_equivalent_for_shape(shape_token)

        if equivalent_key and equivalent_key != "generic":
            from app.domain.services.chat_presentation_profile_service import (
                ChatPresentationProfileService,
            )

            equivalent = ChatPresentationProfileService.profile(equivalent_key)

            if isinstance(equivalent, dict):
                for field in (
                    "viewOrder",
                    "stackPlan",
                    "flags",
                    "stackTailPolicy",
                    "stackLayoutPolicy",
                    "viewBuildPolicy",
                ):
                    if field not in shape_profile and equivalent.get(field) is not None:
                        merged[field] = equivalent[field]

        merged.update(shape_profile)
        merged["presentationStrategy"] = "as_delivered"
        merged["openapiDerived"] = True
        merged["openapiEntity"] = entity_token
        merged["openapiShape"] = shape_token
        if entity_token == _UNKNOWN_ENTITY:
            merged["profileKey"] = f"openapi:shape:{shape_token}"
        else:
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
        entity_token = str(entity or "").strip()

        if key in cls.replaceable_profile_keys():
            return True

        # Shape-only / entity desconhecida: preferir defaults OpenAPI a generic JSON.
        if key == "generic":
            if not entity_token:
                return True
            return entity_token not in cls.mapping("entityProfiles")

        return False

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
