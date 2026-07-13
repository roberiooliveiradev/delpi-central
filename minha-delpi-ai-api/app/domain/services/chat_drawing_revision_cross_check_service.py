"""Revisão no PDF (cliente) vs cadastro TOTVS — sem cruzamento crítico.

A revisão Delpi (B1_REVATU) não aparece no desenho; helpers de carimbo
permanecem para confiança de OCR/outros usos.
"""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_native_text_gate_service import (
    ChatDrawingNativeTextGateService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService


class ChatDrawingRevisionCrossCheckService:
    @classmethod
    def stamp_trusted(cls, pdf_extract: dict[str, Any] | None) -> bool:
        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}

        vision = pdf_meta.get("documentVision")

        if isinstance(vision, dict) and vision.get("hasTitleBlock"):
            return True

        stamp_text = cls._revision_stamp_text(pdf_meta)

        if not stamp_text.strip():
            return False

        if cls._bom_table_noise_in_stamp_text(stamp_text):
            return False

        min_hits = cls._rule_int(
            "minStampMarkerHits",
            ChatDrawingNativeTextGateService._min_marker_hits(),
        )

        return (
            ChatDrawingNativeTextGateService._stamp_marker_hits(stamp_text) >= min_hits
        )

    @classmethod
    def should_pending_instead_of_critical(
        cls,
        pdf_extract: dict[str, Any] | None,
    ) -> bool:
        if not cls._rule_bool("pendingWhenTitleBlockMissing", True):
            return False

        return not cls.stamp_trusted(pdf_extract)

    @classmethod
    def _rule_bool(cls, key: str, default: bool) -> bool:
        node = ChatDrawingPatternsService.validation_rule("revisionCrossCheck")

        if not isinstance(node, dict):
            return default

        value = node.get(key)

        if isinstance(value, bool):
            return value

        return default

    @classmethod
    def _rule_int(cls, key: str, default: int) -> int:
        node = ChatDrawingPatternsService.validation_rule("revisionCrossCheck")

        if not isinstance(node, dict):
            return default

        value = node.get(key)

        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def _revision_stamp_text(cls, pdf_meta: dict[str, Any]) -> str:
        parts: list[str] = []
        source_metadata = pdf_meta.get("sourceMetadata")

        if isinstance(source_metadata, dict):
            for key in ("stampText", "cadReferenceText"):
                text = str(source_metadata.get(key) or "").strip()

                if text:
                    parts.append(text)

        title_block = pdf_meta.get("titleBlock")

        if isinstance(title_block, dict):
            text = str(title_block.get("rawText") or "").strip()

            if text:
                parts.append(text)

        return "\n".join(parts)

    @classmethod
    def _bom_table_noise_in_stamp_text(cls, stamp_text: str) -> bool:
        min_pipes = cls._rule_int("bomTableNoiseMinPipes", 5)

        return str(stamp_text or "").count("|") >= min_pipes
