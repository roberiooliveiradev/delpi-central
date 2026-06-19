"""Padrões regex e constantes de extração/validação de desenhos — bundles assistant."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_STAMP_BUNDLE = "drawing_stamp"
_VALIDATION_BUNDLE = "drawing_validation"
_COMPILED: dict[str, re.Pattern[str]] = {}
_COMPILED_LISTS: dict[str, tuple[re.Pattern[str], ...]] = {}
_DEFAULT_FLAGS = re.IGNORECASE


class ChatDrawingPatternsService:
    @classmethod
    def compile_stamp(cls, key: str) -> re.Pattern[str]:
        cache_key = f"stamp:{key}"

        if cache_key not in _COMPILED:
            raw = ChatAssistantContentService.get(_STAMP_BUNDLE, "patterns", key, default="")
            _COMPILED[cache_key] = re.compile(str(raw), _DEFAULT_FLAGS)

        return _COMPILED[cache_key]

    @classmethod
    def compile_stamp_list(cls, key: str) -> tuple[re.Pattern[str], ...]:
        cache_key = f"stamp_list:{key}"

        if cache_key not in _COMPILED_LISTS:
            patterns = ChatAssistantContentService.list(
                _STAMP_BUNDLE,
                "patternLists",
                key,
            )
            _COMPILED_LISTS[cache_key] = tuple(
                re.compile(str(item), _DEFAULT_FLAGS)
                for item in patterns
                if str(item).strip()
            )

        return _COMPILED_LISTS[cache_key]

    @classmethod
    def component_code(cls) -> re.Pattern[str]:
        return cls.compile_stamp("componentCode")

    @classmethod
    def intermediate_code(cls) -> re.Pattern[str]:
        return cls.compile_stamp("intermediateCode")

    @classmethod
    def finished_product_code(cls) -> re.Pattern[str]:
        return cls.compile_stamp("finishedProductCode")

    @classmethod
    def finished_product_code_anchor(cls) -> re.Pattern[str]:
        cache_key = "stamp:finishedProductCodeAnchor"

        if cache_key not in _COMPILED:
            raw = ChatAssistantContentService.get(
                _STAMP_BUNDLE,
                "patterns",
                "finishedProductCodeAnchor",
                default=r"^90\d{6}$",
            )
            _COMPILED[cache_key] = re.compile(str(raw))

        return _COMPILED[cache_key]

    @classmethod
    def revision(cls) -> re.Pattern[str]:
        return cls.compile_stamp("revision")

    @classmethod
    def internal_revision_table(cls) -> re.Pattern[str]:
        return cls.compile_stamp("internalRevisionTable")

    @classmethod
    def bom_section(cls) -> re.Pattern[str]:
        return cls.compile_stamp("bomSection")

    @classmethod
    def bom_quantity(cls) -> re.Pattern[str]:
        return cls.compile_stamp("bomQuantity")

    @classmethod
    def intermediate_segment(cls) -> re.Pattern[str]:
        return cls.compile_stamp("intermediateSegment")

    @classmethod
    def cota_decape_length(cls) -> re.Pattern[str]:
        return cls.compile_stamp("cotaDecapeLength")

    @classmethod
    def generic_decape(cls) -> re.Pattern[str]:
        return cls.compile_stamp("genericDecape")

    @classmethod
    def decape_note(cls) -> re.Pattern[str]:
        return cls.compile_stamp("decapeNote")

    @classmethod
    def hint_number_tail(cls) -> re.Pattern[str]:
        return cls.compile_stamp("hintNumberTail")

    @classmethod
    def length_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return cls.compile_stamp_list("length")

    @classmethod
    def decape_left_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return cls.compile_stamp_list("decapeLeft")

    @classmethod
    def decape_right_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return cls.compile_stamp_list("decapeRight")

    @classmethod
    def pdf_length_pattern(cls) -> re.Pattern[str]:
        patterns = cls.compile_stamp_list("pdfLength")

        if patterns:
            return patterns[0]

        return cls.compile_stamp("lengthSimple")

    @classmethod
    def pdf_decape_left_pattern(cls) -> re.Pattern[str]:
        patterns = cls.compile_stamp_list("pdfDecapeLeft")

        if patterns:
            return patterns[0]

        return cls.compile_stamp("pdfDecapeLeft")

    @classmethod
    def pdf_decape_right_pattern(cls) -> re.Pattern[str]:
        patterns = cls.compile_stamp_list("pdfDecapeRight")

        if patterns:
            return patterns[0]

        return cls.compile_stamp("pdfDecapeRight")

    @classmethod
    def ocr_normalization(cls, key: str, default: Any = None) -> Any:
        node = ChatAssistantContentService.get_node(_STAMP_BUNDLE, "ocrNormalization") or {}
        return node.get(key, default)

    @classmethod
    def ocr_connector_typo_pattern(cls) -> re.Pattern[str]:
        cache_key = "ocr:connectorTypo"

        if cache_key not in _COMPILED:
            raw = str(cls.ocr_normalization("connectorTypoPattern") or r"^40\d{6}$")
            _COMPILED[cache_key] = re.compile(raw)

        return _COMPILED[cache_key]

    @classmethod
    def intermediate_prefix(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _STAMP_BUNDLE,
                "codeFamilies",
                "intermediatePrefix",
                default="50",
            )
        )

    @classmethod
    def is_intermediate_family(cls, code: str) -> bool:
        prefix = cls.intermediate_prefix()

        return bool(code) and str(code).startswith(prefix)

    @classmethod
    def extraction_limit_int(cls, key: str, default: int) -> int:
        raw = ChatAssistantContentService.get(
            _STAMP_BUNDLE,
            "extractionLimits",
            key,
            default=str(default),
        )

        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def extraction_limit_float(cls, key: str, default: float) -> float:
        raw = ChatAssistantContentService.get(
            _STAMP_BUNDLE,
            "extractionLimits",
            key,
            default=str(default),
        )

        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def validation_rule(cls, key: str, default: Any = None) -> Any:
        node = ChatAssistantContentService.get_node(
            _VALIDATION_BUNDLE,
            "validationRules",
        ) or {}

        return node.get(key, default)

    @classmethod
    def validation_rule_float(cls, key: str, default: float) -> float:
        raw = cls.validation_rule(key, default)

        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def validation_rule_int(cls, key: str, default: int) -> int:
        raw = cls.validation_rule(key, default)

        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def length_tolerance_ratio(cls) -> float:
        return cls.validation_rule_float("lengthToleranceRatio", 0.05)

    @classmethod
    def decape_tolerance_mm(cls) -> float:
        return cls.validation_rule_float("decapeToleranceMm", 1.0)

    @classmethod
    def max_root_structure_quantity_mm(cls) -> float:
        return cls.validation_rule_float("maxRootStructureQuantityMm", 1000.0)

    @classmethod
    def max_segment_length_checks(cls) -> int:
        return cls.validation_rule_int("maxSegmentLengthChecks", 6)

    @classmethod
    def final_inspection_work_center_prefix(cls) -> str:
        return str(cls.validation_rule("finalInspectionWorkCenterPrefix", "CT-99"))

    @classmethod
    def unit_suffixes(cls) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(
            _VALIDATION_BUNDLE,
            "validationRules",
            "unitSuffixes",
        )
        return tuple(str(item).strip().lower() for item in items if str(item).strip())
