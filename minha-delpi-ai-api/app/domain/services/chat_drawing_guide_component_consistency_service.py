"""Cruza component_code do SG2010 com filhos do PI na SG1010."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_structure_index_service import (
    ChatDrawingStructureIndexService,
)
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True)
class GuideComponentMismatch:
    product_code: str
    component_code: str


class ChatDrawingGuideComponentConsistencyService:
    @classmethod
    def compare(cls, *, root: dict, product_code: str) -> tuple[GuideComponentMismatch, ...]:
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)
        structure_codes = cls._collect_structure_codes(root, root_code)
        mismatches: list[GuideComponentMismatch] = []

        for row in cls._iter_guide_rows(root):
            guide_product = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("product_code") or row.get("product") or "")
            )
            component_code = ChatProductQueryIntentService.normalize_product_code(
                str(row.get("component_code") or "")
            )
            component_description = str(
                row.get("component_description") or row.get("description") or ""
            ).strip()

            if not guide_product or not component_code:
                continue

            if guide_product == root_code:
                if component_code in structure_codes:
                    continue

                if cls._matches_structure_intermediate_fingerprint(
                    root,
                    component_description=component_description,
                ):
                    continue

                mismatches.append(
                    GuideComponentMismatch(
                        product_code=guide_product,
                        component_code=component_code,
                    )
                )
                continue

            if not cls._is_component_under_product(root, guide_product, component_code):
                mismatches.append(
                    GuideComponentMismatch(
                        product_code=guide_product,
                        component_code=component_code,
                    )
                )

        return tuple(mismatches)

    @classmethod
    def build_check_items(cls, *, root: dict, product_code: str) -> list[dict[str, Any]]:
        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        guide_items = guide.get("items") if isinstance(guide.get("items"), list) else []

        if not guide_items:
            return []

        mismatches = cls.compare(root=root, product_code=product_code)
        content = ChatDrawingValidationContentService
        items: list[dict[str, Any]] = []

        for mismatch in mismatches[:8]:
            items.append(
                content.item_from_template(
                    "guide_component_mismatch",
                    status="critical_error",
                    pdf_evidence=content.evidence("dash"),
                    api_evidence=content.evidence_format(
                        "guideComponentPair",
                        product=mismatch.product_code,
                        component=mismatch.component_code,
                    ),
                )
            )

        if not mismatches and cls._has_component_rows(root):
            items.append(
                content.item_from_template(
                    "guide_component_ok",
                    status="ok",
                    pdf_evidence=content.evidence("dash"),
                    api_evidence=content.evidence("linked"),
                )
            )

        return items

    @classmethod
    def _collect_structure_codes(cls, root: dict, root_code: str) -> set[str]:
        return ChatDrawingStructureIndexService.collect_all_codes(root, root_code)

    @classmethod
    def _matches_structure_intermediate_fingerprint(
        cls,
        root: dict,
        *,
        component_description: str,
    ) -> bool:
        guide_fingerprint = cls._intermediate_fingerprint(component_description)

        if not guide_fingerprint:
            return False

        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

        for row in ChatDrawingStructureIndexService.flatten_items(structure):
            if not row.code or not ChatDrawingPatternsService.is_intermediate_family(
                row.code
            ):
                continue

            structure_fingerprint = cls._intermediate_fingerprint(row.description)

            if structure_fingerprint and structure_fingerprint == guide_fingerprint:
                return True

        return False

    @classmethod
    def _intermediate_fingerprint(cls, description: str) -> tuple[str, str, str] | None:
        match = ChatDrawingPatternsService.intermediate_segment().search(
            str(description or "")
        )

        if not match:
            return None

        color_match = re.search(r"([A-Z]{4})-\d", str(description or "").upper())
        color = color_match.group(1) if color_match else ""

        return (
            color,
            str(match.group(2) or "").strip().zfill(2),
            str(match.group(3) or "").strip().zfill(2),
        )

    @classmethod
    def _is_component_under_product(
        cls,
        root: dict,
        product_code: str,
        component_code: str,
    ) -> bool:
        normalized_product = ChatProductQueryIntentService.normalize_product_code(
            product_code
        )
        normalized_component = ChatProductQueryIntentService.normalize_product_code(
            component_code
        )
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

        for row in ChatDrawingStructureIndexService.flatten_items(structure):
            if row.code != normalized_component:
                continue

            if normalized_product in row.path:
                return True

        return False

    @classmethod
    def _has_component_rows(cls, root: dict) -> bool:
        return any(
            str(row.get("component_code") or "").strip()
            for row in cls._iter_guide_rows(root)
        )

    @classmethod
    def _iter_guide_rows(cls, root: dict) -> list[dict[str, Any]]:
        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        rows: list[dict[str, Any]] = []

        for item in guide.get("items") or []:
            if not isinstance(item, dict):
                continue

            if item.get("component_code") or item.get("product_code") or item.get("product"):
                rows.append(item)
                continue

            for operation in item.get("operations") or []:
                if not isinstance(operation, dict):
                    continue

                merged = {
                    **item,
                    **operation,
                    "product_code": item.get("product_code") or item.get("product"),
                }

                if merged.get("component_code"):
                    rows.append(merged)

        return rows
