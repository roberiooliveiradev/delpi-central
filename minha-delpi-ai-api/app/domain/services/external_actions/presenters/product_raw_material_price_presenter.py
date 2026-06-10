"""Apresentação humanizada — preço MP, simulador de custos PA e rotas granulares."""

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


class ExternalActionProductRawMaterialPricePresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

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

    def _present_raw_material_price_intelligence(self, root: dict, path: str) -> dict:
        code, description = self._product_context(root, path)
        linhas = self._build_intelligence_lines(root, code=code, description=description)
        markdown = self._build_intelligence_text_presentation(root, path)

        return {
            "titulo": (
                self._route("rawMaterialPriceIntelligence", "titleWithCode", code=code)
                if code
                else self._route("rawMaterialPriceIntelligence", "titleGeneric")
            ),
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
            "humanizedMarkdown": markdown.get("markdown") if isinstance(markdown, dict) else None,
        }

    def _present_cost_impact_simulation(self, root: dict, path: str) -> dict:
        code, description = self._product_context(root, path)
        linhas = self._build_cost_impact_lines(root, code=code, description=description)
        markdown = self._build_cost_impact_text_presentation(root, path)

        return {
            "titulo": (
                self._route("costImpactSimulation", "titleWithCode", code=code)
                if code
                else self._route("costImpactSimulation", "titleGeneric")
            ),
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
            "humanizedMarkdown": markdown.get("markdown") if isinstance(markdown, dict) else None,
        }

    def _present_last_purchase(self, root: dict, path: str) -> dict:
        code, description = self._product_context(root, path)
        markdown = self._build_last_purchase_text_presentation(root, path)
        linhas: list[str] = []

        if isinstance(markdown, dict) and markdown.get("markdown"):
            linhas = [
                line
                for line in str(markdown["markdown"]).splitlines()
                if line.strip() and not line.startswith("###")
            ]
        else:
            compact = _Narrative.compact_product_line(
                self._host,
                code=code,
                description=description,
            )

            if compact:
                linhas.append(compact)

            last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

            if last_purchase:
                for key, value in list(last_purchase.items())[:10]:
                    linhas.append(
                        f"{self._host._humanize_key(str(key))}: "
                        f"{self._host._format_field_value(str(key), value)}"
                    )
            else:
                linhas.append(self._route("lastPurchase", "emptyLine"))

        title = (
            self._route("lastPurchase", "titleWithCode", code=code)
            if code
            else self._route("lastPurchase", "titleGeneric")
        )

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
            "humanizedMarkdown": markdown.get("markdown") if isinstance(markdown, dict) else None,
        }

    def _build_intelligence_lines(
        self,
        root: dict,
        *,
        code: str,
        description: str,
    ) -> list[str]:
        linhas: list[str] = []

        if description:
            linhas.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "introWithDescription",
                    code=code,
                    description=description,
                )
            )
        elif code:
            linhas.append(
                self._route("rawMaterialPriceIntelligence", "introCodeOnly", code=code)
            )

        price_status = str(root.get("price_status") or "").strip()

        if price_status:
            linhas.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "priceStatusLine",
                    status=price_status,
                )
            )

        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

        if last_purchase.get("unit_price") is not None:
            linhas.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "lastPurchaseLine",
                    price=str(last_purchase.get("unit_price")),
                    supplier=str(last_purchase.get("supplier_code") or "—"),
                )
            )

        price_summary = self._section_block(root, "price_history").get("summary")

        if isinstance(price_summary, dict) and price_summary.get("total_records"):
            linhas.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "priceHistorySummaryLine",
                    count=str(price_summary.get("total_records")),
                    avg=str(price_summary.get("average_unit_price") or "—"),
                )
            )

        budget_summary = self._section_block(root, "budget_history").get("summary")

        if isinstance(budget_summary, dict) and budget_summary.get("total_records"):
            linhas.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "budgetHistorySummaryLine",
                    count=str(budget_summary.get("total_records")),
                )
            )

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}

        if indicators.get("dominant_supplier_code"):
            linhas.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "dominantSupplierLine",
                    supplier=str(indicators.get("dominant_supplier_code")),
                )
            )

        linhas.append(self._route("rawMaterialPriceIntelligence", "tableVisualizationHint"))

        return linhas

    def _build_cost_impact_lines(
        self,
        root: dict,
        *,
        code: str,
        description: str,
    ) -> list[str]:
        linhas: list[str] = []

        if description:
            linhas.append(
                self._route(
                    "costImpactSimulation",
                    "introWithDescription",
                    code=code,
                    description=description,
                )
            )
        elif code:
            linhas.append(
                self._route("costImpactSimulation", "introCodeOnly", code=code)
            )

        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        simulation = root.get("simulation") if isinstance(root.get("simulation"), dict) else {}
        materials = self._section_block(root, "materials").get("items") or []

        if summary.get("total_material_cost") is not None:
            linhas.append(
                self._route(
                    "costImpactSimulation",
                    "totalMaterialCostLine",
                    value=str(summary.get("total_material_cost")),
                )
            )

        if materials:
            top = materials[0] if isinstance(materials[0], dict) else {}
            linhas.append(
                self._route(
                    "costImpactSimulation",
                    "topMaterialLine",
                    code=str(top.get("raw_material_code") or "—"),
                    impact=str(top.get("impact_on_material_cost_percent") or "—"),
                )
            )

        adjustment = simulation.get("adjustment_percent")

        if adjustment not in (None, "", 0, 0.0):
            linhas.append(
                self._route(
                    "costImpactSimulation",
                    "simulationLine",
                    percent=str(adjustment),
                    delta=str(simulation.get("projected_cost_delta") or "—"),
                )
            )

        linhas.append(self._route("costImpactSimulation", "tableVisualizationHint"))

        return linhas

    def build_raw_material_price_intelligence_table_presentations(
        self,
        root: dict,
        path: str,
    ) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_intelligence_overview_table(root, path)

        if overview:
            overview["role"] = "profile"
            tables.append(overview)

        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

        if last_purchase:
            purchase_table = self._build_kv_table(
                last_purchase,
                self._route("rawMaterialPriceIntelligence", "lastPurchaseTableTitle"),
            )
            purchase_table["role"] = "pricing"
            tables.append(purchase_table)

        price_items = self._section_block(root, "price_history").get("items")

        if isinstance(price_items, list) and price_items:
            price_dicts = [item for item in price_items if isinstance(item, dict)]
            shown, total = _OpsTable.limit_items(price_dicts, sort_key="issue_date")
            history_title = (
                self._route(
                    "rawMaterialPriceIntelligence",
                    "priceHistoryTableTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("rawMaterialPriceIntelligence", "priceHistoryTableTitle")
            )
            history_table = _OpsTable.build_fixed_items_table(
                self._host,
                shown,
                table_id="mpPriceHistoryDetail",
                title=history_title,
                role="list",
            )

            if history_table:
                tables.append(history_table)

        budget_items = self._section_block(root, "budget_history").get("items")

        if isinstance(budget_items, list) and budget_items:
            budget_dicts = [item for item in budget_items if isinstance(item, dict)]
            shown, total = _OpsTable.limit_items(budget_dicts, sort_key="source", reverse=False)
            budget_title = (
                self._route(
                    "rawMaterialPriceIntelligence",
                    "budgetHistoryTableTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("rawMaterialPriceIntelligence", "budgetHistoryTableTitle")
            )
            budget_table = _OpsTable.build_fixed_items_table(
                self._host,
                shown,
                table_id="mpBudgetHistoryDetail",
                title=budget_title,
                role="other",
            )

            if budget_table:
                tables.append(budget_table)

        return [table for table in tables if isinstance(table, dict)]

    def build_cost_impact_simulation_table_presentations(
        self,
        root: dict,
        path: str,
    ) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_cost_impact_overview_table(root, path)

        if overview:
            overview["role"] = "profile"
            tables.append(overview)

        material_items = self._section_block(root, "materials").get("items")

        if isinstance(material_items, list) and material_items:
            material_dicts = [item for item in material_items if isinstance(item, dict)]
            shown, total = _OpsTable.limit_items(material_dicts, sort_key="rank", reverse=False)
            materials_title = (
                self._route(
                    "costImpactSimulation",
                    "materialsTableTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("costImpactSimulation", "materialsTableTitle")
            )
            materials_table = _OpsTable.build_fixed_items_table(
                self._host,
                shown,
                table_id="costImpactMaterials",
                title=materials_title,
                role="list",
            )

            if materials_table:
                tables.append(materials_table)

        return [table for table in tables if isinstance(table, dict)]

    def build_last_purchase_table_presentation(self, root: dict, path: str) -> dict | None:
        tables = self.build_last_purchase_table_presentations(root, path)

        if not tables:
            return None

        for table in tables:
            if isinstance(table, dict) and table.get("role") == "list":
                return table

        return tables[-1] if tables else None

    def build_last_purchase_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_last_purchase_overview_table(root, path)

        if overview:
            tables.append(overview)

        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

        if last_purchase:
            detail = self._build_kv_table(last_purchase, self._route("lastPurchase", "tableTitle"))
            detail["role"] = "list"
            tables.append(detail)

        return [table for table in tables if isinstance(table, dict)]

    def _build_last_purchase_overview_table(self, root: dict, path: str) -> dict | None:
        code, description = self._product_context(root, path)
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

        if not last_purchase:
            return None

        columns = self._host._column_labels.kv_table_column_defs()
        rows = [
            {
                "campo": self._route("lastPurchase", "overviewProductField"),
                "valor": f"{code} — {description}".strip(" —") or code or "—",
            },
        ]

        for key in ("unit_price", "supplier_code", "supplier_name", "icms_rate", "invoice_date"):
            if key in last_purchase:
                rows.append(
                    {
                        "campo": self._host._humanize_key(key),
                        "valor": self._host._format_field_value(key, last_purchase.get(key)),
                    }
                )

        return {
            "type": "table",
            "title": self._route("lastPurchase", "overviewTableTitle"),
            "columns": columns,
            "rows": rows,
            "role": "profile",
        }

    def _build_last_purchase_text_presentation(self, root: dict, path: str) -> dict | None:
        code, description = self._product_context(root, path)
        title = (
            self._route("lastPurchase", "titleWithCode", code=code)
            if code
            else self._route("lastPurchase", "titleGeneric")
        )
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}
        parts: list[str] = []

        if description:
            parts.append(
                self._route(
                    "lastPurchase",
                    "introWithDescription",
                    code=code,
                    description=description,
                )
            )
        elif code:
            parts.append(self._route("lastPurchase", "introCodeOnly", code=code))

        if last_purchase.get("unit_price") is not None:
            parts.append(
                self._route(
                    "lastPurchase",
                    "priceLine",
                    price=str(last_purchase.get("unit_price")),
                    supplier=str(last_purchase.get("supplier_code") or "—"),
                )
            )

        if last_purchase.get("icms_rate") is not None:
            parts.append(
                self._route(
                    "lastPurchase",
                    "icmsLine",
                    rate=str(last_purchase.get("icms_rate")),
                )
            )

        if not parts:
            parts.append(self._route("lastPurchase", "emptyLine"))

        return {
            "type": "markdown",
            "title": title,
            "markdown": f"### {title}\n\n" + "\n\n".join(parts),
        }

    def build_last_purchase_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        code, _description = self._product_context(root, path)
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

        if not last_purchase:
            return None

        title = (
            self._route("lastPurchase", "kpiTitle", code=code)
            if code
            else self._route("lastPurchase", "kpiTitleGeneric")
        )
        cards: list[dict[str, Any]] = []

        if last_purchase.get("unit_price") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("lastPurchase", "kpiUnitPrice"),
                    value=float(last_purchase.get("unit_price") or 0),
                    unit="R$",
                    color="#10b981",
                    key="unit_price",
                )
            )

        if last_purchase.get("icms_rate") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("lastPurchase", "kpiIcmsRate"),
                    value=float(last_purchase.get("icms_rate") or 0),
                    unit="%",
                    color="#6366f1",
                    key="icms_rate",
                )
            )

        return ChatPresentationKpiAssemblyService.build(title=title, cards=cards, min_cards=2)

    def build_last_purchase_chart_presentation(self, root: dict, path: str) -> dict | None:
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}
        unit_price = last_purchase.get("unit_price")
        icms_rate = last_purchase.get("icms_rate")

        if unit_price is None:
            return None

        price_value = float(unit_price or 0)
        icms_value = price_value * float(icms_rate or 0) / 100 if icms_rate is not None else 0
        net_label = self._route("lastPurchase", "chartNetPriceLabel")
        icms_label = self._route("lastPurchase", "chartIcmsLabel")
        code, _description = self._product_context(root, path)

        return {
            "type": "chart",
            "title": (
                self._route("lastPurchase", "chartTitle", code=code)
                if code
                else self._route("lastPurchase", "chartTitleGeneric")
            ),
            "chartType": "horizontal_bar",
            "data": [
                {
                    "name": self._route("lastPurchase", "chartCompositionLabel"),
                    net_label: price_value,
                    icms_label: icms_value,
                }
            ],
            "config": {
                "xAxis": "name",
                "yAxis": [net_label, icms_label],
                "colors": ["#10b981", "#6366f1"],
                "legend": True,
            },
        }

    def build_last_purchase_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_hierarchy_tree_service import (
            ChatPresentationHierarchyTreeService,
        )

        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

        if not last_purchase:
            return None

        code, _description = self._product_context(root, path)
        supplier = str(last_purchase.get("supplier_code") or "—")
        title = (
            self._route("lastPurchase", "treeTitle", code=code)
            if code
            else self._route("lastPurchase", "treeTitleGeneric")
        )

        def _leaf(item: dict[str, Any]) -> dict[str, Any]:
            return ChatPresentationHierarchyTreeService._serialize_node(
                node_id="last-purchase:nf",
                label=self._route(
                    "lastPurchase",
                    "treeInvoiceLeafLabel",
                    price=str(item.get("unit_price") or "—"),
                ),
                subtitle=str(item.get("invoice_date") or "").strip(),
            )

        enriched = [{**last_purchase, "supplier_group": supplier}]

        return ChatPresentationHierarchyTreeService.build_multi_level(
            title=title,
            root_id=code or "last-purchase",
            root_label=(
                self._route("lastPurchase", "treeRootLabel", code=code)
                if code
                else title
            ),
            items=enriched,
            group_keys=["supplier_group"],
            leaf_builder=_leaf,
        )

    def build_last_purchase_dashboard_presentation(
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
            self._route("lastPurchase", "dashboardTitle", code=code)
            if code
            else self._route("lastPurchase", "dashboardTitleGeneric")
        )
        panels: list[dict] = []

        if isinstance(kpi, dict) and kpi.get("type") == "kpi":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="summary",
                    title=str(kpi.get("title") or self._route("lastPurchase", "overviewTableTitle")),
                    presentation=kpi,
                )
            )

        if isinstance(chart, dict) and chart.get("type") == "chart":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="chart",
                    title=str(chart.get("title") or self._route("lastPurchase", "chartTitleGeneric")),
                    presentation=chart,
                    chart_presentation=chart,
                )
            )

        if isinstance(table, dict) and table.get("type") == "table":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="detail",
                    title=str(table.get("title") or self._route("lastPurchase", "tableTitle")),
                    presentation=table,
                )
            )

        return ChatPresentationDashboardAssemblyService.build(title=title, panels=panels, min_panels=2)

    def _build_intelligence_overview_table(self, root: dict, path: str) -> dict | None:
        code, description = self._product_context(root, path)
        columns = self._host._column_labels.kv_table_column_defs()
        rows = [
            {
                "campo": self._route("rawMaterialPriceIntelligence", "overviewProductField"),
                "valor": f"{code} — {description}".strip(" —") or code or "—",
            },
            {
                "campo": self._route("rawMaterialPriceIntelligence", "overviewStatusField"),
                "valor": str(root.get("price_status") or "—"),
            },
        ]

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}

        for key, value in list(indicators.items())[:6]:
            rows.append(
                {
                    "campo": self._host._humanize_key(str(key)),
                    "valor": self._host._format_field_value(str(key), value),
                }
            )

        return {
            "type": "table",
            "title": self._route("rawMaterialPriceIntelligence", "overviewTableTitle"),
            "columns": columns,
            "rows": rows,
        }

    def _build_cost_impact_overview_table(self, root: dict, path: str) -> dict | None:
        code, description = self._product_context(root, path)
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        simulation = root.get("simulation") if isinstance(root.get("simulation"), dict) else {}
        columns = self._host._column_labels.kv_table_column_defs()
        rows = [
            {
                "campo": self._route("costImpactSimulation", "overviewProductField"),
                "valor": f"{code} — {description}".strip(" —") or code or "—",
            },
        ]

        for key in (
            "total_material_cost",
            "total_materials",
            "price_source",
            "adjustment_percent",
            "projected_cost_delta",
        ):
            if key in summary or key in simulation:
                value = simulation.get(key, summary.get(key))
                rows.append(
                    {
                        "campo": self._host._humanize_key(key),
                        "valor": self._host._format_field_value(key, value),
                    }
                )

        return {
            "type": "table",
            "title": self._route("costImpactSimulation", "overviewTableTitle"),
            "columns": columns,
            "rows": rows,
        }

    def _build_kv_table(self, payload: dict, title: str) -> dict:
        columns = self._host._column_labels.kv_table_column_defs()
        rows = [
            {
                "campo": self._host._humanize_key(str(key)),
                "valor": self._host._format_field_value(str(key), value),
            }
            for key, value in payload.items()
        ]

        return {
            "type": "table",
            "title": title,
            "columns": columns,
            "rows": rows,
        }

    def _build_intelligence_text_presentation(self, root: dict, path: str) -> dict | None:
        code, _ = self._product_context(root, path)
        title = (
            self._route("rawMaterialPriceIntelligence", "titleWithCode", code=code)
            if code
            else self._route("rawMaterialPriceIntelligence", "titleGeneric")
        )
        highlights = self._build_intelligence_highlights(root)
        attention = self._build_intelligence_attention(root)
        parts = [highlights]

        if attention:
            parts.extend(["", attention])

        body = "\n\n".join(part for part in parts if part).strip()

        if not body:
            return None

        return {
            "type": "markdown",
            "title": title,
            "markdown": f"### {title}\n\n{body}".strip(),
        }

    def _build_cost_impact_text_presentation(self, root: dict, path: str) -> dict | None:
        code, _ = self._product_context(root, path)
        title = (
            self._route("costImpactSimulation", "titleWithCode", code=code)
            if code
            else self._route("costImpactSimulation", "titleGeneric")
        )
        highlights = self._build_cost_impact_highlights(root)

        if not highlights:
            return None

        return {
            "type": "markdown",
            "title": title,
            "markdown": f"### {title}\n\n{highlights}".strip(),
        }

    def _build_intelligence_highlights(self, root: dict) -> str:
        parts: list[str] = []
        price_status = str(root.get("price_status") or "").strip()

        if price_status:
            parts.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "priceStatusLine",
                    status=price_status,
                )
            )

        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

        if last_purchase.get("unit_price") is not None:
            parts.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "lastPurchaseLine",
                    price=str(last_purchase.get("unit_price")),
                    supplier=str(last_purchase.get("supplier_code") or "—"),
                )
            )

        return "\n\n".join(parts)

    def _build_intelligence_attention(self, root: dict) -> str:
        warnings = root.get("warnings")

        if not isinstance(warnings, list) or not warnings:
            return ""

        lines = [f"- {str(item).strip()}" for item in warnings if str(item).strip()]

        if not lines:
            return ""

        header = self._route("rawMaterialPriceIntelligence", "warningsHeader")
        return f"**{header}**\n\n" + "\n".join(lines)

    def _build_cost_impact_highlights(self, root: dict) -> str:
        materials = self._section_block(root, "materials").get("items") or []

        if not isinstance(materials, list) or not materials:
            return ""

        lines = [
            self._route("costImpactSimulation", "highlightsHeader"),
            "",
        ]

        for item in materials[:5]:
            if not isinstance(item, dict):
                continue

            lines.append(
                self._route(
                    "costImpactSimulation",
                    "materialRankLine",
                    rank=str(item.get("rank") or "—"),
                    code=str(item.get("raw_material_code") or "—"),
                    impact=str(item.get("impact_on_material_cost_percent") or "—"),
                )
            )

        return "\n".join(lines)

    def build_raw_material_price_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        code, _description = self._product_context(root, path)
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}
        price_summary = self._section_block(root, "price_history").get("summary")
        budget_summary = self._section_block(root, "budget_history").get("summary")
        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}

        if not any(
            (
                last_purchase.get("unit_price") is not None,
                isinstance(price_summary, dict) and price_summary.get("total_records"),
                isinstance(budget_summary, dict) and budget_summary.get("total_records"),
            )
        ):
            return None

        title = (
            self._route("rawMaterialPriceIntelligence", "kpiTitle", code=code)
            if code
            else self._route("rawMaterialPriceIntelligence", "kpiTitleGeneric")
        )
        cards: list[dict[str, Any]] = []

        if last_purchase.get("unit_price") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("rawMaterialPriceIntelligence", "kpiLastPrice"),
                    value=float(last_purchase.get("unit_price") or 0),
                    unit="R$",
                    color="#10b981",
                    key="last_unit_price",
                )
            )

        if isinstance(price_summary, dict) and price_summary.get("average_unit_price") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("rawMaterialPriceIntelligence", "kpiAveragePrice"),
                    value=float(price_summary.get("average_unit_price") or 0),
                    unit="R$",
                    color="#0ea5e9",
                    key="average_unit_price",
                )
            )

        if isinstance(price_summary, dict) and price_summary.get("total_records"):
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("rawMaterialPriceIntelligence", "kpiPriceRecords"),
                    value=int(price_summary.get("total_records") or 0),
                    unit="",
                    color="#6366f1",
                    key="price_records",
                )
            )

        if isinstance(budget_summary, dict) and budget_summary.get("total_records"):
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("rawMaterialPriceIntelligence", "kpiBudgetRecords"),
                    value=int(budget_summary.get("total_records") or 0),
                    unit="",
                    color="#8b5cf6",
                    key="budget_records",
                )
            )

        if indicators.get("dominant_supplier_share_percent") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("rawMaterialPriceIntelligence", "kpiDominantShare"),
                    value=float(indicators.get("dominant_supplier_share_percent") or 0),
                    unit="%",
                    color="#f59e0b",
                    key="dominant_supplier_share",
                )
            )

        return ChatPresentationKpiAssemblyService.build(title=title, cards=cards, min_cards=2)

    def build_raw_material_price_chart_presentation(self, root: dict, path: str) -> dict | None:
        price_items = self._section_block(root, "price_history").get("items")

        if not isinstance(price_items, list) or len(price_items) < 2:
            return None

        unit_label = self._route("rawMaterialPriceIntelligence", "chartUnitPriceLabel")
        chart_data: list[dict[str, Any]] = []

        for index, item in enumerate(price_items[:20], start=1):
            if not isinstance(item, dict):
                continue

            supplier = str(item.get("supplier_code") or "").strip()
            label = supplier or f"#{index}"
            chart_data.append(
                {
                    "name": label,
                    unit_label: float(item.get("unit_price") or 0),
                }
            )

        if len(chart_data) < 2:
            return None

        code, _description = self._product_context(root, path)

        return {
            "type": "chart",
            "title": (
                self._route("rawMaterialPriceIntelligence", "chartPriceHistoryTitle", code=code)
                if code
                else self._route("rawMaterialPriceIntelligence", "chartPriceHistoryTitleGeneric")
            ),
            "chartType": "line_chart",
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": [unit_label],
                "colors": ["#0ea5e9"],
                "legend": False,
            },
        }

    def build_raw_material_price_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_hierarchy_tree_service import (
            ChatPresentationHierarchyTreeService,
        )

        combined: list[dict[str, Any]] = []
        price_items = self._section_block(root, "price_history").get("items")

        if isinstance(price_items, list):
            for item in price_items:
                if isinstance(item, dict):
                    combined.append({**item, "record_kind": "nf"})

        budget_items = self._section_block(root, "budget_history").get("items")

        if isinstance(budget_items, list):
            for item in budget_items:
                if isinstance(item, dict):
                    combined.append({**item, "record_kind": "orcamento"})

        if not combined:
            return None

        code, _description = self._product_context(root, path)
        title = (
            self._route("rawMaterialPriceIntelligence", "treeSuppliersTitle", code=code)
            if code
            else self._route("rawMaterialPriceIntelligence", "treeSuppliersTitleGeneric")
        )

        def _leaf(item: dict[str, Any]) -> dict[str, Any]:
            supplier = str(item.get("supplier_code") or "—")
            price = self._host._format_field_value("unit_price", item.get("unit_price"))

            return ChatPresentationHierarchyTreeService._serialize_node(
                node_id=f"mp:{supplier}:{item.get('record_kind')}:{price}",
                label=self._route(
                    "rawMaterialPriceIntelligence",
                    "treeSupplierLeafLabel",
                    price=price,
                ),
                subtitle=supplier,
                meta={
                    "record_kind": str(item.get("record_kind") or ""),
                    "unit_price": item.get("unit_price"),
                },
            )

        return ChatPresentationHierarchyTreeService.build_multi_level(
            title=title,
            root_id=code or "raw-material-price",
            root_label=(
                self._route("rawMaterialPriceIntelligence", "treeRootLabel", code=code)
                if code
                else title
            ),
            items=combined,
            group_keys=["supplier_code"],
            leaf_builder=_leaf,
        )

    def build_raw_material_price_dashboard_presentation(
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
            self._route("rawMaterialPriceIntelligence", "dashboardTitle", code=code)
            if code
            else self._route("rawMaterialPriceIntelligence", "dashboardTitleGeneric")
        )
        panels: list[dict] = []

        if isinstance(kpi, dict) and kpi.get("type") == "kpi":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="summary",
                    title=str(kpi.get("title") or self._route("rawMaterialPriceIntelligence", "overviewTableTitle")),
                    presentation=kpi,
                )
            )

        if isinstance(chart, dict) and chart.get("type") == "chart":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="chart",
                    title=str(chart.get("title") or self._route("rawMaterialPriceIntelligence", "chartPriceHistoryTitleGeneric")),
                    presentation=chart,
                    chart_presentation=chart,
                )
            )

        if isinstance(table, dict) and table.get("type") == "table":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="overview",
                    title=str(table.get("title") or self._route("rawMaterialPriceIntelligence", "overviewTableTitle")),
                    presentation=table,
                )
            )

        return ChatPresentationDashboardAssemblyService.build(title=title, panels=panels, min_panels=2)

    def build_cost_impact_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        code, _description = self._product_context(root, path)
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        simulation = root.get("simulation") if isinstance(root.get("simulation"), dict) else {}
        materials = self._section_block(root, "materials").get("items") or []

        if not isinstance(materials, list) or not materials:
            return None

        title = (
            self._route("costImpactSimulation", "kpiTitle", code=code)
            if code
            else self._route("costImpactSimulation", "kpiTitleGeneric")
        )
        cards: list[dict[str, Any]] = []

        if summary.get("total_material_cost") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("costImpactSimulation", "kpiTotalMaterialCost"),
                    value=float(summary.get("total_material_cost") or 0),
                    unit="R$",
                    color="#10b981",
                    key="total_material_cost",
                )
            )

        if summary.get("total_materials") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("costImpactSimulation", "kpiTotalMaterials"),
                    value=int(summary.get("total_materials") or 0),
                    unit="MP",
                    color="#6366f1",
                    key="total_materials",
                )
            )

        top = materials[0] if isinstance(materials[0], dict) else {}

        if top.get("impact_on_material_cost_percent") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("costImpactSimulation", "kpiTopImpact"),
                    value=float(top.get("impact_on_material_cost_percent") or 0),
                    unit="%",
                    color="#f59e0b",
                    key="top_impact_percent",
                )
            )

        if simulation.get("adjustment_percent") not in (None, "", 0, 0.0):
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("costImpactSimulation", "kpiAdjustmentPercent"),
                    value=float(simulation.get("adjustment_percent") or 0),
                    unit="%",
                    color="#0ea5e9",
                    key="adjustment_percent",
                )
            )

        if simulation.get("projected_cost_delta") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("costImpactSimulation", "kpiProjectedDelta"),
                    value=float(simulation.get("projected_cost_delta") or 0),
                    unit="R$",
                    color="#8b5cf6",
                    key="projected_cost_delta",
                )
            )

        return ChatPresentationKpiAssemblyService.build(title=title, cards=cards, min_cards=2)

    def build_cost_impact_chart_presentation(self, root: dict, path: str) -> dict | None:
        material_items = self._section_block(root, "materials").get("items")

        if not isinstance(material_items, list) or len(material_items) < 2:
            return None

        impact_label = self._route("costImpactSimulation", "chartImpactLabel")
        chart_data: list[dict[str, Any]] = []

        for item in material_items[:20]:
            if not isinstance(item, dict):
                continue

            mp_code = str(item.get("raw_material_code") or "—")
            chart_data.append(
                {
                    "name": mp_code,
                    impact_label: float(item.get("impact_on_material_cost_percent") or 0),
                }
            )

        if len(chart_data) < 2:
            return None

        code, _description = self._product_context(root, path)

        return {
            "type": "chart",
            "title": (
                self._route("costImpactSimulation", "chartImpactTitle", code=code)
                if code
                else self._route("costImpactSimulation", "chartImpactTitleGeneric")
            ),
            "chartType": "horizontal_bar",
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": [impact_label],
                "colors": ["#f59e0b"],
                "legend": False,
            },
        }

    def build_cost_impact_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_hierarchy_tree_service import (
            ChatPresentationHierarchyTreeService,
        )

        material_items = self._section_block(root, "materials").get("items")

        if not isinstance(material_items, list) or not material_items:
            return None

        enriched = [
            {**item, "bom_group": "materiais"}
            for item in material_items
            if isinstance(item, dict)
        ]

        if not enriched:
            return None

        code, _description = self._product_context(root, path)
        title = (
            self._route("costImpactSimulation", "treeMaterialsTitle", code=code)
            if code
            else self._route("costImpactSimulation", "treeMaterialsTitleGeneric")
        )

        def _leaf(item: dict[str, Any]) -> dict[str, Any]:
            mp_code = str(item.get("raw_material_code") or "—")
            impact = str(item.get("impact_on_material_cost_percent") or "—")

            return ChatPresentationHierarchyTreeService._serialize_node(
                node_id=f"bom:{mp_code}:{item.get('rank')}",
                label=self._route(
                    "costImpactSimulation",
                    "treeMaterialLeafLabel",
                    code=mp_code,
                    impact=impact,
                ),
                subtitle=str(item.get("raw_material_description") or "").strip(),
                meta={
                    "rank": item.get("rank"),
                    "extended_cost": item.get("extended_cost"),
                    "impact_on_pa_cost_percent": item.get("impact_on_pa_cost_percent"),
                },
            )

        return ChatPresentationHierarchyTreeService.build_multi_level(
            title=title,
            root_id=code or "cost-impact",
            root_label=(
                self._route("costImpactSimulation", "treeRootLabel", code=code)
                if code
                else title
            ),
            items=enriched,
            group_keys=["bom_group"],
            leaf_builder=_leaf,
        )

    def build_cost_impact_dashboard_presentation(
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
            self._route("costImpactSimulation", "dashboardTitle", code=code)
            if code
            else self._route("costImpactSimulation", "dashboardTitleGeneric")
        )
        panels: list[dict] = []

        if isinstance(kpi, dict) and kpi.get("type") == "kpi":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="summary",
                    title=str(kpi.get("title") or self._route("costImpactSimulation", "overviewTableTitle")),
                    presentation=kpi,
                )
            )

        if isinstance(chart, dict) and chart.get("type") == "chart":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="chart",
                    title=str(chart.get("title") or self._route("costImpactSimulation", "chartImpactTitleGeneric")),
                    presentation=chart,
                    chart_presentation=chart,
                )
            )

        if isinstance(table, dict) and table.get("type") == "table":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="overview",
                    title=str(table.get("title") or self._route("costImpactSimulation", "overviewTableTitle")),
                    presentation=table,
                )
            )

        return ChatPresentationDashboardAssemblyService.build(title=title, panels=panels, min_panels=2)

    def build_cost_impact_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        code, _description = self._product_context(root, path)
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        simulation = root.get("simulation") if isinstance(root.get("simulation"), dict) else {}
        materials = self._section_block(root, "materials").get("items") or []

        if not isinstance(materials, list) or not materials:
            return None

        title = (
            self._route("costImpactSimulation", "kpiTitle", code=code)
            if code
            else self._route("costImpactSimulation", "kpiTitleGeneric")
        )
        cards: list[dict[str, Any]] = []

        if summary.get("total_material_cost") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("costImpactSimulation", "kpiTotalMaterialCost"),
                    value=float(summary.get("total_material_cost") or 0),
                    unit="R$",
                    color="#10b981",
                    key="total_material_cost",
                )
            )

        if summary.get("total_materials") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("costImpactSimulation", "kpiTotalMaterials"),
                    value=int(summary.get("total_materials") or 0),
                    unit="MP",
                    color="#6366f1",
                    key="total_materials",
                )
            )

        top = materials[0] if isinstance(materials[0], dict) else {}

        if top.get("impact_on_material_cost_percent") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("costImpactSimulation", "kpiTopImpact"),
                    value=float(top.get("impact_on_material_cost_percent") or 0),
                    unit="%",
                    color="#f59e0b",
                    key="top_impact_percent",
                )
            )

        if simulation.get("adjustment_percent") not in (None, "", 0, 0.0):
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("costImpactSimulation", "kpiAdjustmentPercent"),
                    value=float(simulation.get("adjustment_percent") or 0),
                    unit="%",
                    color="#0ea5e9",
                    key="adjustment_percent",
                )
            )

        if simulation.get("projected_cost_delta") is not None:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("costImpactSimulation", "kpiProjectedDelta"),
                    value=float(simulation.get("projected_cost_delta") or 0),
                    unit="R$",
                    color="#8b5cf6",
                    key="projected_cost_delta",
                )
            )

        return ChatPresentationKpiAssemblyService.build(title=title, cards=cards, min_cards=2)

    def build_cost_impact_chart_presentation(self, root: dict, path: str) -> dict | None:
        material_items = self._section_block(root, "materials").get("items")

        if not isinstance(material_items, list) or len(material_items) < 2:
            return None

        impact_label = self._route("costImpactSimulation", "chartImpactLabel")
        chart_data: list[dict[str, Any]] = []

        for item in material_items[:20]:
            if not isinstance(item, dict):
                continue

            code = str(item.get("raw_material_code") or "—")
            chart_data.append(
                {
                    "name": code,
                    impact_label: float(item.get("impact_on_material_cost_percent") or 0),
                }
            )

        if len(chart_data) < 2:
            return None

        code, _description = self._product_context(root, path)

        return {
            "type": "chart",
            "title": (
                self._route("costImpactSimulation", "chartImpactTitle", code=code)
                if code
                else self._route("costImpactSimulation", "chartImpactTitleGeneric")
            ),
            "chartType": "horizontal_bar",
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": [impact_label],
                "colors": ["#f59e0b"],
                "legend": False,
            },
        }

    def build_cost_impact_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_hierarchy_tree_service import (
            ChatPresentationHierarchyTreeService,
        )

        material_items = self._section_block(root, "materials").get("items")

        if not isinstance(material_items, list) or not material_items:
            return None

        enriched = [
            {**item, "bom_group": "materiais"}
            for item in material_items
            if isinstance(item, dict)
        ]

        if not enriched:
            return None

        code, _description = self._product_context(root, path)
        title = (
            self._route("costImpactSimulation", "treeMaterialsTitle", code=code)
            if code
            else self._route("costImpactSimulation", "treeMaterialsTitleGeneric")
        )

        def _leaf(item: dict[str, Any]) -> dict[str, Any]:
            mp_code = str(item.get("raw_material_code") or "—")
            impact = str(item.get("impact_on_material_cost_percent") or "—")

            return ChatPresentationHierarchyTreeService._serialize_node(
                node_id=f"bom:{mp_code}:{item.get('rank')}",
                label=self._route(
                    "costImpactSimulation",
                    "treeMaterialLeafLabel",
                    code=mp_code,
                    impact=impact,
                ),
                subtitle=str(item.get("raw_material_description") or "").strip(),
                meta={
                    "rank": item.get("rank"),
                    "extended_cost": item.get("extended_cost"),
                    "impact_on_pa_cost_percent": item.get("impact_on_pa_cost_percent"),
                },
            )

        return ChatPresentationHierarchyTreeService.build_multi_level(
            title=title,
            root_id=code or "cost-impact",
            root_label=(
                self._route("costImpactSimulation", "treeRootLabel", code=code)
                if code
                else title
            ),
            items=enriched,
            group_keys=["bom_group"],
            leaf_builder=_leaf,
        )

    def build_cost_impact_dashboard_presentation(
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
            self._route("costImpactSimulation", "dashboardTitle", code=code)
            if code
            else self._route("costImpactSimulation", "dashboardTitleGeneric")
        )
        panels: list[dict] = []

        if isinstance(kpi, dict) and kpi.get("type") == "kpi":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="summary",
                    title=str(kpi.get("title") or self._route("costImpactSimulation", "overviewTableTitle")),
                    presentation=kpi,
                )
            )

        if isinstance(chart, dict) and chart.get("type") == "chart":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="chart",
                    title=str(chart.get("title") or self._route("costImpactSimulation", "chartImpactTitleGeneric")),
                    presentation=chart,
                    chart_presentation=chart,
                )
            )

        if isinstance(table, dict) and table.get("type") == "table":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="overview",
                    title=str(table.get("title") or self._route("costImpactSimulation", "overviewTableTitle")),
                    presentation=table,
                )
            )

        return ChatPresentationDashboardAssemblyService.build(title=title, panels=panels, min_panels=2)
