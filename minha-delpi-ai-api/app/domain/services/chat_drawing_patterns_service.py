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
    def bom_stamp_layout_without_table_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return cls.compile_stamp_list("bomStampLayoutWithoutTable")

    @classmethod
    def bom_description_code_noise_patterns(cls) -> tuple[re.Pattern[str], ...]:
        return cls.compile_stamp_list("bomDescriptionCodeNoise")

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
    def compile_validation(cls, key: str) -> re.Pattern[str]:
        cache_key = f"validation:{key}"

        if cache_key not in _COMPILED:
            raw = ChatAssistantContentService.get(
                _VALIDATION_BUNDLE,
                "patterns",
                key,
                default="",
            )
            _COMPILED[cache_key] = re.compile(str(raw), _DEFAULT_FLAGS)

        return _COMPILED[cache_key]

    @classmethod
    def validation_rule_node(cls, *path: str) -> Any:
        node = ChatAssistantContentService.get_node(
            _VALIDATION_BUNDLE,
            "validationRules",
            *path,
        )
        return node if node is not None else {}

    @classmethod
    def validation_rule_str(cls, key: str, default: str = "") -> str:
        raw = cls.validation_rule(key, default)
        return str(raw or default)

    @classmethod
    def validation_rule_frozenset(cls, *path: str) -> frozenset[str]:
        items = ChatAssistantContentService.list(
            _VALIDATION_BUNDLE,
            "validationRules",
            *path,
        )
        return frozenset(str(item).strip().upper() for item in items if str(item).strip())

    @classmethod
    def structure_index_rule_int(cls, key: str, default: int) -> int:
        raw = cls.validation_rule_node("structureIndex", key)

        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def root_product_bom_level(cls) -> int:
        return cls.structure_index_rule_int("rootProductBomLevel", 0)

    @classmethod
    def default_bom_level_when_unknown(cls) -> int:
        return cls.structure_index_rule_int("defaultBomLevelWhenUnknown", 1)

    @classmethod
    def structure_root_depth(cls) -> int:
        return cls.structure_index_rule_int("structureRootDepth", 1)

    @classmethod
    def guide_product_types(cls) -> frozenset[str]:
        return cls.validation_rule_frozenset("structureIndex", "guideProductTypes")

    @classmethod
    def nested_bom_line_types(cls) -> frozenset[str]:
        return cls.validation_rule_frozenset("structureIndex", "nestedBomLineTypes")

    @classmethod
    def intermediate_color_ocr_markers(cls, color: str) -> tuple[str, ...]:
        normalized_color = str(color or "").strip().upper()
        markers_node = cls.validation_rule_node("intermediateColorOcrMarkers")

        if not isinstance(markers_node, dict):
            markers_node = {}

        raw_markers = markers_node.get(normalized_color)

        if not isinstance(raw_markers, list) or not raw_markers:
            fallback = cls.validation_rule_str(
                "intermediateColorFallbackMarker",
                "CB20{color}",
            )
            raw_markers = [fallback.format(color=normalized_color)]

        return tuple(
            str(marker).upper().replace(" ", "")
            for marker in raw_markers
            if str(marker).strip()
        )

    @classmethod
    def inspection_legacy_plan_keys(cls) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(
            _VALIDATION_BUNDLE,
            "validationRules",
            "inspectionContract",
            "legacyPlanKeys",
        )
        return tuple(str(item).strip() for item in items if str(item).strip())

    @classmethod
    def inspection_plan_list_keys(cls) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(
            _VALIDATION_BUNDLE,
            "validationRules",
            "inspectionContract",
            "planListKeys",
        )
        return tuple(str(item).strip() for item in items if str(item).strip())

    @classmethod
    def pdf_haystack_source_metadata_keys(cls) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(
            _VALIDATION_BUNDLE,
            "validationRules",
            "pdfHaystackSourceMetadataKeys",
        )
        return tuple(str(item).strip() for item in items if str(item).strip())

    @classmethod
    def pdf_haystack_bom_row_keys(cls) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(
            _VALIDATION_BUNDLE,
            "validationRules",
            "pdfHaystackBomRowKeys",
        )
        return tuple(str(item).strip() for item in items if str(item).strip())

    @classmethod
    def multipage_coverage_rule(cls, key: str, default: Any = None) -> Any:
        node = cls.validation_rule_node("multipageCoverage")
        return node.get(key, default) if isinstance(node, dict) else default

    @classmethod
    def multipage_min_page_count(cls) -> int:
        return cls.validation_rule_int_from_node(
            cls.multipage_coverage_rule("minPageCount", 2),
            2,
        )

    @classmethod
    def multipage_min_api_codes(cls) -> int:
        return cls.validation_rule_int_from_node(
            cls.multipage_coverage_rule("minApiCodesToEvaluate", 3),
            3,
        )

    @classmethod
    def multipage_warning_ratio_below(cls) -> float:
        return cls.validation_rule_float_from_node(
            cls.multipage_coverage_rule("warningRatioBelow", 0.7),
            0.7,
        )

    @classmethod
    def multipage_pending_ratio_below(cls) -> float:
        return cls.validation_rule_float_from_node(
            cls.multipage_coverage_rule("pendingRatioBelow", 0.4),
            0.4,
        )

    @classmethod
    def multipage_page_count_keys(cls) -> tuple[str, ...]:
        items = cls.multipage_coverage_rule("pageCountKeys", ["pageCount"])

        if isinstance(items, list):
            return tuple(str(item).strip() for item in items if str(item).strip())

        return ("pageCount",)

    @classmethod
    def multipage_status_warning(cls) -> str:
        return str(cls.multipage_coverage_rule("statusWarning", "error"))

    @classmethod
    def multipage_status_pending(cls) -> str:
        return str(cls.multipage_coverage_rule("statusPending", "pending"))

    @classmethod
    def multipage_template_low_coverage(cls) -> str:
        return str(
            cls.multipage_coverage_rule("templateLowCoverage", "multipage_low_coverage")
        )

    @classmethod
    def multipage_template_partial(cls) -> str:
        return str(
            cls.multipage_coverage_rule("templatePartial", "multipage_bom_partial")
        )

    @classmethod
    def validation_rule_int_from_node(cls, raw: Any, default: int) -> int:
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def validation_rule_float_from_node(cls, raw: Any, default: float) -> float:
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    @classmethod
    def dimension_note_type_node(cls, note_type: str) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(
            _STAMP_BUNDLE,
            "dimensionNoteTypes",
            note_type,
        )
        return node if isinstance(node, dict) else {}

    @classmethod
    def dimension_note_context_markers(cls, note_type: str) -> tuple[str, ...]:
        markers = cls.dimension_note_type_node(note_type).get("contextMarkers")

        if not isinstance(markers, list):
            return ()

        return tuple(
            str(marker).strip().upper()
            for marker in markers
            if str(marker).strip()
        )

    @classmethod
    def dimension_note_types_suppressing_decape(cls) -> tuple[str, ...]:
        types: list[str] = []
        node = ChatAssistantContentService.get_node(_STAMP_BUNDLE, "dimensionNoteTypes") or {}

        if not isinstance(node, dict):
            return ()

        for note_type, payload in node.items():
            if not isinstance(payload, dict):
                continue

            if payload.get("suppressesDecapeExtraction"):
                types.append(str(note_type))

        return tuple(types)

    @classmethod
    def dimension_note_validation_rule(cls, key: str, default: str = "") -> str:
        return str(
            cls.validation_rule_node("dimensionNoteValidation", key) or default
        )

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

        if not normalized:
            return False

        prefixes = cls.code_family_prefixes("finishedProductPrefixes")

        if prefixes:
            return any(normalized.startswith(prefix) for prefix in prefixes)

        prefix = cls.code_family_prefix("finishedProductPrefix", "90")

        return bool(normalized.startswith(prefix))

    @classmethod
    def is_assembly_pa(cls, code: str | None) -> bool:
        normalized = str(code or "").strip()
        prefixes = cls.code_family_prefixes("assemblyProductPrefixes")

        if prefixes:
            return any(normalized.startswith(prefix) for prefix in prefixes)

        prefix = cls.code_family_prefix("assemblyProductPrefix", "70")

        return bool(normalized and normalized.startswith(prefix))

    @classmethod
    def is_sample_pa(cls, code: str | None) -> bool:
        normalized = str(code or "").strip()
        prefixes = cls.code_family_prefixes("sampleProductPrefixes")

        return bool(
            normalized and prefixes and any(normalized.startswith(prefix) for prefix in prefixes)
        )

    @classmethod
    def is_chicote_leaf_pa(cls, code: str | None) -> bool:
        normalized = str(code or "").strip()

        if not normalized:
            return False

        chicote_prefix = cls.code_family_prefix("finishedProductPrefix", "90")

        return normalized.startswith(chicote_prefix) or cls.is_sample_pa(normalized)

    @classmethod
    def is_nested_chicote_in_assembly_bom(
        cls,
        code: str | None,
        assembly_code: str | None,
    ) -> bool:
        normalized = str(code or "").strip()
        assembly = str(assembly_code or "").strip()

        if not normalized or not assembly or not cls.is_assembly_pa(assembly):
            return False

        chicote_prefix = cls.code_family_prefix("nestedChicotePrefix", "90")

        return normalized.startswith(chicote_prefix)

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
