"""Sugestão de tags a partir de OCR/texto de evidência PAC (Onda 6.3)."""

from __future__ import annotations

from typing import Any

from app.domain.services.quality_action_plans.pac_evidence_tag_vocabulary_content_service import (
    PacEvidenceTagVocabularyContentService,
)


def _normalize_text(*parts: str | None) -> str:
    return " ".join(
        token.strip().lower()
        for part in parts
        if part and str(part).strip()
        for token in str(part).split()
    )


class PacEvidenceOcrTagSuggestionService:
    @classmethod
    def suggest(
        cls,
        *,
        ocr_text: str | None = None,
        file_name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        corpus = _normalize_text(ocr_text, file_name, description)
        max_tags = PacEvidenceTagVocabularyContentService.limit_int("maxSuggestedTags", 8)
        preview_chars = PacEvidenceTagVocabularyContentService.limit_int(
            "ocrTextPreviewChars",
            240,
        )

        symptom_tags = cls._match_marker_groups(
            corpus,
            PacEvidenceTagVocabularyContentService.marker_groups("symptomMarkers"),
            limit=max_tags,
        )
        failure_modes = cls._match_marker_groups(
            corpus,
            PacEvidenceTagVocabularyContentService.marker_groups("failureModeMarkers"),
            limit=max_tags,
        )
        product_codes = sorted(
            {
                match.group(0)
                for match in PacEvidenceTagVocabularyContentService.product_code_pattern().finditer(
                    corpus
                )
            }
        )

        ocr_preview = (ocr_text or "").strip()
        if len(ocr_preview) > preview_chars:
            ocr_preview = f"{ocr_preview[: preview_chars - 1]}…"

        return {
            "suggested_symptom_tags": symptom_tags,
            "suggested_failure_modes": failure_modes,
            "suggested_product_codes": product_codes,
            "ocr_text_preview": ocr_preview or None,
            "source_fields": {
                "has_ocr_text": bool((ocr_text or "").strip()),
                "has_file_name": bool((file_name or "").strip()),
                "has_description": bool((description or "").strip()),
            },
        }

    @staticmethod
    def _match_marker_groups(
        corpus: str,
        groups: list[dict[str, Any]],
        *,
        limit: int,
    ) -> list[str]:
        if not corpus:
            return []

        matched: list[str] = []
        for group in groups:
            tag = str(group.get("tag") or "").strip()
            if not tag:
                continue
            markers = [str(item).strip().lower() for item in (group.get("markers") or []) if item]
            if any(marker and marker in corpus for marker in markers):
                matched.append(tag)
            if len(matched) >= limit:
                break
        return matched
