"""Cobertura BOM em PDF multipágina — razão PDF × SG1010 sem reprovar só por incompletude."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_bom_comparison_service import BomComparisonResult
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)


@dataclass(frozen=True)
class MultipageCoverageResult:
    applicable: bool
    page_count: int
    pdf_code_count: int
    api_code_count: int
    matched_code_count: int
    coverage_ratio: float | None
    status: str | None
    template_key: str | None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "applicable": self.applicable,
            "pageCount": self.page_count,
            "pdfCodeCount": self.pdf_code_count,
            "apiCodeCount": self.api_code_count,
            "matchedCodeCount": self.matched_code_count,
            "coverageRatio": self.coverage_ratio,
            "status": self.status,
            "templateKey": self.template_key,
        }


class ChatDrawingMultipageCoverageService:
    @classmethod
    def evaluate(
        cls,
        *,
        pdf_extract: dict,
        comparison: BomComparisonResult,
    ) -> MultipageCoverageResult:
        page_count = cls._resolve_page_count(pdf_extract)
        min_pages = ChatDrawingPatternsService.multipage_min_page_count()

        if page_count < min_pages:
            return cls._not_applicable(page_count=page_count, comparison=comparison)

        api_codes = set(comparison.api_codes)
        api_count = len(api_codes)

        if api_count < ChatDrawingPatternsService.multipage_min_api_codes():
            return cls._not_applicable(page_count=page_count, comparison=comparison)

        pdf_codes = set(comparison.pdf_bom_codes)
        matched = len(pdf_codes & api_codes)
        ratio = matched / api_count
        status, template_key = cls._resolve_status_and_template(ratio)

        return MultipageCoverageResult(
            applicable=True,
            page_count=page_count,
            pdf_code_count=len(pdf_codes),
            api_code_count=api_count,
            matched_code_count=matched,
            coverage_ratio=ratio,
            status=status,
            template_key=template_key,
        )

    @classmethod
    def build_check_items(
        cls,
        *,
        pdf_extract: dict,
        comparison: BomComparisonResult,
    ) -> list[dict[str, Any]]:
        result = cls.evaluate(pdf_extract=pdf_extract, comparison=comparison)

        if not result.applicable or not result.template_key or not result.status:
            return []

        content = ChatDrawingValidationContentService
        ratio_pct = (
            f"{result.coverage_ratio * 100:.0f}%"
            if result.coverage_ratio is not None
            else content.evidence("dash")
        )

        item = content.item_from_template(
            result.template_key,
            status=result.status,
            pdf_evidence=content.evidence_format(
                "multipageCoverageRatio",
                ratio=ratio_pct,
                pdfCount=str(result.pdf_code_count),
                apiCount=str(result.api_code_count),
                pageCount=str(result.page_count),
            ),
            api_evidence=content.evidence_format(
                "multipageMatchedCodes",
                matched=str(result.matched_code_count),
                apiCount=str(result.api_code_count),
            ),
        )
        item["multipageCoverage"] = result.to_metadata()

        return [item]

    @classmethod
    def resolve_metadata_from_items(
        cls,
        items: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        for item in items:
            if not isinstance(item, dict):
                continue

            metadata = item.get("multipageCoverage")

            if isinstance(metadata, dict) and metadata.get("applicable"):
                return metadata

        return None

    @classmethod
    def resolve_absence_check_status(
        cls,
        default_status: str,
        *,
        pdf_extract: dict,
        comparison: BomComparisonResult,
    ) -> str:
        if not ChatDrawingPatternsService.multipage_demote_absence_checks_when_partial():
            return default_status

        result = cls.evaluate(pdf_extract=pdf_extract, comparison=comparison)

        if result.applicable and result.template_key and result.status:
            return str(result.status)

        return default_status

    @classmethod
    def _not_applicable(
        cls,
        *,
        page_count: int,
        comparison: BomComparisonResult,
    ) -> MultipageCoverageResult:
        return MultipageCoverageResult(
            applicable=False,
            page_count=page_count,
            pdf_code_count=len(set(comparison.pdf_bom_codes)),
            api_code_count=len(set(comparison.api_codes)),
            matched_code_count=0,
            coverage_ratio=None,
            status=None,
            template_key=None,
        )

    @classmethod
    def _resolve_page_count(cls, pdf_extract: dict) -> int:
        for key in ChatDrawingPatternsService.multipage_page_count_keys():
            raw = pdf_extract.get(key)

            if raw is None:
                source_metadata = pdf_extract.get("sourceMetadata")

                if isinstance(source_metadata, dict):
                    raw = source_metadata.get(key)

            try:
                count = int(raw or 0)
            except (TypeError, ValueError):
                continue

            if count > 0:
                return count

        return 0

    @classmethod
    def _resolve_status_and_template(
        cls,
        ratio: float,
    ) -> tuple[str | None, str | None]:
        pending_below = ChatDrawingPatternsService.multipage_pending_ratio_below()
        warning_below = ChatDrawingPatternsService.multipage_warning_ratio_below()

        if ratio < pending_below:
            return (
                ChatDrawingPatternsService.multipage_status_pending(),
                ChatDrawingPatternsService.multipage_template_partial(),
            )

        if ratio < warning_below:
            return (
                ChatDrawingPatternsService.multipage_status_warning(),
                ChatDrawingPatternsService.multipage_template_low_coverage(),
            )

        return (None, None)
