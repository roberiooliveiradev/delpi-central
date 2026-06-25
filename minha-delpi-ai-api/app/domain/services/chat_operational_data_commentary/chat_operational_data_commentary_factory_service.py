"""Delegate — comentário operacional."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)
from app.domain.services.chat_operational_commentary_profile_service import (
    ChatOperationalCommentaryProfileService,
)
from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.external_actions.operational_route_narrative_service import (
    ExternalActionOperationalRouteNarrativeService,
)

from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_constants import (
    CONTENT_SECTION as _CONTENT_SECTION,
    MP_LOW_COVERAGE_PA_THRESHOLD as _MP_LOW_COVERAGE_PA_THRESHOLD,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_facade_access import (
    commentary_service,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_support_service import (
    ChatOperationalDataCommentarySupportService,
)

_Narrative = ExternalActionOperationalRouteNarrativeService



class ChatOperationalDataCommentaryFactoryService:
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
                producible = round(available / required, 4)
                row["pa_coverage_estimate"] = producible
                row["pa_producible_from_stock"] = producible
            else:
                row["pa_coverage_estimate"] = None
                row["pa_producible_from_stock"] = None

            row["available_quantity_total"] = available
            rows.append(row)

        return rows

    @classmethod
    def _build_factory_commentary(cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any]:
        highlights = ChatOperationalDataCommentaryFactoryService._build_factory_highlights(root, format_quantity=format_quantity)
        attention = ChatOperationalDataCommentaryFactoryService._build_factory_attention(root)

        return {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
        }

    @classmethod
    def _build_factory_highlights(cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> list[str]:
        highlights: list[str] = []
        status = str(root.get("factory_status") or "").strip()
        profile = "factoryStatus"

        if status:
            highlights.append(ChatOperationalDataCommentarySupportService._text(profile, "headlineStatus", status=status))

        if "SEM ESTRUTURA" in status.upper():
            highlights.append(ChatOperationalDataCommentarySupportService._text(profile, "noStructure"))

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}
        without_stock = indicators.get("total_raw_materials_without_stock_for_one_pa")

        if without_stock not in (None, "", 0, "0"):
            highlights.append(
                ChatOperationalDataCommentarySupportService._text(
                    profile,
                    "exclusiveWithoutStock",
                    count=str(without_stock),
                )
            )

        production_summary = ChatOperationalDataCommentarySupportService._section_block(root, "production").get("summary")

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
                highlights.append(ChatOperationalDataCommentarySupportService._text(profile, "noProductionOrders"))
            elif not pa_started and not pi_started and total_orders > 0:
                highlights.append(ChatOperationalDataCommentarySupportService._text(profile, "productionNotStarted"))
            else:
                highlights.append(
                    ChatOperationalDataCommentarySupportService._text(
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

        shipping_summary = ChatOperationalDataCommentarySupportService._section_block(root, "shipping").get("summary")

        if isinstance(shipping_summary, dict):
            shipped = _OpsTable.parse_quantity(shipping_summary.get("total_shipped_quantity") or 0)

            if shipped > 0:
                highlights.append(
                    ChatOperationalDataCommentarySupportService._text(
                        profile,
                        "shippingWithMovement",
                        shipped=str(shipped),
                    )
                )
            else:
                highlights.append(ChatOperationalDataCommentarySupportService._text(profile, "shippingNoMovement"))

        stock_items = ChatOperationalDataCommentarySupportService._section_block(root, "raw_material_stock").get("items")
        mp_summary = commentary_service().aggregate_mp_stock_rows(stock_items)

        if mp_summary:
            exclusive_count = 0
            structure_items = ChatOperationalDataCommentarySupportService._section_block(root, "structure").get("items")

            if isinstance(structure_items, list):
                exclusive_count = sum(
                    1
                    for item in structure_items
                    if isinstance(item, dict)
                    and item.get("exclusive_raw_material") in (True, "SIM", "Sim")
                )

            if exclusive_count == 0:
                highlights.append(ChatOperationalDataCommentarySupportService._text(profile, "sharedMpWarning"))

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
                        ChatOperationalDataCommentarySupportService._text(
                            profile,
                            "mpLowCoverage",
                            code=code,
                            required=str(row.get("quantity_required_for_one_pa") or "—"),
                            unit=str(row.get("unit") or ""),
                            available=available_text,
                            paCount=f"{pa_count:.1f}".rstrip("0").rstrip("."),
                        )
                    )

        stock_summary = ChatOperationalDataCommentarySupportService._section_block(root, "raw_material_stock").get("summary")

        if isinstance(stock_summary, dict):
            max_pa = stock_summary.get("max_pa_producible_from_stock")
            limiting_code = str(stock_summary.get("limiting_raw_material_code") or "").strip()

            if max_pa not in (None, ""):
                try:
                    pa_count = int(float(max_pa))
                except (TypeError, ValueError):
                    pa_count = None

                if pa_count is not None and limiting_code:
                    if pa_count > 0:
                        highlights.append(
                            ChatOperationalDataCommentarySupportService._text(
                                profile,
                                "paProducibleCapacity",
                                count=str(pa_count),
                                code=limiting_code,
                            )
                        )
                    else:
                        highlights.append(
                            ChatOperationalDataCommentarySupportService._text(
                                profile,
                                "paProducibleCapacityZero",
                                code=limiting_code,
                            )
                        )

            without_stock_count = int(stock_summary.get("total_without_stock_for_one_pa") or 0)

            if without_stock_count > 0:
                highlights.append(
                    ChatOperationalDataCommentarySupportService._text(
                        profile,
                        "conclusionBlocked",
                        count=str(without_stock_count),
                    )
                )
            elif "LIBERADO" in status.upper():
                highlights.append(ChatOperationalDataCommentarySupportService._text(profile, "conclusionReleased"))

        return highlights

    @classmethod
    def _build_factory_attention(cls, root: dict[str, Any]) -> list[str]:
        attention: list[str] = []
        status = str(root.get("factory_status") or "").strip()
        profile = "factoryStatus"

        if "SEM ESTRUTURA" in status.upper():
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "attentionNoStructure"))

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}
        without_stock = indicators.get("total_raw_materials_without_stock_for_one_pa")

        if without_stock not in (None, "", 0, "0"):
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "attentionExclusiveStock"))

        if "NÃO INICIADO" in status.upper() or "NAO INICIADO" in status.upper():
            attention.append(ChatOperationalDataCommentarySupportService._text(profile, "attentionOpNotStarted"))

        return attention

