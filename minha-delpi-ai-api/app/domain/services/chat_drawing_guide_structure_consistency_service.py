"""Cruza roteiro (SG2010) × estrutura (SG1010) — produtos e níveis BOM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True)
class GuideStructureConsistencyResult:
    extra_in_guide: tuple[str, ...]
    missing_in_guide: tuple[str, ...]
    level_mismatches: tuple[tuple[str, int, int], ...]
    expected_codes: tuple[str, ...]
    guide_codes: tuple[str, ...]


class ChatDrawingGuideStructureConsistencyService:
    @classmethod
    def compare(
        cls,
        *,
        root: dict,
        product_code: str,
    ) -> GuideStructureConsistencyResult:
        expected = cls.collect_expected_guide_codes(root, product_code)
        guide_codes = cls.collect_guide_product_codes(root)
        extra = sorted(guide_codes - expected)
        missing = sorted(expected - guide_codes)
        level_mismatches = tuple(cls._collect_level_mismatches(root, product_code))

        return GuideStructureConsistencyResult(
            extra_in_guide=tuple(extra),
            missing_in_guide=tuple(missing),
            level_mismatches=level_mismatches,
            expected_codes=tuple(sorted(expected)),
            guide_codes=tuple(sorted(guide_codes)),
        )

    @classmethod
    def build_check_items(
        cls,
        *,
        root: dict,
        product_code: str,
    ) -> list[dict[str, Any]]:
        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        guide_items = guide.get("items") if isinstance(guide.get("items"), list) else []

        if not guide_items:
            return []

        comparison = cls.compare(root=root, product_code=product_code)
        items: list[dict[str, Any]] = []
        content = ChatDrawingValidationContentService
        delimiter = content.get("presentation", "codeListDelimiter", default=", ")

        if comparison.extra_in_guide:
            items.append(
                content.item_from_template(
                    "guide_structure_extra",
                    status="critical_error",
                    pdf_evidence=content.evidence("dash"),
                    api_evidence=delimiter.join(comparison.extra_in_guide[:8]),
                )
            )

        if comparison.missing_in_guide:
            items.append(
                content.item_from_template(
                    "guide_structure_missing",
                    status="critical_error",
                    pdf_evidence=content.evidence("dash"),
                    api_evidence=delimiter.join(comparison.missing_in_guide[:8]),
                )
            )

        for code, actual_level, expected_level in comparison.level_mismatches[:6]:
            items.append(
                content.item_from_template(
                    "guide_structure_level",
                    status="critical_error",
                    pdf_evidence=content.evidence_format(
                        "guideBomLevel",
                        level=str(actual_level),
                    ),
                    api_evidence=content.evidence_format(
                        "guideBomLevelExpected",
                        level=str(expected_level),
                    ),
                    item_values={"code": code},
                )
            )

        if (
            comparison.expected_codes
            and not comparison.extra_in_guide
            and not comparison.missing_in_guide
            and not comparison.level_mismatches
        ):
            items.append(
                content.item_from_template(
                    "guide_structure_ok",
                    status="ok",
                    pdf_evidence=content.evidence("dash"),
                    api_evidence=content.evidence_format(
                        "codeCount",
                        count=str(len(comparison.guide_codes)),
                    ),
                )
            )

        return items

    @classmethod
    def collect_expected_guide_codes(cls, root: dict, product_code: str) -> set[str]:
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)
        codes: set[str] = set()

        if root_code:
            codes.add(root_code)

        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("code") or "")
            )

            if not code or code == root_code:
                continue

            if cls._structure_item_requires_guide(item, code=code):
                codes.add(code)

        return codes

    @classmethod
    def collect_guide_product_codes(cls, root: dict) -> set[str]:
        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        codes: set[str] = set()

        for item in guide.get("items") or []:
            if not isinstance(item, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("product_code") or item.get("product") or "")
            )

            if code:
                codes.add(code)

        return codes

    @classmethod
    def _structure_item_requires_guide(cls, item: dict, *, code: str) -> bool:
        if ChatDrawingPatternsService.is_intermediate_family(code):
            return True

        item_type = str(item.get("type") or "").strip().upper()

        return item_type in {"PI", "PA"}

    @classmethod
    def _collect_level_mismatches(
        cls,
        root: dict,
        product_code: str,
    ) -> list[tuple[str, int, int]]:
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)
        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        mismatches: list[tuple[str, int, int]] = []

        for item in guide.get("items") or []:
            if not isinstance(item, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("product_code") or item.get("product") or "")
            )

            if not code:
                continue

            raw_level = item.get("bom_level")

            if raw_level is None:
                continue

            try:
                level = int(raw_level)
            except (TypeError, ValueError):
                continue

            expected_level = 0 if code == root_code else 1

            if level != expected_level:
                mismatches.append((code, level, expected_level))

        return mismatches
