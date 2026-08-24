"""Commentary transversal para payloads de estrutura (BOM / árvore)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_constants import (
    CONTENT_SECTION as _CONTENT_SECTION,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_support_service import (
    ChatOperationalDataCommentarySupportService,
)
from app.domain.services.chat_product_structure_presentation_service import (
    ChatProductStructurePresentationService,
    ProductStructureModel,
)

_PROFILE = "structure"


class ChatOperationalDataCommentaryStructureService:
    @classmethod
    def _build_structure_commentary(
        cls,
        root: dict[str, Any],
        *,
        format_quantity: Any = None,
    ) -> dict[str, Any] | None:
        payload = cls._unwrap_payload(root)
        stats = cls._aggregate_stats(payload)

        if stats is None:
            return None

        highlights = cls._build_highlights(stats)

        if not highlights:
            return None

        return {
            "profileKey": _PROFILE,
            "highlights": highlights,
            "summaryLines": highlights[:4],
            "visualHints": ["tree"],
        }

    @classmethod
    def _unwrap_payload(cls, root: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(root, dict):
            return {}

        data = root.get("data")

        if isinstance(data, dict):
            return data

        return root

    @classmethod
    def _aggregate_stats(cls, payload: dict[str, Any]) -> dict[str, Any] | None:
        model = ChatProductStructurePresentationService.parse_payload(payload)

        if model is not None:
            return cls._stats_from_model(model)

        flat_items = cls._flat_structure_items(payload)

        if flat_items:
            return cls._stats_from_flat_items(payload, flat_items)

        return None

    @classmethod
    def _stats_from_model(cls, model: ProductStructureModel) -> dict[str, Any]:
        pi_nodes = [
            node
            for node in model.level1
            if str(node.item_type or "").upper() == "PI"
        ]
        mp_by_parent: dict[str, list[str]] = defaultdict(list)

        for parent_code, mp_node in model.all_mp_nodes():
            mp_by_parent[mp_node.code].append(str(parent_code or "").strip())

        shared_mp_count = sum(
            1 for parents in mp_by_parent.values() if len({p for p in parents if p}) > 1
        )
        max_depth = 0

        if model.level1:
            max_depth = 1

        if model.unique_mp_codes():
            max_depth = 2

        return {
            "product_code": model.product_code,
            "product_description": str(model.root.description or "").strip(),
            "level1_count": len(model.level1),
            "pi_count": len(pi_nodes),
            "mp_count": len(model.unique_mp_codes()),
            "max_depth": max_depth,
            "shared_mp_count": shared_mp_count,
            "color_variant_pi_count": cls._count_color_variant_pis(pi_nodes),
        }

    @classmethod
    def _flat_structure_items(cls, payload: dict[str, Any]) -> list[dict[str, Any]]:
        items = payload.get("items")

        if not isinstance(items, list) or not items:
            return []

        first = items[0] if isinstance(items[0], dict) else {}

        if "component_type" in first or "level" in first:
            return [item for item in items if isinstance(item, dict)]

        return []

    @classmethod
    def _stats_from_flat_items(
        cls,
        payload: dict[str, Any],
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        product = payload.get("product") if isinstance(payload.get("product"), dict) else {}
        root = payload.get("root") if isinstance(payload.get("root"), dict) else {}
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}

        product_code = str(
            product.get("product_code")
            or root.get("code")
            or ""
        ).strip()
        product_description = str(
            product.get("description")
            or root.get("description")
            or ""
        ).strip()

        level1_count = int(summary.get("total_components") or 0)
        pi_count = int(summary.get("total_intermediates") or 0)
        mp_count = int(summary.get("total_raw_materials") or 0)
        max_depth = 0
        mp_parents: dict[str, set[str]] = defaultdict(set)
        pi_descriptions: list[str] = []

        for item in items:
            level = int(item.get("level") or 0)
            component_type = str(
                item.get("component_type") or item.get("type") or ""
            ).upper()
            code = str(
                item.get("component_code")
                or item.get("product_code")
                or item.get("code")
                or ""
            ).strip()
            parent_code = str(item.get("parent_code") or "").strip()
            description = str(
                item.get("component_description") or item.get("description") or ""
            ).strip()

            if level > max_depth:
                max_depth = level

            if component_type == "PI" and description:
                pi_descriptions.append(description)

            if component_type == "MP" and code:
                if parent_code:
                    mp_parents[code].add(parent_code)

        if not level1_count:
            level1_count = sum(1 for item in items if int(item.get("level") or 0) == 1)

        if not pi_count:
            pi_count = sum(
                1
                for item in items
                if str(item.get("component_type") or item.get("type") or "").upper() == "PI"
            )

        if not mp_count:
            mp_count = len(mp_parents) or sum(
                1
                for item in items
                if str(item.get("component_type") or item.get("type") or "").upper() == "MP"
            )

        shared_mp_count = sum(1 for parents in mp_parents.values() if len(parents) > 1)

        return {
            "product_code": product_code,
            "product_description": product_description,
            "level1_count": level1_count,
            "pi_count": pi_count,
            "mp_count": mp_count,
            "max_depth": max_depth,
            "shared_mp_count": shared_mp_count,
            "color_variant_pi_count": cls._count_color_variant_descriptions(pi_descriptions),
        }

    @classmethod
    def _count_color_variant_pis(cls, pi_nodes: list[Any]) -> int:
        descriptions = [str(node.description or "").strip() for node in pi_nodes]
        return cls._count_color_variant_descriptions(descriptions)

    @classmethod
    def _count_color_variant_descriptions(cls, descriptions: list[str]) -> int:
        markers = cls._color_description_markers()
        hits = 0

        for description in descriptions:
            upper = description.upper()

            if any(marker in upper for marker in markers):
                hits += 1

        return hits if hits >= 2 else 0

    @classmethod
    def _color_description_markers(cls) -> tuple[str, ...]:
        raw = ChatHumanizedDataResponseContentService.get_node(
            "commentaryProfiles",
            _PROFILE,
            "colorDescriptionMarkers",
        )

        if not isinstance(raw, list):
            return ()

        return tuple(str(item).strip().upper() for item in raw if str(item or "").strip())

    @classmethod
    def _build_highlights(cls, stats: dict[str, Any]) -> list[str]:
        highlights: list[str] = []
        code = str(stats.get("product_code") or "").strip()
        description = str(stats.get("product_description") or "").strip()

        if code:
            if description:
                highlights.append(
                    ChatOperationalDataCommentarySupportService._text(
                        _PROFILE,
                        "productLine",
                        code=code,
                        description=description,
                    )
                )
            else:
                highlights.append(
                    ChatOperationalDataCommentarySupportService._text(
                        _PROFILE,
                        "productCodeOnly",
                        code=code,
                    )
                )

        level1_count = int(stats.get("level1_count") or 0)

        if level1_count <= 0:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    _PROFILE,
                    "emptyStructure",
                    code=code or "—",
                )
            )
            return highlights

        highlights.append(
            ChatOperationalDataCommentarySupportService._text(
                _PROFILE,
                "level1Summary",
                count=str(level1_count),
            )
        )

        pi_count = int(stats.get("pi_count") or 0)
        mp_count = int(stats.get("mp_count") or 0)

        if pi_count or mp_count:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    _PROFILE,
                    "compositionLine",
                    piCount=str(pi_count),
                    mpCount=str(mp_count),
                )
            )

        max_depth = int(stats.get("max_depth") or 0)

        if max_depth > 1:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    _PROFILE,
                    "depthLine",
                    depth=str(max_depth),
                )
            )

        shared_mp_count = int(stats.get("shared_mp_count") or 0)

        if shared_mp_count > 0:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    _PROFILE,
                    "sharedMpLine",
                    count=str(shared_mp_count),
                )
            )

        color_variant_pi_count = int(stats.get("color_variant_pi_count") or 0)

        if color_variant_pi_count >= 2:
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    _PROFILE,
                    "colorVariantsLine",
                    count=str(color_variant_pi_count),
                )
            )

        return [line for line in highlights if str(line or "").strip()]
