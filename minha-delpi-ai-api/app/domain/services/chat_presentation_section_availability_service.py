"""Disponibilidade de seções humanizadas — inteligência de apresentação (chat base)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_section_rules_service import (
    ChatPresentationSectionRulesService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class ChatPresentationSectionAvailabilityService:
    """Define quais blocos do stack humanizado têm dado — o MFE só renderiza o que vier True."""

    @classmethod
    def enrich_stack_plan(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        from app.domain.services.chat_presentation_evidence_first_layout_service import (
            ChatPresentationEvidenceFirstLayoutService,
        )

        path = str(metadata.get("path") or "")
        entity = cls._metadata_entity(metadata)
        presentation_mode = None

        if ChatPresentationEvidenceFirstLayoutService.is_active(metadata):
            presentation_mode = ChatPresentationEvidenceFirstLayoutService.presentation_mode()

        stack_config = ChatPresentationProfileService.stack_plan_config(
            path,
            entity,
            presentation_mode=presentation_mode,
        )
        section_rules = stack_config.get("sectionRules")

        if isinstance(section_rules, dict) and section_rules.get("enabled"):
            plan = ChatPresentationSectionRulesService.apply(
                metadata,
                plan,
                stack_config,
                path=path,
                entity=entity,
            )
        else:
            profile_key = ChatPresentationProfileService.resolve_profile_key(path, entity)
            plan["presentationProfile"] = profile_key
            plan["presentationProfileKey"] = profile_key

            from app.domain.services.chat_presentation_stack_markdown_service import (
                ChatPresentationStackMarkdownService,
            )

            plan = ChatPresentationStackMarkdownService.apply_generic_humanized_stack_plan(
                metadata,
                plan,
                profile_key=profile_key,
            )

        if ChatPresentationEvidenceFirstLayoutService.is_active(metadata):
            plan["presentationMode"] = ChatPresentationEvidenceFirstLayoutService.presentation_mode()

        return plan

    @classmethod
    def filter_analyser_highlights(cls, insights: list[str]) -> list[str]:
        """Remove bullets que só comunicam ausência de dado (seção vazia não deve narrar falta)."""
        filtered: list[str] = []

        for line in insights:
            token = str(line or "").strip()

            if not token or ChatPresentationVocabularyService.absence_insight_pattern().search(token):
                continue

            filtered.append(token)

        return filtered

    @classmethod
    def _metadata_entity(cls, metadata: dict[str, Any]) -> str | None:
        api_meta = metadata.get("apiDelpiResponseMeta")

        if not isinstance(api_meta, dict):
            return None

        raw_entity = api_meta.get("entity")

        if isinstance(raw_entity, str) and raw_entity.strip():
            return raw_entity.strip()

        return None
