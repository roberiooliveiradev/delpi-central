"""Apresentação humanizada para respostas composite_analysis (factory-status e similares)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)
from app.domain.services.external_actions.operational_route_narrative_service import (
    ExternalActionOperationalRouteNarrativeService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

_Narrative = ExternalActionOperationalRouteNarrativeService


class ExternalActionProductCompositeAnalysisPresenter:
    """Perfil configurável via `presenter_content.json` — reutilizável por outras APIs."""

    _FACTORY_ENTITY = "product_factory_status"
    _MP_LOW_COVERAGE_PA_THRESHOLD = 3.0

    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _insight(self, profile: str, key: str, **values: str) -> str:
        return self._host._presenter_text("compositeAnalysisInsights", profile, key, **values)

    def _route(self, route: str, key: str, **values: str) -> str:
        return self._host._route_presentation(route, key, **values)

    def _product_context(self, root: dict, path: str) -> tuple[str, str]:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        code = str(
            product.get("product_code")
            or product.get("code")
            or self._host._extract_product_code_from_path(path)
            or ""
        ).strip()
        description = str(product.get("description") or "").strip()

        return code, description

    def _section_block(self, root: dict, key: str) -> dict[str, Any]:
        block = root.get(key)

        if isinstance(block, dict):
            return block

        return {}

    def _present_factory_status(self, root: dict, path: str) -> dict:
        code, description = self._product_context(root, path)
        linhas = self._build_factory_narrative_lines(root, code=code, description=description)
        markdown_body = self._build_factory_markdown_body(root, code=code, description=description)

        return {
            "titulo": (
                self._route("factoryStatus", "titleWithCode", code=code)
                if code
                else self._route("factoryStatus", "titleGeneric")
            ),
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
            "humanizedMarkdown": markdown_body,
        }

    def _build_factory_narrative_lines(
        self,
        root: dict,
        *,
        code: str,
        description: str,
        compact_for_rich_ui: bool = False,
    ) -> list[str]:
        linhas: list[str] = []

        if compact_for_rich_ui:
            compact_line = _Narrative.compact_product_line(
                self._host,
                code=code,
                description=description,
            )

            if compact_line:
                linhas.append(compact_line)
        elif description:
            linhas.append(
                self._route(
                    "factoryStatus",
                    "introWithDescription",
                    code=code,
                    description=description,
                )
            )
        elif code:
            linhas.append(
                self._route("factoryStatus", "introCodeOnly", code=code)
            )

        status = str(root.get("factory_status") or "").strip()

        if status:
            linhas.append(self._route("factoryStatus", "statusLine", status=status))

        reference_date = str(root.get("reference_date") or "").strip()

        if reference_date:
            linhas.append(
                self._route("factoryStatus", "referenceDateLine", date=reference_date)
            )

        structure_summary = self._section_block(root, "structure").get("summary")

        if isinstance(structure_summary, dict):
            linhas.append(
                self._route(
                    "factoryStatus",
                    "structureSummary",
                    components=str(structure_summary.get("total_components") or 0),
                    intermediates=str(structure_summary.get("total_intermediates") or 0),
                    rawMaterials=str(structure_summary.get("total_raw_materials") or 0),
                    exclusive=str(structure_summary.get("total_exclusive_raw_materials") or 0),
                )
            )

        stock_summary = self._section_block(root, "raw_material_stock").get("summary")

        if isinstance(stock_summary, dict):
            linhas.append(
                self._route(
                    "factoryStatus",
                    "stockSummary",
                    withoutStock=str(stock_summary.get("total_without_stock_for_one_pa") or 0),
                )
            )

        production_summary = self._section_block(root, "production").get("summary")

        if isinstance(production_summary, dict):
            linhas.append(
                self._route(
                    "factoryStatus",
                    "productionSummary",
                    paStarted=_Narrative.format_production_flag(
                        production_summary.get("pa_production_started")
                    ),
                    piStarted=_Narrative.format_production_flag(
                        production_summary.get("pi_production_started")
                    ),
                    paOrders=str(production_summary.get("total_pa_orders") or 0),
                    piOrders=str(production_summary.get("total_pi_orders") or 0),
                )
            )

        shipping_summary = self._section_block(root, "shipping").get("summary")

        if isinstance(shipping_summary, dict):
            linhas.append(
                self._route(
                    "factoryStatus",
                    "shippingSummary",
                    shipped=_Narrative.format_quantity(
                        self._host,
                        shipping_summary.get("total_shipped_quantity"),
                        field_key="total_shipped_quantity",
                    ),
                    loss=_Narrative.format_quantity(
                        self._host,
                        shipping_summary.get("total_inspection_loss_quantity"),
                        field_key="total_inspection_loss_quantity",
                    ),
                )
            )

        if compact_for_rich_ui:
            linhas.append(self._route("factoryStatus", "tableVisualizationHint"))

        return linhas or [self._host._presenter_text("generic", "apiAuthorized")]

    def _build_factory_highlights(self, root: dict) -> list[str]:
        highlights: list[str] = []
        status = str(root.get("factory_status") or "").strip()

        if status:
            highlights.append(
                self._insight("factoryStatus", "headlineStatus", status=status)
            )

        if "SEM ESTRUTURA" in status.upper():
            highlights.append(self._insight("factoryStatus", "noStructure"))

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}
        without_stock = indicators.get("total_raw_materials_without_stock_for_one_pa")

        if without_stock not in (None, "", 0, "0"):
            highlights.append(
                self._insight(
                    "factoryStatus",
                    "exclusiveWithoutStock",
                    count=str(without_stock),
                )
            )

        production_summary = self._section_block(root, "production").get("summary")

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
                highlights.append(self._insight("factoryStatus", "noProductionOrders"))
            elif not pa_started and not pi_started and total_orders > 0:
                highlights.append(self._insight("factoryStatus", "productionNotStarted"))
            else:
                highlights.append(
                    self._insight(
                        "factoryStatus",
                        "productionStarted",
                        pa=_Narrative.format_production_flag(
                            production_summary.get("pa_production_started")
                        ),
                        pi=_Narrative.format_production_flag(
                            production_summary.get("pi_production_started")
                        ),
                    )
                )

        shipping_summary = self._section_block(root, "shipping").get("summary")

        if isinstance(shipping_summary, dict):
            shipped = float(shipping_summary.get("total_shipped_quantity") or 0)

            if shipped > 0:
                highlights.append(
                    self._insight(
                        "factoryStatus",
                        "shippingWithMovement",
                        shipped=str(shipped),
                    )
                )
            else:
                highlights.append(self._insight("factoryStatus", "shippingNoMovement"))

        stock_items = self._section_block(root, "raw_material_stock").get("items")
        mp_summary = self._aggregate_mp_stock_rows(stock_items)

        if mp_summary:
            exclusive_count = 0
            structure_items = self._section_block(root, "structure").get("items")

            if isinstance(structure_items, list):
                exclusive_count = sum(
                    1
                    for item in structure_items
                    if isinstance(item, dict) and item.get("exclusive_raw_material") in (
                        True,
                        "SIM",
                        "Sim",
                    )
                )

            if exclusive_count == 0:
                highlights.append(self._insight("factoryStatus", "sharedMpWarning"))

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

                if pa_count <= self._MP_LOW_COVERAGE_PA_THRESHOLD:
                    highlights.append(
                        self._insight(
                            "factoryStatus",
                            "mpLowCoverage",
                            code=code,
                            required=str(row.get("quantity_required_for_one_pa") or "—"),
                            unit=str(row.get("unit") or ""),
                            available=_Narrative.format_quantity(
                                self._host,
                                row.get("available_quantity_total"),
                                field_key="available_quantity",
                            ),
                            paCount=f"{pa_count:.1f}".rstrip("0").rstrip("."),
                        )
                    )

        stock_summary = self._section_block(root, "raw_material_stock").get("summary")

        if isinstance(stock_summary, dict):
            without_stock = int(stock_summary.get("total_without_stock_for_one_pa") or 0)

            if without_stock > 0:
                highlights.append(
                    self._insight(
                        "factoryStatus",
                        "conclusionBlocked",
                        count=str(without_stock),
                    )
                )
            elif "LIBERADO" in status.upper():
                highlights.append(self._insight("factoryStatus", "conclusionReleased"))

        return highlights

    def _build_factory_attention(self, root: dict) -> list[str]:
        attention: list[str] = []
        status = str(root.get("factory_status") or "").strip()

        if "SEM ESTRUTURA" in status.upper():
            attention.append(self._insight("factoryStatus", "attentionNoStructure"))

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}
        without_stock = indicators.get("total_raw_materials_without_stock_for_one_pa")

        if without_stock not in (None, "", 0, "0"):
            attention.append(self._insight("factoryStatus", "attentionExclusiveStock"))

        if "NÃO INICIADO" in status.upper() or "NAO INICIADO" in status.upper():
            attention.append(self._insight("factoryStatus", "attentionOpNotStarted"))

        return attention

    def _build_factory_markdown_body(
        self,
        root: dict,
        *,
        code: str,
        description: str,
        compact_for_rich_ui: bool = False,
    ) -> str:
        parts: list[str] = []
        narrative_lines = self._build_factory_narrative_lines(
            root,
            code=code,
            description=description,
            compact_for_rich_ui=compact_for_rich_ui,
        )

        if narrative_lines:
            parts.append("\n\n".join(line for line in narrative_lines if line))

        highlights = self._build_factory_highlights(root)

        if highlights:
            parts.extend(["", self._insight("factoryStatus", "highlightsHeader"), ""])
            parts.extend(f"- {line}" for line in highlights)

        attention = self._build_factory_attention(root)

        if attention:
            parts.extend(["", self._insight("factoryStatus", "attentionHeader"), ""])
            parts.extend(f"{index}. {line}" for index, line in enumerate(attention, start=1))

        return _OpsTable.join_markdown_blocks(parts)

    def _build_factory_status_text_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )
        from app.domain.services.chat_rich_presentation_text_service import (
            ChatRichPresentationTextService,
        )

        code, description = self._product_context(root, path)
        title = (
            self._host._presenter_text(
                "productPresentationTitles",
                "factoryStatusWithCode",
                code=code,
            )
            if code
            else self._host._presenter_text(
                "productPresentationTitles",
                "factoryStatusGeneric",
            )
        )
        auxiliary_tables = self.build_factory_status_table_presentations(root, path)
        compact_for_rich_ui = ChatRichPresentationTextService.should_compact_narrative(
            table_presentations=auxiliary_tables,
        )
        body = self._build_factory_markdown_body(
            root,
            code=code,
            description=description,
            compact_for_rich_ui=compact_for_rich_ui,
        )

        if not body:
            return None

        markdown_parts = [f"### {title}", ""]

        if not compact_for_rich_ui:
            scope_line = ChatProductOperationalContentService.get(
                "presenter",
                "factoryStatus",
                "scopeIntro",
            )
            markdown_parts.extend([scope_line, ""])

        markdown_parts.append(body)

        return {
            "type": "markdown",
            "title": title,
            "markdown": "\n".join(markdown_parts).strip(),
        }

    def build_factory_status_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_factory_overview_table(root, path)

        if overview:
            overview["role"] = "profile"
            tables.append(overview)

        structure_items = self._section_block(root, "structure").get("items")

        if isinstance(structure_items, list) and structure_items:
            enriched = _OpsTable.enrich_structure_rows(
                [item for item in structure_items if isinstance(item, dict)]
            )
            shown, total = _OpsTable.limit_items(enriched, sort_key="level", reverse=False)
            structure_title = (
                self._route(
                    "factoryStatus",
                    "sectionStructureTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("factoryStatus", "sectionStructureTitle")
            )
            structure_table = _OpsTable.build_fixed_items_table(
                self._host,
                shown,
                table_id="structureExclusivityDetail",
                title=structure_title,
                role="structure",
            )

            if structure_table:
                tables.append(structure_table)

        stock_items = self._section_block(root, "raw_material_stock").get("items")

        if isinstance(stock_items, list) and stock_items:
            mp_summary_table = self._build_factory_mp_stock_summary_table(stock_items)

            if mp_summary_table:
                tables.append(mp_summary_table)

            stock_table = self._build_factory_stock_detail_table(stock_items)

            if stock_table:
                tables.append(stock_table)

        production_items = self._section_block(root, "production").get("items")

        if isinstance(production_items, list) and production_items:
            production_table = self._build_factory_production_table(production_items)

            if production_table:
                tables.append(production_table)

        shipping_items = self._section_block(root, "shipping").get("items")

        if isinstance(shipping_items, list) and shipping_items:
            shipping_dicts = [item for item in shipping_items if isinstance(item, dict)]
            shown, total = _OpsTable.limit_items(
                shipping_dicts,
                sort_key="production_order",
            )
            shipping_title = (
                self._route(
                    "factoryStatus",
                    "sectionShippingTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("factoryStatus", "sectionShippingTitle")
            )
            shipping_table = _OpsTable.build_fixed_items_table(
                self._host,
                shown,
                table_id="shippingStatusDetail",
                title=shipping_title,
                role="other",
            )

            if shipping_table:
                tables.append(shipping_table)

        return [table for table in tables if isinstance(table, dict)]

    def _aggregate_mp_stock_rows(self, stock_items: object) -> list[dict[str, Any]]:
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
                    "raw_material_description": str(item.get("raw_material_description") or "").strip(),
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

    def _build_factory_mp_stock_summary_table(self, stock_items: list) -> dict | None:
        rows = self._aggregate_mp_stock_rows(stock_items)

        return _OpsTable.build_fixed_items_table(
            self._host,
            rows,
            table_id="factoryMpStockSummary",
            title=self._route("factoryStatus", "sectionMpStockSummaryTitle"),
            role="stock",
        )

    def _build_factory_stock_detail_table(self, stock_items: list) -> dict | None:
        return _OpsTable.build_fixed_items_table(
            self._host,
            [item for item in stock_items if isinstance(item, dict)],
            table_id="factoryRawMaterialStockDetail",
            title=self._route("factoryStatus", "sectionStockTitle"),
            role="stock",
        )

    def _build_factory_production_table(self, production_items: list) -> dict | None:
        items = [item for item in production_items if isinstance(item, dict)]
        shown_items, total = _OpsTable.limit_items(items, sort_key="production_order")
        title = (
            self._route(
                "factoryStatus",
                "sectionProductionTitleTruncated",
                shown=str(len(shown_items)),
                total=str(total),
            )
            if total > len(shown_items)
            else self._route("factoryStatus", "sectionProductionTitle")
        )

        return _OpsTable.build_fixed_items_table(
            self._host,
            shown_items,
            table_id="factoryProductionDetail",
            title=title,
            role="list",
        )

    def _build_factory_overview_table(self, root: dict, path: str) -> dict | None:
        code, description = self._product_context(root, path)
        columns = self._host._column_labels.kv_table_column_defs()
        rows = [
            {
                "campo": "Situação consolidada",
                "valor": str(root.get("factory_status") or "—"),
            },
            {
                "campo": "Produto",
                "valor": f"{code} — {description}".strip(" —") or code or "—",
            },
        ]

        reference_date = str(root.get("reference_date") or "").strip()

        if reference_date:
            rows.append({"campo": "Referência", "valor": reference_date})

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}

        for key, value in list(indicators.items())[:8]:
            rows.append(
                {
                    "campo": self._host._column_labels.label_for(str(key)),
                    "valor": self._host._format_field_value(str(key), value),
                }
            )

        return {
            "type": "table",
            "title": self._route("factoryStatus", "overviewTableTitle"),
            "columns": columns,
            "rows": rows,
            "role": "profile",
        }

    def build_factory_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_kpi(
            self._host,
            root,
            path,
            profile_key="factory_status"
        )


    def build_factory_chart_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_chart(
            self._host,
            root,
            path,
            profile_key="factory_status",
        )

    def build_factory_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_tree(
            self._host,
            root,
            path,
            profile_key="factory_status"
        )

    def build_factory_dashboard_presentation(self, root: dict, path: str, *, kpi: dict | None = None, tree: dict | None = None, chart: dict | None = None, table: dict | None = None) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_dashboard(
            self._host,
            root,
            path,
            profile_key="factory_status",
            kpi=kpi,
            tree=tree,
            chart=chart,
            table=table
        )
