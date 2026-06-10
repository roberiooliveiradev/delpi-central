"""Comentário e análise de dados operacionais — desacoplado de presenters e agentes."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)
from app.domain.services.external_actions.operational_route_narrative_service import (
    ExternalActionOperationalRouteNarrativeService,
)

_Narrative = ExternalActionOperationalRouteNarrativeService
_CONTENT_SECTION = "compositeAnalysisInsights"
_MP_LOW_COVERAGE_PA_THRESHOLD = 3.0

_ENTITY_PROFILE_MAP = {
    "product_factory_status": "factory_status",
}

_PROFILE_CONTENT_MAP = {
    "factory_status": "factoryStatus",
    "production_status": "productionStatus",
    "shipping_status": "shippingStatus",
    "stock": "stock",
}


class ChatOperationalDataCommentaryService:
    @classmethod
    def resolve_profile_key(
        cls,
        *,
        path: str = "",
        entity: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        meta = metadata if isinstance(metadata, dict) else {}
        stack_plan = meta.get("stackPresentationPlan")

        if isinstance(stack_plan, dict):
            profile_key = str(stack_plan.get("presentationProfileKey") or "").strip()

            if profile_key:
                return profile_key

        entity_token = str(entity or "").strip()

        if not entity_token:
            api_meta = meta.get("apiDelpiResponseMeta")

            if isinstance(api_meta, dict):
                entity_token = str(api_meta.get("entity") or "").strip()

        if entity_token in _ENTITY_PROFILE_MAP:
            return _ENTITY_PROFILE_MAP[entity_token]

        lowered = str(path or "").lower()

        if "/factory-status" in lowered:
            return "factory_status"

        if "/production-status" in lowered:
            return "production_status"

        if "/shipping-status" in lowered:
            return "shipping_status"

        if "/stock" in lowered:
            return "stock"

        return None

    @classmethod
    def build(
        cls,
        profile_key: str,
        data: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(data, dict) or not profile_key:
            return None

        builders = {
            "factory_status": cls._build_factory_commentary,
        }
        builder = builders.get(str(profile_key).strip())

        if not builder:
            return None

        commentary = builder(data, format_quantity=format_quantity)

        if not commentary:
            return None

        commentary["profileKey"] = profile_key
        commentary["narrativeInsight"] = cls._build_narrative_insight(commentary)

        return commentary

    @classmethod
    def render_markdown_sections(cls, commentary: dict[str, Any] | None) -> str:
        if not isinstance(commentary, dict):
            return ""

        parts: list[str] = []
        highlights = [
            str(line).strip()
            for line in (commentary.get("highlights") or [])
            if str(line or "").strip()
        ]
        attention = [
            str(line).strip()
            for line in (commentary.get("attention") or [])
            if str(line or "").strip()
        ]
        profile_key = cls._content_profile(str(commentary.get("profileKey") or "factory_status"))

        if highlights:
            parts.extend(
                [
                    "",
                    cls._text(profile_key, "highlightsHeader"),
                    "",
                    *[f"- {line}" for line in highlights],
                ]
            )

        if attention:
            parts.extend(
                [
                    "",
                    cls._text(profile_key, "attentionHeader"),
                    "",
                    *[f"{index}. {line}" for index, line in enumerate(attention, start=1)],
                ]
            )

        return _OpsTable.join_markdown_blocks(parts)

    @classmethod
    def aggregate_mp_stock_rows(cls, stock_items: object) -> list[dict[str, Any]]:
        if not isinstance(stock_items, list):
            return []

        grouped: dict[str, dict[str, Any]] = {}

        for item in stock_items:
            if not isinstance(item, dict):
                continue

            code = str(item.get("raw_material_code") or "").strip()

            if not code:
                continue

            bucket = grouped.setdefault(
                code,
                {
                    "raw_material_code": code,
                    "raw_material_description": str(
                        item.get("raw_material_description") or ""
                    ).strip(),
                    "unit": str(item.get("unit") or "").strip(),
                    "quantity_required_for_one_pa": item.get("quantity_required_for_one_pa"),
                    "available_quantity_total": 0.0,
                    "has_stock_for_one_pa_label": item.get("has_stock_for_one_pa_label"),
                },
            )
            bucket["available_quantity_total"] += _OpsTable.parse_quantity(
                item.get("available_quantity")
            )

            if item.get("has_stock_for_one_pa_label"):
                bucket["has_stock_for_one_pa_label"] = item.get("has_stock_for_one_pa_label")

        rows: list[dict[str, Any]] = []

        for code in sorted(grouped):
            row = grouped[code]
            required = _OpsTable.parse_quantity(row.get("quantity_required_for_one_pa"))
            available = float(row.get("available_quantity_total") or 0)

            if required > 0:
                row["pa_coverage_estimate"] = round(available / required, 2)
            else:
                row["pa_coverage_estimate"] = None

            row["available_quantity_total"] = available
            rows.append(row)

        return rows

    @classmethod
    def _build_factory_commentary(
        cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any]:
        highlights = cls._build_factory_highlights(root, format_quantity=format_quantity)
        attention = cls._build_factory_attention(root)

        return {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
        }

    @classmethod
    def _build_factory_highlights(
        cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> list[str]:
        highlights: list[str] = []
        status = str(root.get("factory_status") or "").strip()
        profile = "factoryStatus"

        if status:
            highlights.append(cls._text(profile, "headlineStatus", status=status))

        if "SEM ESTRUTURA" in status.upper():
            highlights.append(cls._text(profile, "noStructure"))

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}
        without_stock = indicators.get("total_raw_materials_without_stock_for_one_pa")

        if without_stock not in (None, "", 0, "0"):
            highlights.append(
                cls._text(
                    profile,
                    "exclusiveWithoutStock",
                    count=str(without_stock),
                )
            )

        production_summary = cls._section_block(root, "production").get("summary")

        if isinstance(production_summary, dict):
            total_orders = int(production_summary.get("total_pa_orders") or 0) + int(
                production_summary.get("total_pi_orders") or 0
            )
            pa_started = _Narrative.is_production_started(
                production_summary.get("pa_production_started")
            )
            pi_started = _Narrative.is_production_started(
                production_summary.get("pi_production_started")
            )

            if total_orders == 0 and "SEM ESTRUTURA" not in status.upper():
                highlights.append(cls._text(profile, "noProductionOrders"))
            elif not pa_started and not pi_started and total_orders > 0:
                highlights.append(cls._text(profile, "productionNotStarted"))
            else:
                highlights.append(
                    cls._text(
                        profile,
                        "productionStarted",
                        pa=_Narrative.format_production_flag(
                            production_summary.get("pa_production_started")
                        ),
                        pi=_Narrative.format_production_flag(
                            production_summary.get("pi_production_started")
                        ),
                    )
                )

        shipping_summary = cls._section_block(root, "shipping").get("summary")

        if isinstance(shipping_summary, dict):
            shipped = float(shipping_summary.get("total_shipped_quantity") or 0)

            if shipped > 0:
                highlights.append(
                    cls._text(
                        profile,
                        "shippingWithMovement",
                        shipped=str(shipped),
                    )
                )
            else:
                highlights.append(cls._text(profile, "shippingNoMovement"))

        stock_items = cls._section_block(root, "raw_material_stock").get("items")
        mp_summary = cls.aggregate_mp_stock_rows(stock_items)

        if mp_summary:
            exclusive_count = 0
            structure_items = cls._section_block(root, "structure").get("items")

            if isinstance(structure_items, list):
                exclusive_count = sum(
                    1
                    for item in structure_items
                    if isinstance(item, dict)
                    and item.get("exclusive_raw_material") in (True, "SIM", "Sim")
                )

            if exclusive_count == 0:
                highlights.append(cls._text(profile, "sharedMpWarning"))

            for row in mp_summary:
                coverage = row.get("pa_coverage_estimate")

                if coverage is None:
                    continue

                try:
                    pa_count = float(coverage)
                except (TypeError, ValueError):
                    continue

                code = str(row.get("raw_material_code") or "").strip()

                if not code:
                    continue

                if pa_count <= _MP_LOW_COVERAGE_PA_THRESHOLD:
                    available = row.get("available_quantity_total")

                    if format_quantity:
                        available_text = format_quantity(available, "available_quantity")
                    else:
                        available_text = str(available)

                    highlights.append(
                        cls._text(
                            profile,
                            "mpLowCoverage",
                            code=code,
                            required=str(row.get("quantity_required_for_one_pa") or "—"),
                            unit=str(row.get("unit") or ""),
                            available=available_text,
                            paCount=f"{pa_count:.1f}".rstrip("0").rstrip("."),
                        )
                    )

        stock_summary = cls._section_block(root, "raw_material_stock").get("summary")

        if isinstance(stock_summary, dict):
            without_stock_count = int(stock_summary.get("total_without_stock_for_one_pa") or 0)

            if without_stock_count > 0:
                highlights.append(
                    cls._text(
                        profile,
                        "conclusionBlocked",
                        count=str(without_stock_count),
                    )
                )
            elif "LIBERADO" in status.upper():
                highlights.append(cls._text(profile, "conclusionReleased"))

        return highlights

    @classmethod
    def _build_factory_attention(cls, root: dict[str, Any]) -> list[str]:
        attention: list[str] = []
        status = str(root.get("factory_status") or "").strip()
        profile = "factoryStatus"

        if "SEM ESTRUTURA" in status.upper():
            attention.append(cls._text(profile, "attentionNoStructure"))

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}
        without_stock = indicators.get("total_raw_materials_without_stock_for_one_pa")

        if without_stock not in (None, "", 0, "0"):
            attention.append(cls._text(profile, "attentionExclusiveStock"))

        if "NÃO INICIADO" in status.upper() or "NAO INICIADO" in status.upper():
            attention.append(cls._text(profile, "attentionOpNotStarted"))

        return attention

    @classmethod
    def _build_narrative_insight(cls, commentary: dict[str, Any]) -> str:
        highlights = [
            str(line).strip()
            for line in (commentary.get("highlights") or [])
            if str(line or "").strip()
        ]
        attention = [
            str(line).strip()
            for line in (commentary.get("attention") or [])
            if str(line or "").strip()
        ]

        if not highlights and not attention:
            return ""

        lead = highlights[0] if highlights else attention[0]
        extras = highlights[1:3] if len(highlights) > 1 else []

        if attention and not extras:
            extras = attention[:2]

        body = " ".join(extras)

        if body:
            return f"{lead} {body}".strip()

        return lead

    @classmethod
    def _section_block(cls, root: dict[str, Any], key: str) -> dict[str, Any]:
        block = root.get(key)

        if isinstance(block, dict):
            return block

        return {}

    @classmethod
    def _content_profile(cls, profile_key: str) -> str:
        return _PROFILE_CONTENT_MAP.get(str(profile_key or "").strip(), profile_key)

    @classmethod
    def _text(cls, profile: str, key: str, **values: str) -> str:
        if values:
            return ChatAssistantContentService.format(
                "presenter_content",
                _CONTENT_SECTION,
                profile,
                key,
                **values,
            )

        return ChatAssistantContentService.get(
            "presenter_content",
            _CONTENT_SECTION,
            profile,
            key,
            default="",
        )
