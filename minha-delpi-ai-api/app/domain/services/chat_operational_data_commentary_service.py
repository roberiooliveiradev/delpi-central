"""Comentário e análise de dados operacionais — desacoplado de presenters e agentes."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
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

_Narrative = ExternalActionOperationalRouteNarrativeService
_CONTENT_SECTION = "compositeAnalysisInsights"
_MP_LOW_COVERAGE_PA_THRESHOLD = 3.0

_PROFILE_CONTENT_MAP = {
    "factory_status": "factoryStatus",
    "production_status": "productionStatus",
    "shipping_status": "shippingStatus",
    "stock": "stock",
    "directives": "directives",
    "structure_exclusivity": "structureExclusivity",
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
        presentation_key = ""

        if isinstance(stack_plan, dict):
            presentation_key = str(stack_plan.get("presentationProfileKey") or "").strip()

        entity_token = str(entity or "").strip()

        if not entity_token:
            api_meta = meta.get("apiDelpiResponseMeta")

            if isinstance(api_meta, dict):
                entity_token = str(api_meta.get("entity") or "").strip()

        if not presentation_key:
            presentation_key = ChatPresentationProfileService.resolve_profile_key(
                path,
                entity_token or None,
            )

        commentary_key = ChatPresentationProfileService.commentary_profile_key(
            presentation_key,
            path=path,
            entity=entity_token or None,
        )

        if commentary_key:
            return commentary_key

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
            "stock": cls._build_stock_commentary,
            "production_status": cls._build_production_commentary,
            "shipping_status": cls._build_shipping_commentary,
            "directives": cls._build_directives_commentary,
            "sale_pricing": cls._build_sale_pricing_commentary,
            "analyser": cls._build_analyser_commentary,
            "structure_exclusivity": cls._build_structure_exclusivity_commentary,
        }
        builder = builders.get(str(profile_key).strip())

        if not builder:
            return None

        commentary = builder(data, format_quantity=format_quantity)

        if not commentary:
            return None

        if not (commentary.get("highlights") or commentary.get("attention")):
            return None

        commentary["profileKey"] = profile_key
        commentary["narrativeInsight"] = cls._build_narrative_insight(commentary)

        return ChatHumanizedDataResponseService.normalize(commentary, profile_key=profile_key)

    @classmethod
    def render_markdown_sections(cls, commentary: dict[str, Any] | None) -> str:
        if not isinstance(commentary, dict):
            return ""

        parts: list[str] = []
        quick_layer = ChatHumanizedDataResponseService.render_quick_layer_markdown(commentary)

        if quick_layer:
            parts.append(quick_layer)

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
            shipped = _OpsTable.parse_quantity(shipping_summary.get("total_shipped_quantity") or 0)

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
                            cls._text(
                                profile,
                                "paProducibleCapacity",
                                count=str(pa_count),
                                code=limiting_code,
                            )
                        )
                    else:
                        highlights.append(
                            cls._text(
                                profile,
                                "paProducibleCapacityZero",
                                code=limiting_code,
                            )
                        )

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
    def _build_stock_commentary(
        cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any]:
        items = cls._resolve_stock_items(root)
        agg = cls._aggregate_stock(items, root)
        profile = "stock"
        highlights = cls._build_stock_highlights(agg, format_quantity=format_quantity)
        attention = cls._build_stock_attention(agg)

        commentary: dict[str, Any] = {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
        }

        if (
            agg.get("total_records") is not None
            and int(agg.get("positions") or 0) < int(agg.get("total_records") or 0)
        ):
            commentary["paginated"] = True

        return commentary

    @classmethod
    def _build_production_commentary(
        cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any]:
        _ = format_quantity
        profile = "productionStatus"
        reference_date = str(root.get("reference_date") or "").strip()
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        items = root.get("items") if isinstance(root.get("items"), list) else []
        highlights: list[str] = []
        attention: list[str] = []

        pa_started = _Narrative.format_production_flag(summary.get("pa_production_started"))
        pi_started = _Narrative.format_production_flag(summary.get("pi_production_started"))
        pa_started_flag = _Narrative.is_production_started(summary.get("pa_production_started"))
        pi_started_flag = _Narrative.is_production_started(summary.get("pi_production_started"))
        total_orders = int(summary.get("total_pa_orders") or 0) + int(
            summary.get("total_pi_orders") or 0
        )
        reported_pa = _OpsTable.parse_quantity(summary.get("total_pa_reported_quantity") or 0)
        reported_pi = _OpsTable.parse_quantity(summary.get("total_pi_reported_quantity") or 0)

        if reference_date and summary:
            highlights.append(
                cls._text(
                    profile,
                    "quickSummaryLine",
                    date=reference_date,
                    paStarted=pa_started,
                    piStarted=pi_started,
                    paQty=str(summary.get("total_pa_reported_quantity") or 0),
                )
            )
        elif reference_date:
            highlights.append(
                cls._text(profile, "scopeHeadline", date=reference_date)
            )

        appointment_count = sum(
            1
            for item in items
            if isinstance(item, dict) and int(item.get("total_reports") or 0) > 0
        )

        if appointment_count:
            highlights.append(
                cls._text(profile, "hasAppointments", count=str(appointment_count))
            )

        if total_orders > 0 and not pa_started_flag and not pi_started_flag:
            attention.append(cls._text(profile, "attentionStaleOp"))
        elif pi_started_flag and not pa_started_flag:
            attention.append(cls._text(profile, "piWithoutPa"))

        if total_orders > 0 and reported_pa + reported_pi <= 0:
            attention.append(cls._text(profile, "attentionLowReport"))

        commentary: dict[str, Any] = {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
            "periodScoped": bool(reference_date),
        }

        return commentary

    @classmethod
    def _build_shipping_commentary(
        cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any]:
        _ = format_quantity
        profile = "shippingStatus"
        date_start = str(root.get("date_start") or "").strip()
        date_end = str(root.get("date_end_exclusive") or "").strip()
        period = f"{date_start} → {date_end}".strip(" →")
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        highlights: list[str] = []
        attention: list[str] = []

        if period:
            highlights.append(cls._text(profile, "scopeHeadline", period=period))

        shipped = _OpsTable.parse_quantity(summary.get("total_shipped_quantity") or 0)
        loss = _OpsTable.parse_quantity(summary.get("total_inspection_loss_quantity") or 0)

        if shipped > 0:
            highlights.append(
                cls._text(profile, "hasShipped", quantity=str(int(shipped) if shipped.is_integer() else shipped))
            )

        if loss > 0 and shipped <= 0:
            highlights.append(cls._text(profile, "lossWithoutShip"))
            attention.append(cls._text(profile, "attentionLossOnly"))
        elif shipped <= 0 and loss <= 0:
            highlights.append(cls._text(profile, "noMovement"))

        if loss > 0 and shipped > 0 and loss >= shipped * 0.2:
            attention.append(cls._text(profile, "attentionHighLoss"))

        return {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
            "periodScoped": bool(period),
        }

    @classmethod
    def _build_directives_commentary(
        cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any]:
        _ = format_quantity
        profile = "directives"
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        raw_materials = root.get("raw_materials") if isinstance(root.get("raw_materials"), list) else []
        highlights: list[str] = []
        attention: list[str] = []

        if summary:
            highlights.append(
                cls._text(
                    profile,
                    "summaryLine",
                    raw_materials=str(summary.get("total_raw_materials") or len(raw_materials)),
                    suppliers=str(summary.get("total_supplier_links") or 0),
                    with_purchase=str(summary.get("raw_materials_with_last_purchase") or 0),
                    without_purchase=str(summary.get("raw_materials_without_last_purchase") or 0),
                )
            )

        without_purchase = int(summary.get("raw_materials_without_last_purchase") or 0)

        if without_purchase > 0:
            attention.append(
                cls._text(profile, "attentionWithoutPurchase", count=str(without_purchase))
            )

        if not highlights and not attention:
            return {}

        return {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
            "alertLevel": "attention" if attention else "ok",
        }

    @classmethod
    def _resolve_stock_items(cls, root: dict[str, Any]) -> list[dict[str, Any]]:
        if isinstance(root.get("items"), list):
            return [item for item in root["items"] if isinstance(item, dict)]

        data = root.get("data")

        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return [item for item in data["items"] if isinstance(item, dict)]

        return []

    @classmethod
    def _aggregate_stock(cls, items: list[dict[str, Any]], root: dict[str, Any]) -> dict[str, Any]:
        total_available = 0.0
        total_committed = 0.0
        has_available = False
        negative_positions = 0
        zero_available_positions = 0
        committed_over_current_positions = 0
        branch_available: dict[str, float] = {}

        for item in items:
            available_raw = item.get("available_quantity")
            current_raw = item.get("current_quantity")
            committed_raw = item.get("committed_quantity")
            available = (
                _OpsTable.parse_quantity(available_raw) if available_raw is not None else None
            )
            current = _OpsTable.parse_quantity(current_raw) if current_raw is not None else None
            committed = _OpsTable.parse_quantity(committed_raw or 0)
            branch = str(item.get("branch") or "").strip()

            if available is not None:
                has_available = True
                total_available += available

                if branch:
                    branch_available[branch] = branch_available.get(branch, 0.0) + available

                if available < 0:
                    negative_positions += 1

                if available == 0:
                    zero_available_positions += 1

            if current is not None and committed > current:
                committed_over_current_positions += 1

            total_committed += committed

        top_branch = ""
        top_branch_available = 0.0

        if branch_available:
            top_branch, top_branch_available = max(
                branch_available.items(),
                key=lambda pair: pair[1],
            )

        meta = root if isinstance(root, dict) else {}

        if isinstance(meta.get("data"), dict):
            meta = meta["data"]

        total_records = meta.get("total")

        return {
            "positions": len(items),
            "total_available": total_available,
            "total_committed": total_committed,
            "has_available": has_available,
            "negative_positions": negative_positions,
            "zero_available_positions": zero_available_positions,
            "committed_over_current_positions": committed_over_current_positions,
            "top_branch": top_branch,
            "top_branch_available": top_branch_available,
            "total_records": int(total_records) if total_records is not None else None,
        }

    @classmethod
    def _build_stock_highlights(
        cls,
        agg: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> list[str]:
        profile = "stock"
        highlights: list[str] = []

        def fmt(value: Any) -> str:
            if format_quantity:
                return format_quantity(value, "available_quantity")

            return str(value)

        if agg.get("has_available"):
            highlights.append(
                cls._text(
                    profile,
                    "headlineAvailable",
                    total=fmt(agg.get("total_available")),
                    positions=str(agg.get("positions") or 0),
                )
            )

        if float(agg.get("total_available") or 0) < 0:
            highlights.append(
                cls._text(
                    profile,
                    "negativeTotal",
                    total=fmt(agg.get("total_available")),
                )
            )

        top_branch = str(agg.get("top_branch") or "").strip()

        if top_branch and float(agg.get("top_branch_available") or 0) != 0:
            highlights.append(
                cls._text(
                    profile,
                    "topBranch",
                    branch=top_branch,
                    quantity=fmt(agg.get("top_branch_available")),
                )
            )

        if int(agg.get("zero_available_positions") or 0):
            highlights.append(
                cls._text(
                    profile,
                    "zeroPositions",
                    count=str(agg.get("zero_available_positions")),
                )
            )

        if int(agg.get("committed_over_current_positions") or 0):
            highlights.append(
                cls._text(
                    profile,
                    "committedOverCurrent",
                    count=str(agg.get("committed_over_current_positions")),
                )
            )

        return highlights

    @classmethod
    def _build_stock_attention(cls, agg: dict[str, Any]) -> list[str]:
        profile = "stock"
        attention: list[str] = []

        if float(agg.get("total_available") or 0) < 0 or int(agg.get("negative_positions") or 0):
            attention.append(cls._text(profile, "attentionNegative"))

        if int(agg.get("committed_over_current_positions") or 0):
            attention.append(cls._text(profile, "attentionCommitted"))

        if (
            float(agg.get("total_committed") or 0) > 0
            and agg.get("has_available")
            and float(agg.get("total_available") or 0) <= 0
        ):
            attention.append(cls._text(profile, "attentionFullyCommitted"))

        return attention

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
    def _build_sale_pricing_commentary(
        cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        _ = format_quantity

        from app.domain.services.chat_product_pricing_insight_service import (
            ChatProductPricingInsightService,
        )

        return ChatProductPricingInsightService.build_commentary(root)

    @classmethod
    def _build_structure_exclusivity_commentary(
        cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        _ = format_quantity

        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        items = root.get("items") if isinstance(root.get("items"), list) else []
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        code = str(product.get("product_code") or product.get("code") or "").strip()
        description = str(product.get("description") or "").strip()

        exclusive_count = int(summary.get("total_exclusive_raw_materials") or 0)
        mp_count = int(summary.get("total_raw_materials") or 0)
        highlights: list[str] = []

        if exclusive_count > 0:
            highlights.append(
                cls._presenter_format(
                    "structureExclusivity",
                    "exclusivityVerdictYes",
                    count=str(exclusive_count),
                )
            )
        elif items or mp_count > 0:
            highlights.append(
                cls._presenter_format(
                    "structureExclusivity",
                    "exclusivityVerdictNo",
                    count=str(mp_count),
                )
            )

        if description and code:
            intro_key = (
                "introWithDescription"
                if exclusive_count > 0
                else "introWithDescriptionNeutral"
            )
            highlights.append(
                cls._presenter_format(
                    "structureExclusivity",
                    intro_key,
                    code=code,
                    description=description,
                )
            )
        elif code:
            highlights.append(
                cls._presenter_format(
                    "structureExclusivity",
                    "introCodeOnly",
                    code=code,
                )
            )

        if summary:
            highlights.append(
                cls._presenter_format(
                    "structureExclusivity",
                    "componentsLine",
                    total=str(summary.get("total_components") or 0),
                    intermediates=str(summary.get("total_intermediates") or 0),
                    rawMaterials=str(mp_count),
                )
            )

        if not highlights:
            return None

        return {
            "profileKey": "structure_exclusivity",
            "highlights": highlights,
            "summaryLines": highlights[:4],
            "visualHints": ["tree", "table"],
        }

    @staticmethod
    def _presenter_format(section: str, key: str, **values: str) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        return ChatAssistantContentService.format(
            "presenter_content",
            "routePresentations",
            section,
            key,
            **values,
        )

    @classmethod
    def _build_analyser_commentary(
        cls,
        root: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        _ = format_quantity

        from app.domain.services.chat_product_analyser_divergence_service import (
            ChatProductAnalyserDivergenceService,
        )

        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        highlights: list[str] = []
        attention = ChatProductAnalyserDivergenceService.build_attention_points(root, product)
        opening = ChatProductAnalyserDivergenceService.build_opening_narrative(root, product)

        if opening:
            highlights.append(opening)

        if not highlights and not attention:
            return {}

        return {
            "highlights": highlights,
            "attention": attention,
            "summaryLines": highlights[:4],
            "alertLevel": "attention" if attention else "ok",
        }

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
