"""Classifica códigos do desenho (PI 50xx × MP 10xx × consumível) via vocabulário técnico.

Ponte canônica entre ``technical_description_vocabulary`` e o pipeline de validação
de desenho — evita falso intermediário e alinha assinatura CA–CV / cor 4 letras.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_technical_description_vocabulary_service import (
    ChatTechnicalDescriptionVocabularyService,
)

_COMPILED: dict[str, re.Pattern[str]] = {}


@dataclass(frozen=True)
class DrawingProductFamily:
    kind: str
    group_code: str | None = None
    label: str | None = None


class ChatDrawingProductFamilyClassificationService:
    KIND_INTERMEDIATE = "intermediate"
    KIND_RAW_MATERIAL = "raw_material"
    KIND_CONSUMABLE = "consumable"
    KIND_FINISHED = "finished"
    KIND_UNKNOWN = "unknown"

    @classmethod
    def classify(
        cls,
        code: str | None,
        *,
        description: str | None = None,
    ) -> DrawingProductFamily:
        normalized = ChatProductQueryIntentService.normalize_product_code(code or "")

        if not normalized:
            return DrawingProductFamily(kind=cls.KIND_UNKNOWN)

        if ChatDrawingPatternsService.is_finished_product(normalized):
            return DrawingProductFamily(kind=cls.KIND_FINISHED, group_code=normalized[:4])

        if ChatDrawingPatternsService.is_intermediate_family(normalized):
            if cls.is_false_intermediate_candidate(
                normalized,
                description=description,
            ):
                return DrawingProductFamily(
                    kind=cls.KIND_CONSUMABLE,
                    group_code="50xx",
                    label="falso intermediário / consumível",
                )

            return DrawingProductFamily(
                kind=cls.KIND_INTERMEDIATE,
                group_code=normalized[:4] if len(normalized) >= 4 else "50xx",
                label="intermediários",
            )

        group_code = cls.resolve_mp_group_code(normalized)
        desc = str(description or "")

        if cls.is_consumable_mp(normalized, description=desc):
            return DrawingProductFamily(
                kind=cls.KIND_CONSUMABLE,
                group_code=group_code,
                label=cls._label_for_group(group_code) or "consumível",
            )

        if group_code or ChatDrawingPatternsService.is_bom_component(normalized):
            return DrawingProductFamily(
                kind=cls.KIND_RAW_MATERIAL,
                group_code=group_code,
                label=cls._label_for_group(group_code) or "matéria-prima",
            )

        return DrawingProductFamily(kind=cls.KIND_UNKNOWN)

    @classmethod
    def resolve_mp_group_code(cls, code: str | None) -> str | None:
        normalized = ChatProductQueryIntentService.normalize_product_code(code or "")

        if not normalized:
            return None

        for prefix in sorted(
            ChatTechnicalDescriptionVocabularyService.material_group_code_prefixes(),
            key=len,
            reverse=True,
        ):
            if normalized.startswith(prefix):
                return prefix

        return None

    @classmethod
    def is_consumable_mp(cls, code: str | None, *, description: str | None = None) -> bool:
        normalized = ChatProductQueryIntentService.normalize_product_code(code or "")
        group_code = cls.resolve_mp_group_code(normalized)

        if group_code and group_code in set(
            ChatTechnicalDescriptionVocabularyService.consumable_group_codes()
        ):
            return True

        for prefix in ChatDrawingPatternsService.length_consumable_code_prefixes():
            if normalized.startswith(prefix):
                return True

        folded = str(description or "").upper().replace(" ", "")

        if not folded:
            return False

        for marker in ChatDrawingPatternsService.length_consumable_description_markers():
            if marker and marker.replace(" ", "") in folded:
                return True

        for noise in cls._consumable_description_noise_markers():
            if noise in folded:
                return True

        return False

    @classmethod
    def is_false_intermediate_candidate(
        cls,
        code: str | None,
        *,
        description: str | None = None,
    ) -> bool:
        """50xx sem assinatura de cabo / com descrição de consumível."""
        normalized = ChatProductQueryIntentService.normalize_product_code(code or "")

        if not normalized or not ChatDrawingPatternsService.is_intermediate_family(
            normalized
        ):
            return False

        text = str(description or "").strip()

        if not text:
            return True

        if cls.has_intermediate_signature(text):
            return False

        folded = text.upper().replace(" ", "")

        for marker in cls.consumable_description_noise_markers():
            if marker in folded:
                return True

        return False

    @classmethod
    def has_intermediate_signature(cls, description: str | None) -> bool:
        text = str(description or "")

        if not text.strip():
            return False

        if ChatDrawingPatternsService.intermediate_segment().search(text):
            return True

        if ChatDrawingPatternsService.compile_validation("intermediateDatePath").search(
            text
        ):
            return True

        return cls._has_vocabulary_intermediate_signature(text)

    @classmethod
    def extract_intermediate_color(cls, signature_or_description: str | None) -> str | None:
        compact = str(signature_or_description or "").upper().replace(" ", "")

        if not compact:
            return None

        match = cls.intermediate_color_signature_pattern().match(compact)

        if match:
            return str(match.group(1) or "").upper() or None

        for color in ChatTechnicalDescriptionVocabularyService.intermediate_four_letter_colors():
            if re.search(rf"(?<![A-Z0-9]){re.escape(color)}(?![A-Z0-9])", compact):
                return color

        return None

    @classmethod
    def intermediate_color_signature_pattern(cls) -> re.Pattern[str]:
        cache_key = "intermediate_color_signature_vocab"

        if cache_key not in _COMPILED:
            tokens = sorted(
                ChatTechnicalDescriptionVocabularyService.insulation_code_tokens(),
                key=len,
                reverse=True,
            ) or ["CA", "CB", "CF", "CT", "CV"]
            joined = "|".join(re.escape(token) for token in tokens)
            _COMPILED[cache_key] = re.compile(
                rf"^(?:{joined})[\d,.]+([A-Z]{{4}})",
                re.IGNORECASE,
            )

        return _COMPILED[cache_key]

    @classmethod
    def vocabulary_color_ocr_markers(cls, color: str) -> tuple[str, ...]:
        normalized_color = str(color or "").strip().upper()

        if not normalized_color:
            return ()

        markers: list[str] = []

        for insulation in ChatTechnicalDescriptionVocabularyService.insulation_code_tokens():
            markers.append(f"{insulation}20{normalized_color}")
            markers.append(f"{insulation}{normalized_color}")

        markers.append(normalized_color)
        return tuple(dict.fromkeys(markers))

    @classmethod
    def is_credible_intermediate_code(
        cls,
        code: str | None,
        *,
        description: str | None = None,
        allow_empty_description: bool = False,
    ) -> bool:
        normalized = ChatProductQueryIntentService.normalize_product_code(code or "")

        if not normalized or not ChatDrawingPatternsService.is_intermediate_family(
            normalized
        ):
            return False

        if cls.is_false_intermediate_candidate(normalized, description=description):
            return False

        text = str(description or "").strip()

        if not text:
            return allow_empty_description

        return True

    @classmethod
    def consumable_description_noise_markers(cls) -> tuple[str, ...]:
        node = ChatDrawingPatternsService.validation_rule("intermediateBomEvidence")
        markers: list[str] = []

        if isinstance(node, dict):
            raw = node.get("consumableDescriptionNoise")

            if isinstance(raw, list):
                markers.extend(
                    str(marker).strip().upper().replace(" ", "")
                    for marker in raw
                    if str(marker).strip()
                )

        for group in ChatTechnicalDescriptionVocabularyService.material_groups():
            group_code = str(group.get("groupCode") or "").strip()

            if group_code not in set(
                ChatTechnicalDescriptionVocabularyService.consumable_group_codes()
            ):
                continue

            for keyword in group.get("keywords") or ():
                folded = str(keyword).strip().upper().replace(" ", "").replace("-", "")

                if folded:
                    markers.append(folded)

        return tuple(dict.fromkeys(markers))

    @classmethod
    def _has_vocabulary_intermediate_signature(cls, description: str) -> bool:
        compact = str(description or "").upper().replace(" ", "")

        if not compact:
            return False

        tokens = ChatTechnicalDescriptionVocabularyService.insulation_code_tokens() or (
            "CA",
            "CB",
            "CF",
            "CT",
            "CV",
        )
        joined = "|".join(re.escape(token) for token in sorted(tokens, key=len, reverse=True))
        insulation_hit = bool(re.search(rf"(?:{joined})[\d,.]", compact))

        if not insulation_hit:
            return False

        for color in ChatTechnicalDescriptionVocabularyService.intermediate_four_letter_colors():
            if color and color in compact:
                return True

        return False

    @classmethod
    def _label_for_group(cls, group_code: str | None) -> str | None:
        if not group_code:
            return None

        for group in ChatTechnicalDescriptionVocabularyService.material_groups():
            code = str(group.get("groupCode") or "").strip()

            if code == group_code:
                return str(group.get("label") or "").strip() or None

            if "-" in code:
                try:
                    start_raw, end_raw = code.split("-", 1)
                    start = int(start_raw)
                    end = int(end_raw)
                    value = int(group_code)
                except ValueError:
                    continue

                if start <= value <= end:
                    return str(group.get("label") or "").strip() or None

        return None
