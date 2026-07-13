"""Perguntas sobre descrição técnica de MP e intermediários (Normas + códigos 50xx)."""

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
    _INTERMEDIATE_FAMILY_RE = re.compile(r"\b(50\d{2})(?:\d{4,})?\b")
    _INTERMEDIATE_INSULATION_TOKEN_RE = re.compile(
        r"(?<![a-z0-9])c[abftv](?:\d|,\d)",
        re.IGNORECASE,
    )
    _MP_GROUP_RE = re.compile(r"\bgrupo\s+(10\d{2})\b")

    @classmethod
    def requires_normas_knowledge(cls, message: str | None) -> bool:
        vocab = ChatTechnicalDescriptionVocabularyService
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        intermediate_query = cls._is_intermediate_nomenclature_query(normalized)

        if cls._contains_any(normalized, vocab.product_lookup_markers()):
            return False

        if ChatProductQueryIntentService.extract_product_code(message or ""):
            if not intermediate_query:
                return False

        if cls._contains_any(normalized, vocab.normas_markers()):
            return True

        if intermediate_query:
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
            if "grupo " in normalized and re.search(r"\b50\d{2}\b", normalized):
                return True

        if cls._contains_any(normalized, vocab.field_meaning_markers()):
            if cls._contains_any(normalized, vocab.description_fields()):
                return True
            if cls._contains_any(normalized, vocab.description_guidance_markers()):
                return True
            if cls._mentions_color_abbreviation(normalized):
                return True
            if cls._mentions_insulation_code(normalized):
                return True

        if re.search(r"\bgrupo\s+10\d{2}\b", normalized) and (
            "descricao" in normalized or "estrutura" in normalized or "campo" in normalized
        ):
            return True

        if re.search(r"\bgrupo\s+50\d{2}\b", normalized) and (
            "descricao" in normalized
            or "estrutura" in normalized
            or "codigo" in normalized
            or "campo" in normalized
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

        group_match = cls._MP_GROUP_RE.search(normalized)

        if group_match:
            code = group_match.group(1)
            return code, f"grupo {code}", code

        family_match = cls._INTERMEDIATE_FAMILY_RE.search(normalized)

        if family_match:
            code = family_match.group(1)
            return code, "intermediários", code

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
    def resolve_insulation_code(cls, token: str | None) -> str | None:
        return ChatTechnicalDescriptionVocabularyService.resolve_insulation_code(token)

    @classmethod
    def build_rag_query(cls, message: str | None) -> str:
        vocab = ChatTechnicalDescriptionVocabularyService
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        parts = list(vocab.rag_query_seeds())
        intermediate = cls._is_intermediate_nomenclature_query(normalized)
        group = cls.resolve_material_group(normalized)

        if intermediate or (group and str(group[0]).startswith("50")):
            parts.extend(vocab.intermediate_rag_query_seeds())

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
                ]
            )
            if intermediate or (group and str(group[0]).startswith("50")):
                parts.append("cor 4 letras intermediário")
            else:
                parts.append("COR abreviação 1ª e 4ª letra")

        insulation = cls._first_insulation_code_in_text(normalized)

        if insulation:
            meaning = cls.resolve_insulation_code(insulation)
            parts.extend(
                [
                    f"isolação {insulation}",
                    meaning or "",
                    "material de isolação bitola",
                ]
            )

        if normalized:
            parts.append(normalized)

        return " ".join(dict.fromkeys(part for part in parts if part))

    @classmethod
    def _is_intermediate_nomenclature_query(cls, normalized: str) -> bool:
        vocab = ChatTechnicalDescriptionVocabularyService

        if not normalized:
            return False

        if "intermedi" in normalized:
            return True

        if cls._contains_any(
            normalized,
            (
                "familia 50",
                "familia 50xx",
                "50xx",
                "codigo intermediario",
                "nomenclatura intermediario",
            ),
        ):
            return True

        has_family = bool(cls._INTERMEDIATE_FAMILY_RE.search(normalized))
        has_structure = cls._has_intermediate_structure_tokens(normalized)
        has_guidance = cls._contains_any(normalized, vocab.guidance_verbs())

        if has_family and (
            has_structure
            or has_guidance
            or "estrutura" in normalized
            or "decape" in normalized
            or "nomenclatura" in normalized
        ):
            return True

        if has_structure and (
            has_guidance
            or "estrutura" in normalized
            or "decape" in normalized
            or "nomenclatura" in normalized
        ):
            return True

        return False

    @classmethod
    def _has_intermediate_structure_tokens(cls, normalized: str) -> bool:
        if cls._INTERMEDIATE_INSULATION_TOKEN_RE.search(normalized or ""):
            return True

        if re.search(r"\b\d{2}/\d{2}\b", normalized or ""):
            return True

        # Cores de 4 letras típicas do intermediário (PRET, VERD, …).
        for token in ("PRET", "BRAN", "VERD", "AZUL", "VERM", "AMAR", "CINZ", "MARR"):
            if re.search(rf"(?<![a-z0-9]){token.lower()}(?![a-z0-9])", normalized or ""):
                return True

        return False

    @classmethod
    def _mentions_color_abbreviation(cls, normalized: str) -> bool:
        return cls._first_color_abbreviation_in_text(normalized) is not None

    @classmethod
    def _mentions_insulation_code(cls, normalized: str) -> bool:
        return cls._first_insulation_code_in_text(normalized) is not None

    @classmethod
    def _first_color_abbreviation_in_text(cls, normalized: str) -> str | None:
        upper = str(normalized or "").upper()

        if not upper.strip():
            return None

        # Compostos / 4 letras primeiro (VDAR, PRET antes de VD/PT).
        tokens = sorted(
            ChatTechnicalDescriptionVocabularyService.color_abbreviation_tokens(),
            key=len,
            reverse=True,
        )

        for token in tokens:
            if re.search(rf"(?<![A-Z0-9]){re.escape(token)}(?![A-Z0-9])", upper):
                return token

        return None

    @classmethod
    def _first_insulation_code_in_text(cls, normalized: str) -> str | None:
        upper = str(normalized or "").upper()

        if not upper.strip():
            return None

        for token in ChatTechnicalDescriptionVocabularyService.insulation_code_tokens():
            if re.search(rf"(?<![A-Z0-9]){re.escape(token)}(?![A-Z0-9])", upper):
                return token

        return None
