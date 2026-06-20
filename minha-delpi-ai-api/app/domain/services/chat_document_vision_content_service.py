"""Vocabulário e configuração da skill document-vision-delpi — bundle document_vision.json."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "document_vision"
_COMPILED_PATTERNS: list[re.Pattern[str]] | None = None
_COMPILED_DESCRIBE_PATTERNS: list[re.Pattern[str]] | None = None
_COMPILED_CONFIG_PATTERNS: dict[str, re.Pattern[str]] = {}


class ChatDocumentVisionContentService:
    @classmethod
    def min_message_length(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "intent",
            "minMessageLength",
            default="8",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 8

    @classmethod
    def read_content_patterns(cls) -> tuple[re.Pattern[str], ...]:
        global _COMPILED_PATTERNS

        if _COMPILED_PATTERNS is None:
            patterns = ChatAssistantContentService.list(
                _BUNDLE,
                "intent",
                "readContentPatterns",
            )
            _COMPILED_PATTERNS = [
                re.compile(str(item), re.IGNORECASE)
                for item in patterns
                if str(item).strip()
            ]

        return tuple(_COMPILED_PATTERNS)

    @classmethod
    def describe_image_patterns(cls) -> tuple[re.Pattern[str], ...]:
        global _COMPILED_DESCRIBE_PATTERNS

        if _COMPILED_DESCRIBE_PATTERNS is None:
            patterns = ChatAssistantContentService.list(
                _BUNDLE,
                "intent",
                "describeImagePatterns",
            )
            _COMPILED_DESCRIBE_PATTERNS = [
                re.compile(str(item), re.IGNORECASE)
                for item in patterns
                if str(item).strip()
            ]

        return tuple(_COMPILED_DESCRIBE_PATTERNS)

    @classmethod
    def vision_purpose(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "purposes",
            key,
            default=key,
        )

    @classmethod
    def vlm_prompt(cls, purpose: str, *, is_image: bool = False) -> str:
        normalized = str(purpose or "").strip().lower()

        if normalized == cls.vision_purpose("hybrid"):
            prompt_key = "hybrid"
        elif normalized == cls.vision_purpose("describe"):
            prompt_key = "describeImage" if is_image else "describeDocument"
        else:
            prompt_key = "ocr"

        return ChatAssistantContentService.get(
            _BUNDLE,
            "vlm",
            "prompts",
            prompt_key,
            default="",
        )

    @classmethod
    def context_label(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "context",
            key,
            default=key,
        )

    @classmethod
    def image_extensions(cls) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(_BUNDLE, "supported", "imageExtensions")
        return tuple(str(item).strip().lower() for item in items if str(item).strip())

    @classmethod
    def document_mime_prefixes(cls) -> tuple[str, ...]:
        items = ChatAssistantContentService.list(
            _BUNDLE,
            "supported",
            "documentMimePrefixes",
        )
        return tuple(str(item).strip().lower() for item in items if str(item).strip())

    @classmethod
    def activation_mode(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "activation",
            "modes",
            key,
            default=key,
        )

    @classmethod
    def activation_reason(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "activation",
            "reasons",
            key,
            default=key,
        )

    @classmethod
    def _compile_config_pattern(cls, *path: str) -> re.Pattern[str]:
        cache_key = f"config:{'/'.join(path)}"

        if cache_key not in _COMPILED_CONFIG_PATTERNS:
            raw = ChatAssistantContentService.get(_BUNDLE, *path, default="")
            _COMPILED_CONFIG_PATTERNS[cache_key] = re.compile(
                str(raw),
                re.IGNORECASE,
            )

        return _COMPILED_CONFIG_PATTERNS[cache_key]

    @classmethod
    def title_block_stamp_line_pattern(cls) -> re.Pattern[str]:
        return cls._compile_config_pattern("titleBlock", "stampLinePattern")

    @classmethod
    def title_block_min_line_length(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "titleBlock",
            "minLineLength",
            default="4",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 4

    @classmethod
    def title_block_max_stamp_lines(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "titleBlock",
            "maxStampLines",
            default="12",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 12

    @classmethod
    def table_pipe_row_pattern(cls) -> re.Pattern[str]:
        return cls._compile_config_pattern("tables", "pipeRow")

    @classmethod
    def table_pipe_separator_pattern(cls) -> re.Pattern[str]:
        return cls._compile_config_pattern("tables", "pipeSeparator")

    @classmethod
    def tables_max_tables(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "tables",
            "maxTables",
            default="3",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 3

    @classmethod
    def tables_max_rows(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "tables",
            "maxRows",
            default="40",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 40

    @classmethod
    def pdf_fusion_min_embedded_chars(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "fusion",
            "minEmbeddedChars",
            default="80",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 80

    @classmethod
    def pdf_annotation_row_cluster_tolerance_pt(cls) -> float:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "annotationTable",
            "rowClusterTolerancePt",
            default="6",
        )

        try:
            return max(1.0, float(raw))
        except (TypeError, ValueError):
            return 6.0

    @classmethod
    def pdf_region_ocr_min_chars(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "regionOcr",
            "minChars",
            default="120",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 120

    @classmethod
    def pdf_region_ocr_engines(cls) -> tuple[str, ...]:
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "pdfExtraction",
            "regionOcr",
            "engines",
        )

        if isinstance(node, list):
            engines = tuple(
                str(item).strip().lower()
                for item in node
                if str(item).strip()
            )

            if engines:
                return engines

        return ("tesseract",)

    @classmethod
    def pdf_bom_region_ocr_engines(cls) -> tuple[str, ...]:
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "pdfExtraction",
            "regionOcr",
            "bomFusion",
            "engines",
        )

        if isinstance(node, list):
            engines = tuple(
                str(item).strip().lower()
                for item in node
                if str(item).strip()
            )

            if engines:
                return engines

        return ("tesseract", "easyocr")

    @classmethod
    def pdf_bom_engine_weights(cls) -> dict[str, float]:
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "pdfExtraction",
            "regionOcr",
            "bomFusion",
            "engineWeights",
        )

        if not isinstance(node, dict):
            return {"tesseract": 1.0, "easyocr": 1.15}

        weights: dict[str, float] = {}

        for key, value in node.items():
            engine = str(key or "").strip().lower()

            if not engine:
                continue

            try:
                weights[engine] = float(value)
            except (TypeError, ValueError):
                continue

        return weights or {"tesseract": 1.0, "easyocr": 1.15}

    @classmethod
    def pdf_bom_fusion_max_digit_edits(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "regionOcr",
            "bomFusion",
            "maxDigitEdits",
            default="2",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 2

    @classmethod
    def pdf_layout_profile_allows_region_ocr(cls, layout_profile: str) -> bool:
        normalized = str(layout_profile or cls.LAYOUT_GENERIC).strip().lower() or cls.LAYOUT_GENERIC
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "layoutProfiles",
            normalized,
            "enableRegionOcr",
            default="false",
        )

        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    LAYOUT_GENERIC = "generic"

    @classmethod
    def table_structure_enabled(cls) -> bool:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "tableStructure",
            "enabled",
            default="true",
        )

        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    @classmethod
    def table_structure_max_rows(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "tableStructure",
            "maxRows",
            default="40",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 40

    @classmethod
    def table_structure_min_columns(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "tableStructure",
            "minColumns",
            default="3",
        )

        try:
            return max(2, int(raw))
        except (TypeError, ValueError):
            return 3

    @classmethod
    def table_structure_cell_max_attempts(cls) -> int:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "tableStructure",
            "cellRefinement",
            "maxAttempts",
            default="3",
        )

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 3

    @classmethod
    def table_structure_cell_dpi_multiplier(cls) -> float:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "tableStructure",
            "cellRefinement",
            "dpiMultiplier",
            default="2.0",
        )

        try:
            return max(1.0, float(raw))
        except (TypeError, ValueError):
            return 2.0

    @classmethod
    def table_structure_cell_padding(cls) -> float:
        raw = ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "tableStructure",
            "cellRefinement",
            "cellPadding",
            default="0.005",
        )

        try:
            return max(0.0, float(raw))
        except (TypeError, ValueError):
            return 0.005

    @classmethod
    def table_structure_cell_tesseract_config(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "pdfExtraction",
                "tableStructure",
                "cellRefinement",
                "tesseractConfig",
                default="--psm 7 -c tessedit_char_whitelist=0123456789.,",
            )
            or "--psm 7 -c tessedit_char_whitelist=0123456789.,"
        ).strip()

    @classmethod
    def _table_structure_row_parsing(cls, key: str, default: Any = None) -> Any:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "pdfExtraction",
            "tableStructure",
            "rowParsing",
            key,
            default=default,
        )

    @classmethod
    def table_structure_header_markers(cls) -> tuple[str, ...]:
        raw = cls._table_structure_row_parsing("headerMarkers", [])

        if not isinstance(raw, list):
            return tuple()

        resolved: list[str] = []

        for item in raw:
            token = str(item or "").strip().upper()

            if token and token not in resolved:
                resolved.append(token)

        return tuple(resolved)

    @classmethod
    def table_structure_header_scan_max_lines(cls) -> int:
        raw = cls._table_structure_row_parsing("headerScanMaxLines", 24)

        try:
            return max(4, int(raw))
        except (TypeError, ValueError):
            return 24

    @classmethod
    def table_structure_header_min_marker_hits(cls) -> int:
        raw = cls._table_structure_row_parsing("headerMinMarkerHits", 2)

        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 2

    @classmethod
    def table_structure_row_anchor_min_digits(cls) -> int:
        raw = cls._table_structure_row_parsing("rowAnchorMinDigits", 8)

        try:
            return max(4, int(raw))
        except (TypeError, ValueError):
            return 8

    @classmethod
    def table_structure_min_partial_row_columns(cls) -> int:
        raw = cls._table_structure_row_parsing("minPartialRowColumns", 2)

        try:
            return max(2, int(raw))
        except (TypeError, ValueError):
            return 2

    @classmethod
    def table_structure_noise_row_patterns(cls) -> tuple[re.Pattern[str], ...]:
        raw = cls._table_structure_row_parsing("noiseRowPatterns", [])

        if not isinstance(raw, list):
            return tuple()

        compiled: list[re.Pattern[str]] = []

        for item in raw:
            pattern = str(item or "").strip()

            if not pattern:
                continue

            try:
                compiled.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                continue

        return tuple(compiled)
