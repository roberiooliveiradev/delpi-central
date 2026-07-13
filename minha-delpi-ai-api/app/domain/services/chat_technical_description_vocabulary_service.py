"""Vocabulário PT de descrição técnica / Normas DELPI — bundle ``technical_description_vocabulary``."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatTechnicalDescriptionVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "technical_description_vocabulary"

    @classmethod
    def guidance_verbs(cls) -> tuple[str, ...]:
        return cls.terms("guidanceVerbs")

    @classmethod
    def normas_markers(cls) -> tuple[str, ...]:
        return cls.terms("normasMarkers")

    @classmethod
    def description_guidance_markers(cls) -> tuple[str, ...]:
        return cls.terms("descriptionGuidanceMarkers")

    @classmethod
    def field_meaning_markers(cls) -> tuple[str, ...]:
        return cls.terms("fieldMeaningMarkers")

    @classmethod
    def description_fields(cls) -> tuple[str, ...]:
        return cls.terms("descriptionFields")

    @classmethod
    def product_lookup_markers(cls) -> tuple[str, ...]:
        return cls.terms("productLookupMarkers")

    @classmethod
    def rag_query_seeds(cls) -> tuple[str, ...]:
        return cls.terms("ragQuerySeeds")

    @classmethod
    def intermediate_rag_query_seeds(cls) -> tuple[str, ...]:
        return cls.terms("intermediateRagQuerySeeds")

    @classmethod
    def source_docs(cls) -> tuple[str, ...]:
        return cls.terms("sourceDocs")

    @classmethod
    def insulation_codes(cls) -> dict[str, str]:
        return {
            str(key).strip().upper(): str(value).strip()
            for key, value in cls.mapping("insulationCodes").items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def resolve_insulation_code(cls, token: str | None) -> str | None:
        compact = "".join(ch for ch in str(token or "").upper() if ch.isalnum())

        if not compact:
            return None

        return cls.insulation_codes().get(compact)

    @classmethod
    def insulation_code_tokens(cls) -> tuple[str, ...]:
        return tuple(cls.insulation_codes().keys())

    @classmethod
    def material_groups(cls) -> tuple[dict[str, Any], ...]:
        raw = cls.node("materialGroups")

        if not isinstance(raw, list):
            return ()

        groups: list[dict[str, Any]] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            keywords = item.get("keywords") or []

            if not isinstance(keywords, list):
                keywords = []

            groups.append(
                {
                    "groupCode": str(item.get("groupCode") or "").strip(),
                    "label": str(item.get("label") or "").strip(),
                    "keywords": tuple(
                        str(keyword).strip()
                        for keyword in keywords
                        if str(keyword).strip()
                    ),
                }
            )

        return tuple(groups)

    @classmethod
    def color_abbreviations(cls) -> dict[str, str]:
        return {
            str(key).strip().upper(): str(value).strip()
            for key, value in cls.mapping("colorAbbreviations").items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def resolve_color_abbreviation(cls, token: str | None) -> str | None:
        compact = "".join(ch for ch in str(token or "").upper() if ch.isalnum())

        if not compact:
            return None

        return cls.color_abbreviations().get(compact)

    @classmethod
    def color_abbreviation_tokens(cls) -> tuple[str, ...]:
        return tuple(cls.color_abbreviations().keys())
