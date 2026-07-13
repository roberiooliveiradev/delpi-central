"""Perguntas sobre descrição técnica de matérias-primas (Normas_Tecnicas_DELPI.md)."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_technical_description_vocabulary_service import (
    ChatTechnicalDescriptionVocabularyService,
)


class ChatTechnicalDescriptionIntentService:
    @classmethod
    def requires_normas_knowledge(cls, message: str | None) -> bool:
        vocab = ChatTechnicalDescriptionVocabularyService
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if ChatProductQueryIntentService.extract_product_code(message or ""):
            return False

        if cls._contains_any(normalized, vocab.product_lookup_markers()):
            return False

        if cls._contains_any(normalized, vocab.normas_markers()):
            return True

        if cls._contains_any(normalized, vocab.guidance_verbs()):
            if cls._contains_any(normalized, vocab.description_guidance_markers()):
                return True
            if cls.resolve_material_group(normalized):
                return True
            if "descricao" in normalized:
                return True

        if cls._contains_any(normalized, vocab.description_guidance_markers()):
            if cls.resolve_material_group(normalized):
                return True
            if "grupo " in normalized and re.search(r"\b10\d{2}\b", normalized):
                return True

        if cls._contains_any(normalized, vocab.field_meaning_markers()):
            if cls._contains_any(normalized, vocab.description_fields()):
                return True
            if cls._contains_any(normalized, vocab.description_guidance_markers()):
                return True
            if cls._mentions_color_abbreviation(normalized):
                return True

        if re.search(r"\bgrupo\s+10\d{2}\b", normalized) and (
            "descricao" in normalized or "estrutura" in normalized or "campo" in normalized
        ):
            return True

        return False

    @classmethod
    def resolve_material_group(
        cls,
        normalized_message: str | None,
    ) -> tuple[str, str, str] | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(
            normalized_message
        )

        if not normalized:
            return None

        for group in ChatTechnicalDescriptionVocabularyService.material_groups():
            keywords = group.get("keywords") or ()
            group_code = str(group.get("groupCode") or "").strip()
            label = str(group.get("label") or "").strip()

            if not group_code or not keywords:
                continue

            if cls._contains_any(normalized, keywords):
                return group_code, label, str(keywords[0])

        group_match = re.search(r"\bgrupo\s+(10\d{2})\b", normalized)

        if group_match:
            code = group_match.group(1)
            return code, f"grupo {code}", code

        return None

    @classmethod
    def _contains_any(cls, normalized: str, markers: tuple[str, ...] | list[str]) -> bool:
        return any(
            ChatMessageNormalizationService.strip_accents(marker) in normalized
            for marker in markers
            if str(marker or "").strip()
        )

    @classmethod
    def resolve_color_abbreviation(cls, token: str | None) -> str | None:
        return ChatTechnicalDescriptionVocabularyService.resolve_color_abbreviation(
            token
        )

    @classmethod
    def build_rag_query(cls, message: str | None) -> str:
        vocab = ChatTechnicalDescriptionVocabularyService
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        parts = list(vocab.rag_query_seeds())

        group = cls.resolve_material_group(normalized)

        if group:
            group_code, label, _keyword = group
            parts.extend(
                [
                    f"grupo {group_code}",
                    label,
                    "objetivo abrangência estrutura campos",
                ]
            )

        color = cls._first_color_abbreviation_in_text(normalized)

        if color:
            meaning = cls.resolve_color_abbreviation(color)
            parts.extend(
                [
                    f"abreviação de cor {color}",
                    meaning or "",
                    "COR abreviação 1ª e 4ª letra",
                ]
            )

        if normalized:
            parts.append(normalized)

        return " ".join(dict.fromkeys(part for part in parts if part))

    @classmethod
    def _mentions_color_abbreviation(cls, normalized: str) -> bool:
        return cls._first_color_abbreviation_in_text(normalized) is not None

    @classmethod
    def _first_color_abbreviation_in_text(cls, normalized: str) -> str | None:
        upper = str(normalized or "").upper()

        if not upper.strip():
            return None

        # Compostos primeiro (VDAR antes de VD/AR).
        tokens = sorted(
            ChatTechnicalDescriptionVocabularyService.color_abbreviation_tokens(),
            key=len,
            reverse=True,
        )

        for token in tokens:
            if re.search(rf"(?<![A-Z0-9]){re.escape(token)}(?![A-Z0-9])", upper):
                return token

        return None
