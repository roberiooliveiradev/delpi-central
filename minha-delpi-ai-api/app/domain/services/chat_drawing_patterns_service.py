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
    def bom_table_header(cls) -> re.Pattern[str]:
        return cls.compile_stamp("bomTableHeader")

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
    def segment_length_tolerance(cls) -> re.Pattern[str]:
        return cls.compile_stamp("segmentLengthTolerance")

    @classmethod
    def decape_tolerance(cls) -> re.Pattern[str]:
        return cls.compile_stamp("decapeTolerance")

    @classmethod
    def glued_tolerance_cota(cls) -> re.Pattern[str]:
        return cls.compile_stamp("gluedToleranceCota")

    @classmethod
    def max_segment_length_mm(cls) -> float:
        raw = ChatAssistantContentService.get(
            _STAMP_BUNDLE,
            "dimensionHeuristics",
            "maxSegmentLengthMm",
            default="6000",
        )

        try:
            return float(raw)
        except (TypeError, ValueError):
            return 6000.0

    @classmethod
    def max_decape_mm(cls) -> float:
        raw = ChatAssistantContentService.get(
            _STAMP_BUNDLE,
            "dimensionHeuristics",
            "maxDecapeMm",
            default="50",
        )

        try:
            return float(raw)
        except (TypeError, ValueError):
            return 50.0

    @classmethod
    def unlabeled_decape_tolerance_side(cls) -> str:
        raw = str(
            ChatAssistantContentService.get(
                _STAMP_BUNDLE,
                "dimensionHeuristics",
                "unlabeledDecapeToleranceSide",
                default="right",
            )
            or "right"
        ).strip().lower()

        return raw if raw in {"left", "right"} else "right"

    @classmethod
    def generic_decape(cls) -> re.Pattern[str]:
        return cls.compile_stamp("genericDecape")

    @classmethod
    def decape_note(cls) -> re.Pattern[str]:
        return cls.compile_stamp("decapeNote")

    @classmethod
    def decape_machine_side(cls) -> re.Pattern[str]:
        return cls.compile_stamp("decapeMachineSide")

    @classmethod
    def hint_number_tail(cls) -> re.Pattern[str]:
        return cls.compile_stamp("hintNumberTail")

    @classmethod
    def bom_revision_noise_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return cls.compile_stamp_list("bomRevisionNoise")

    @classmethod
    def bom_client_reference_noise_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return cls.compile_stamp_list("bomClientReferenceNoise")

    @classmethod
    def client_reference_code_patterns(cls) -> tuple[re.Pattern[str], ...]:
        cache_key = "stamp_list:clientReferenceCodeCapture"

        if cache_key not in _COMPILED_LISTS:
            patterns = ChatAssistantContentService.list(
                _STAMP_BUNDLE,
                "patternLists",
                "clientReferenceCodeCapture",
            )
            _COMPILED_LISTS[cache_key] = tuple(
                re.compile(str(item), _DEFAULT_FLAGS)
                for item in patterns
                if str(item).strip()
            )

        return _COMPILED_LISTS[cache_key]

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
    def unit_suffixes(cls) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(
            _VALIDATION_BUNDLE,
            "validationRules",
            "unitSuffixes",
        )
        return tuple(str(item).strip().lower() for item in items if str(item).strip())

    @classmethod
    def cable_length_units(cls) -> frozenset[str]:
        items = ChatAssistantContentService.list(
            _VALIDATION_BUNDLE,
            "validationRules",
            "cableLengthUnits",
        )
        return frozenset(str(item).strip().upper() for item in items if str(item).strip())

    @classmethod
    def piece_count_units(cls) -> frozenset[str]:
        items = ChatAssistantContentService.list(
            _VALIDATION_BUNDLE,
            "validationRules",
            "pieceCountUnits",
        )
        return frozenset(str(item).strip().upper() for item in items if str(item).strip())

    @classmethod
    def max_piece_count_quantity(cls) -> float:
        return cls.validation_rule_float("maxPieceCountQuantity", 10.0)

    @classmethod
    def intermediate_description_signature(cls, description: str) -> str | None:
        match = cls.intermediate_segment().search(str(description or ""))

        if not match:
            return None

        token = str(match.group(0) or "").split("/", 1)[0]
        normalized = token.replace(" ", "").upper()

        return normalized or None

    @classmethod
    def compile_stamp_anchor(cls, key: str) -> re.Pattern[str]:
        cache_key = f"stamp_anchor:{key}"

        if cache_key not in _COMPILED:
            raw = ChatAssistantContentService.get(_STAMP_BUNDLE, "patterns", key, default="")
            _COMPILED[cache_key] = re.compile(str(raw))

        return _COMPILED[cache_key]

    @classmethod
    def code_token(cls) -> re.Pattern[str]:
        return cls.compile_stamp("codeToken")

    @classmethod
    def ocr_spaced_code(cls) -> re.Pattern[str]:
        return cls.compile_stamp("ocrSpacedCode")

    @classmethod
    def stamp_revision(cls) -> re.Pattern[str]:
        return cls.compile_stamp("stampRevision")

    @classmethod
    def primary_drawing_code(cls) -> re.Pattern[str]:
        return cls.compile_stamp_anchor("primaryDrawingCode")

    @classmethod
    def labeled_product_code_capture(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _STAMP_BUNDLE,
                "patterns",
                "labeledProductCodeCapture",
                default="",
            )
        )

    @classmethod
    def filename_code(cls) -> re.Pattern[str]:
        return cls.compile_stamp("filenameCode")

    @classmethod
    def customer_code_labeled(cls) -> re.Pattern[str]:
        return cls.compile_stamp("customerCodeLabeled")

    @classmethod
    def customer_code_inline(cls) -> re.Pattern[str]:
        return cls.compile_stamp("customerCodeInline")

    @classmethod
    def customer_description_labeled(cls) -> re.Pattern[str]:
        return cls.compile_stamp("customerDescriptionLabeled")

    @classmethod
    def title_separator_strip(cls) -> re.Pattern[str]:
        return cls.compile_stamp("titleSeparatorStrip")

    @classmethod
    def code_family_prefix(cls, key: str, default: str = "") -> str:
        return str(
            ChatAssistantContentService.get(
                _STAMP_BUNDLE,
                "codeFamilies",
                key,
                default=default,
            )
        )

    @classmethod
    def code_family_prefixes(cls, key: str) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(_STAMP_BUNDLE, "codeFamilies", key)
        return tuple(str(item) for item in items if str(item))

    @classmethod
    def is_bom_component(cls, code: str | None) -> bool:
        normalized = str(code or "").strip()

        if not normalized:
            return False

        prefixes = cls.code_family_prefixes("bomComponentPrefixes")

        return any(normalized.startswith(prefix) for prefix in prefixes)

    @classmethod
    def is_finished_product(cls, code: str | None) -> bool:
        normalized = str(code or "").strip()
        prefix = cls.code_family_prefix("finishedProductPrefix", "90")

        return bool(normalized and normalized.startswith(prefix))

    @classmethod
    def is_primary_drawing_code(cls, code: str | None) -> bool:
        normalized = str(code or "").strip()

        return bool(normalized and cls.primary_drawing_code().match(normalized))

    @classmethod
    def candidate_confidence(cls, key: str, default: float) -> float:
        raw = ChatAssistantContentService.get(
            _STAMP_BUNDLE,
            "candidateConfidence",
            key,
            default=str(default),
        )

        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def high_confidence_threshold(cls) -> float:
        return cls.candidate_confidence("highConfidenceThreshold", 0.85)

    @classmethod
    def product_code_source_rank(cls, source: str | None) -> int:
        node = ChatAssistantContentService.get_node(
            _STAMP_BUNDLE,
            "productCodeResolution",
            "sourceRanking",
        ) or {}

        return int(node.get(str(source or "").strip(), 0))

    @classmethod
    def default_chicote_description(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _STAMP_BUNDLE,
                "defaults",
                "chicoteDescription",
                default="CHICOTE DE LIGACAO",
            )
        )
