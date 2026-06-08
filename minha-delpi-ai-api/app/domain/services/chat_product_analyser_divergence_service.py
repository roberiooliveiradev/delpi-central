"""Cruza roteiro, inspeção e estrutura do analyser — pontos de atenção confiáveis."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)

_BUNDLE = "analyser_insights"


class ChatProductAnalyserDivergenceService:
    @classmethod
    def _txt(cls, *path: str, default: str = "", **values: str) -> str:
        if values:
            return ChatAssistantContentService.format(
                _BUNDLE, *path, default=default, **values
            )

        return ChatAssistantContentService.get(_BUNDLE, *path, default=default)

    @classmethod
    def build_attention_points(cls, root: dict | None, product: dict | None) -> list[str]:
        if not isinstance(root, dict):
            return []

        product = product if isinstance(product, dict) else {}
        points: list[str] = []

        guide_points = cls._guide_attention(root)
        inspection_points = cls._inspection_attention(root)
        cross_points = cls._cross_collection_attention(root)
        cadastral_points = cls._cadastral_attention(product)

        for block in (guide_points, inspection_points, cross_points, cadastral_points):
            for item in block:
                token = str(item or "").strip()

                if token and token not in points:
                    points.append(token)

        return points

    @classmethod
    def build_opening_narrative(cls, root: dict | None, product: dict | None) -> str | None:
        if not isinstance(root, dict) or not isinstance(product, dict):
            return None

        code = str(product.get("code") or "").strip()
        description = str(product.get("description") or "").strip()
        product_type = str(product.get("type") or "").strip()
        group_code = str(product.get("group_code") or "").strip()

        if not code:
            return None

        line = cls._txt("opening", "productLine", code=code)

        if description:
            line += cls._txt("opening", "descriptionSuffix", description=description)

        parts = [line]
        meta_bits: list[str] = []

        if product_type:
            meta_bits.append(cls._txt("opening", "metaType", type=product_type))

        if group_code:
            meta_bits.append(cls._txt("opening", "metaGroup", group_code=group_code))

        if meta_bits:
            parts.append(
                cls._txt(
                    "opening",
                    "metaWrapper",
                    meta=cls._txt("opening", "metaSeparator").join(meta_bits),
                )
            )

        composition = cls._structure_component_labels(root)

        if composition:
            ellipsis = (
                cls._txt("opening", "structureEllipsis")
                if len(composition) > 8
                else ""
            )
            parts.append(
                cls._txt(
                    "opening",
                    "structureIntro",
                    composition=", ".join(composition[:8]),
                    ellipsis=ellipsis,
                )
            )

        guide_total = cls._collection_total(root.get("guide"))
        inspection_total = cls._collection_total(root.get("inspection"))
        structure_total = cls._collection_total(root.get("structure"))

        availability: list[str] = []

        if guide_total and int(guide_total) > 0:
            availability.append(
                cls._txt(
                    "opening",
                    "availabilityWithGuide",
                    total=str(guide_total),
                )
            )
        else:
            availability.append(cls._txt("opening", "availabilityNoGuide"))

        if inspection_total and int(inspection_total) > 0:
            availability.append(
                cls._txt(
                    "opening",
                    "availabilityWithInspection",
                    total=str(inspection_total),
                )
            )
        else:
            availability.append(cls._txt("opening", "availabilityNoInspection"))

        if structure_total and int(structure_total) > 0:
            availability.append(
                cls._txt(
                    "opening",
                    "availabilityWithStructure",
                    total=str(structure_total),
                )
            )
        else:
            availability.append(cls._txt("opening", "availabilityEmptyStructure"))

        parts.append(
            cls._txt(
                "opening",
                "sourcesFooter",
                availability="; ".join(availability),
            )
        )

        return " ".join(parts)

    @classmethod
    def _guide_attention(cls, root: dict) -> list[str]:
        guide = root.get("guide")

        if not isinstance(guide, dict):
            return []

        items = [item for item in (guide.get("items") or []) if isinstance(item, dict)]
        total = cls._collection_total(guide)

        if total == 0 or not items:
            return [cls._txt("attention", "guideMissing")]

        without_operations = [
            str(item.get("product_code") or item.get("product") or "?").strip()
            for item in items
            if not cls._guide_item_has_operations(item)
        ]

        if without_operations and len(without_operations) == len(items):
            return [cls._txt("attention", "guideNoOperations")]

        return []

    @classmethod
    def _inspection_attention(cls, root: dict) -> list[str]:
        inspection = root.get("inspection")

        if not isinstance(inspection, dict):
            return [cls._txt("attention", "inspectionNotRegistered")]

        items = [item for item in (inspection.get("items") or []) if isinstance(item, dict)]
        total = cls._collection_total(inspection)

        if total == 0 or not items:
            return [cls._txt("attention", "inspectionNotRegistered")]

        empty_qp: list[str] = []
        missing_blocks: list[str] = []

        for item in items:
            code = str(
                item.get("product")
                or item.get("product_code")
                or "?"
            ).strip()

            if not cls._has_qp_blocks(item):
                missing_blocks.append(code)
                continue

            if cls._qp_blocks_empty(item):
                empty_qp.append(code)

        points: list[str] = []

        if empty_qp:
            sample = ", ".join(empty_qp[:5])
            suffix = (
                cls._txt("suffix", "andMoreCodes", count=str(len(empty_qp) - 5))
                if len(empty_qp) > 5
                else ""
            )
            points.append(
                cls._txt(
                    "attention",
                    "inspectionEmptyQp",
                    sample=sample,
                    suffix=suffix,
                )
            )

        if missing_blocks:
            sample = ", ".join(missing_blocks[:5])
            points.append(
                cls._txt("attention", "inspectionMissingQp", sample=sample)
            )

        return points

    @classmethod
    def _cross_collection_attention(cls, root: dict) -> list[str]:
        structure_codes = cls._structure_component_codes(root)
        inspection_codes = cls._inspection_product_codes(root)
        points: list[str] = []

        only_inspection = sorted(inspection_codes - structure_codes)
        only_structure = sorted(structure_codes - inspection_codes)

        for code in only_inspection[:6]:
            points.append(
                cls._txt("attention", "crossOnlyInspection", code=code)
            )

        if len(only_inspection) > 6:
            points.append(
                cls._txt(
                    "attention",
                    "crossOnlyInspectionMore",
                    count=str(len(only_inspection) - 6),
                )
            )

        if only_structure and inspection_codes:
            sample = ", ".join(only_structure[:4])
            points.append(
                cls._txt("attention", "crossOnlyStructure", sample=sample)
            )

        return points

    @classmethod
    def _cadastral_attention(cls, product: dict) -> list[str]:
        points: list[str] = []
        blocked = str(product.get("blocked") or "").strip()

        if blocked and blocked not in {"N", "0", ""}:
            points.append(
                cls._txt("attention", "cadastralBlocked", blocked=blocked)
            )

        if product.get("last_purchase_price") in (0, 0.0, None) and not str(
            product.get("last_purchase_date") or ""
        ).strip():
            points.append(cls._txt("attention", "cadastralNoPurchase"))

        drawing = str(product.get("drawing_code") or "").strip()
        customer_ref = str(product.get("customer_reference") or "").strip()

        if drawing and customer_ref and drawing != customer_ref:
            points.append(
                cls._txt(
                    "attention",
                    "cadastralRefMismatch",
                    drawing=drawing,
                    customer_ref=customer_ref,
                )
            )

        return points

    @classmethod
    def _structure_component_codes(cls, root: dict) -> set[str]:
        structure = root.get("structure")

        if not isinstance(structure, dict):
            return set()

        codes: set[str] = set()

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            for component in item.get("components") or []:
                if not isinstance(component, dict):
                    continue

                code = str(component.get("code") or "").strip()

                if code:
                    codes.add(code)

            code = str(item.get("code") or "").strip()

            if code and not item.get("components"):
                codes.add(code)

        return codes

    @classmethod
    def _inspection_product_codes(cls, root: dict) -> set[str]:
        inspection = root.get("inspection")

        if not isinstance(inspection, dict):
            return set()

        codes: set[str] = set()

        for item in inspection.get("items") or []:
            if not isinstance(item, dict):
                continue

            code = str(
                item.get("product")
                or item.get("product_code")
                or ""
            ).strip()

            if code:
                codes.add(code)

        return codes

    @classmethod
    def _structure_component_labels(cls, root: dict) -> list[str]:
        structure = root.get("structure")

        if not isinstance(structure, dict):
            return []

        labels: list[str] = []

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            for component in item.get("components") or []:
                if not isinstance(component, dict):
                    continue

                desc = str(component.get("description") or "").strip()
                code = str(component.get("code") or "").strip()
                comp_type = str(component.get("type") or "").strip()

                if desc:
                    label = desc

                    if code:
                        label = f"{desc} ({code})"

                    if comp_type:
                        label = f"{label} [{comp_type}]"

                    labels.append(label)

        return labels

    @classmethod
    def _collection_total(cls, value: Any) -> int | None:
        if isinstance(value, dict):
            total = value.get("total")

            if total is not None:
                try:
                    return int(total)
                except (TypeError, ValueError):
                    return None

        return None

    @classmethod
    def _guide_item_has_operations(cls, item: dict) -> bool:
        operations = item.get("operations")

        if isinstance(operations, list) and operations:
            return True

        return bool(str(item.get("operation_description") or "").strip())

    @classmethod
    def _has_qp_blocks(cls, item: dict) -> bool:
        return any(key in item for key in ("QP6", "QP7", "QP8", "qp6", "qp7", "qp8"))

    @classmethod
    def _qp_blocks_empty(cls, item: dict) -> bool:
        if not cls._has_qp_blocks(item):
            return True

        for key in ("QP6", "QP7", "QP8", "qp6", "qp7", "qp8"):
            value = item.get(key)

            if isinstance(value, list) and value:
                return False

        return True
