"""Gate de plausibilidade do texto nativo PDF — Onda 14.7."""

from __future__ import annotations

import unicodedata

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

_BUNDLE = "drawing_stamp"


class ChatDrawingNativeTextGateService:
    @classmethod
    def is_native_text_plausible(
        cls,
        text: str | None,
        *,
        product_code: str | None = None,
        filename_code: str | None = None,
    ) -> bool:
        normalized = str(text or "").strip()

        if not normalized:
            return False

        code = ChatProductQueryIntentService.normalize_product_code(product_code or "")
        file_code = ChatProductQueryIntentService.normalize_product_code(filename_code or "")

        if not code and file_code and ChatDrawingPatternsService.is_primary_drawing_code(file_code):
            if not cls._has_labeled_delpi_code(normalized):
                return False

        if code and file_code and ChatDrawingPatternsService.is_bom_component(code):
            if ChatDrawingPatternsService.is_primary_drawing_code(file_code):
                return False

        if code and file_code and ChatDrawingPatternsService.is_primary_drawing_code(file_code):
            if code != file_code and ChatDrawingPatternsService.is_bom_component(code):
                return False

        if code and not ChatDrawingPatternsService.is_primary_drawing_code(code):
            if file_code and ChatDrawingPatternsService.is_primary_drawing_code(file_code):
                return False

            if not cls._stamp_marker_hits(normalized):
                return False

        marker_hits = cls._stamp_marker_hits(normalized)

        if marker_hits >= cls._min_marker_hits():
            return True

        if code and ChatDrawingPatternsService.is_primary_drawing_code(code):
            if file_code and code == file_code:
                return True

            return marker_hits >= 1

        return False

    @classmethod
    def _min_marker_hits(cls) -> int:
        gate = ChatAssistantContentService.get_node(_BUNDLE, "nativeTextGate") or {}

        return max(1, int(gate.get("minMarkerHits") or 2))

    @classmethod
    def _stamp_marker_hits(cls, text: str) -> int:
        folded = cls._fold_ascii(text)
        markers = ChatAssistantContentService.list(_BUNDLE, "nativeTextGate", "stampMarkers")
        hits = 0

        for marker in markers:
            token = cls._fold_ascii(marker)

            if token and token in folded:
                hits += 1

        return hits

    @classmethod
    def _has_labeled_delpi_code(cls, text: str) -> bool:
        folded = cls._fold_ascii(text)
        labels = ChatAssistantContentService.list(_BUNDLE, "stampFieldLabels", "productCode")

        for label in labels:
            token = cls._fold_ascii(label)

            if token and token in folded:
                return True

        return False

    @classmethod
    def _fold_ascii(cls, value: str) -> str:
        folded = unicodedata.normalize("NFKD", str(value or ""))

        return folded.encode("ascii", "ignore").decode("ascii").upper()
