"""Apresentação humanizada para respostas composite_analysis (factory-status e similares)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
        parts.extend(
            self._build_factory_narrative_lines(
                root,
                code=code,
                description=description,
                compact_for_rich_ui=compact_for_rich_ui,
            )
        )

        highlights = self._build_factory_highlights(root)

        if highlights:
            parts.extend(["", self._insight("factoryStatus", "highlightsHeader"), ""])
            parts.extend(f"- {line}" for line in highlights)

        attention = self._build_factory_attention(root)

        if attention:
            parts.extend(["", self._insight("factoryStatus", "attentionHeader"), ""])
            parts.extend(f"{index}. {line}" for index, line in enumerate(attention, start=1))

        return "\n".join(part for part in parts if part is not None).strip()

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
            structure_table = self._host._build_items_table(
                structure_items,
                title=self._route("factoryStatus", "sectionStructureTitle"),
                path=path,
            )

            if isinstance(structure_table, dict):
                structure_table["role"] = "structure"
                tables.append(structure_table)

        stock_items = self._section_block(root, "raw_material_stock").get("items")

        if isinstance(stock_items, list) and stock_items:
            stock_table = self._host._build_items_table(
                stock_items,
                title=self._route("factoryStatus", "sectionStockTitle"),
                path=path,
            )

            if isinstance(stock_table, dict):
                stock_table["role"] = "stock"
                tables.append(stock_table)

        production_items = self._section_block(root, "production").get("items")

        if isinstance(production_items, list) and production_items:
            production_table = self._host._build_items_table(
                production_items,
                title=self._route("factoryStatus", "sectionProductionTitle"),
                path=path,
            )

            if isinstance(production_table, dict):
                production_table["role"] = "list"
                tables.append(production_table)

        shipping_items = self._section_block(root, "shipping").get("items")

        if isinstance(shipping_items, list) and shipping_items:
            shipping_table = self._host._build_items_table(
                shipping_items,
                title=self._route("factoryStatus", "sectionShippingTitle"),
                path=path,
            )

            if isinstance(shipping_table, dict):
                shipping_table["role"] = "other"
                tables.append(shipping_table)

        return [table for table in tables if isinstance(table, dict)]

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
                    "campo": self._host._humanize_key(str(key)),
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
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        code, _description = self._product_context(root, path)
        structure_summary = self._section_block(root, "structure").get("summary")
        stock_summary = self._section_block(root, "raw_material_stock").get("summary")
        production_summary = self._section_block(root, "production").get("summary")
        shipping_summary = self._section_block(root, "shipping").get("summary")

        if not any(
            isinstance(block, dict)
            for block in (structure_summary, stock_summary, production_summary, shipping_summary)
        ):
            return None

        title = (
            self._route("factoryStatus", "kpiTitle", code=code)
            if code
            else self._route("factoryStatus", "kpiTitleGeneric")
        )
        cards: list[dict[str, Any]] = []

        if isinstance(structure_summary, dict):
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("factoryStatus", "kpiComponents"),
                    value=int(structure_summary.get("total_components") or 0),
                    unit="",
                    color="#6366f1",
                    key="total_components",
                )
            )
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("factoryStatus", "kpiExclusiveRawMaterials"),
                    value=int(structure_summary.get("total_exclusive_raw_materials") or 0),
                    unit="",
                    color="#8b5cf6",
                    key="exclusive_raw_materials",
                )
            )

        if isinstance(stock_summary, dict):
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("factoryStatus", "kpiWithoutStock"),
                    value=int(stock_summary.get("total_without_stock_for_one_pa") or 0),
                    unit="MP",
                    color="#ef4444",
                    key="without_stock",
                )
            )

        if isinstance(production_summary, dict):
            total_orders = int(production_summary.get("total_pa_orders") or 0) + int(
                production_summary.get("total_pi_orders") or 0
            )
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("factoryStatus", "kpiProductionOrders"),
                    value=total_orders,
                    unit="OP",
                    color="#0ea5e9",
                    key="production_orders",
                )
            )

        if isinstance(shipping_summary, dict):
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("factoryStatus", "kpiShipped"),
                    value=float(shipping_summary.get("total_shipped_quantity") or 0),
                    unit="un.",
                    color="#10b981",
                    key="shipped_quantity",
                )
            )

        return ChatPresentationKpiAssemblyService.build(title=title, cards=cards, min_cards=2)

    def build_factory_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_hierarchy_tree_service import (
            ChatPresentationHierarchyTreeService,
        )

        structure_items = self._section_block(root, "structure").get("items")
        items = [item for item in structure_items if isinstance(item, dict)] if isinstance(
            structure_items,
            list,
        ) else []

        if not items:
            stock_items = self._section_block(root, "raw_material_stock").get("items")
            items = [item for item in stock_items if isinstance(item, dict)] if isinstance(
                stock_items,
                list,
            ) else []

            if not items:
                return None

            code, _description = self._product_context(root, path)
            title = (
                self._route("factoryStatus", "treeStockTitle", code=code)
                if code
                else self._route("factoryStatus", "treeStockTitleGeneric")
            )

            def _stock_leaf(item: dict[str, Any]) -> dict[str, Any]:
                mp_code = str(item.get("raw_material_code") or "—")
                return ChatPresentationHierarchyTreeService._serialize_node(
                    node_id=f"mp:{mp_code}",
                    label=self._route("factoryStatus", "treeStockLeafLabel", code=mp_code),
                    subtitle=str(item.get("has_stock_for_one_pa") or "").strip(),
                    meta={
                        "available_quantity": float(item.get("available_quantity") or 0),
                    },
                )

            return ChatPresentationHierarchyTreeService.build_multi_level(
                title=title,
                root_id=code or "factory-stock",
                root_label=(
                    self._route("factoryStatus", "treeRootLabel", code=code)
                    if code
                    else title
                ),
                items=items,
                group_keys=["has_stock_for_one_pa"],
                leaf_builder=_stock_leaf,
            )

        code, _description = self._product_context(root, path)
        title = (
            self._route("factoryStatus", "treeTitle", code=code)
            if code
            else self._route("factoryStatus", "treeTitleGeneric")
        )

        def _structure_leaf(item: dict[str, Any]) -> dict[str, Any]:
            component_type = str(item.get("component_type") or "—")
            component_code = str(
                item.get("component_code")
                or item.get("raw_material_code")
                or component_type
            )
            return ChatPresentationHierarchyTreeService._serialize_node(
                node_id=f"cmp:{component_code}:{component_type}",
                label=self._route(
                    "factoryStatus",
                    "treeStructureLeafLabel",
                    code=component_code,
                    componentType=component_type,
                ),
                subtitle=str(item.get("exclusive_raw_material") or "").strip(),
            )

        return ChatPresentationHierarchyTreeService.build_multi_level(
            title=title,
            root_id=code or "factory-structure",
            root_label=(
                self._route("factoryStatus", "treeRootLabel", code=code)
                if code
                else title
            ),
            items=items,
            group_keys=["component_type"],
            leaf_builder=_structure_leaf,
        )

    def build_factory_chart_presentation(self, root: dict, path: str) -> dict | None:
        stock_items = self._section_block(root, "raw_material_stock").get("items")

        if not isinstance(stock_items, list) or not stock_items:
            return None

        chart_data: list[dict[str, Any]] = []
        quantity_label = self._host._humanize_key("available_quantity")

        for item in stock_items[:20]:
            if not isinstance(item, dict):
                continue

            code = str(item.get("raw_material_code") or "—")
            chart_data.append(
                {
                    "name": code,
                    quantity_label: float(item.get("available_quantity") or 0),
                }
            )

        if not chart_data:
            return None

        code, _description = self._product_context(root, path)

        return {
            "type": "chart",
            "title": (
                self._route("factoryStatus", "chartStockTitle", code=code)
                if code
                else self._route("factoryStatus", "chartStockTitleGeneric")
            ),
            "chartType": "horizontal_bar",
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": [quantity_label],
                "colors": ["#10b981"],
                "legend": False,
            },
        }

    def build_factory_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        from app.domain.services.chat_presentation_dashboard_assembly_service import (
            ChatPresentationDashboardAssemblyService,
        )

        code, _description = self._product_context(root, path)
        title = (
            self._route("factoryStatus", "dashboardTitle", code=code)
            if code
            else self._route("factoryStatus", "dashboardTitleGeneric")
        )
        panels: list[dict] = []

        if isinstance(kpi, dict) and kpi.get("type") == "kpi":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="summary",
                    title=str(kpi.get("title") or self._route("factoryStatus", "overviewTableTitle")),
                    presentation=kpi,
                )
            )

        if isinstance(chart, dict) and chart.get("type") == "chart":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="chart",
                    title=str(chart.get("title") or self._route("factoryStatus", "chartStockTitleGeneric")),
                    presentation=chart,
                    chart_presentation=chart,
                )
            )

        if isinstance(table, dict) and table.get("type") == "table":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="detail",
                    title=str(table.get("title") or self._route("factoryStatus", "sectionStockTitle")),
                    presentation=table,
                )
            )

        return ChatPresentationDashboardAssemblyService.build(title=title, panels=panels)
