"""Histórico de preço de compra e orçamento SC/PC — perfil generalizável."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionProductPurchaseHistoryPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _route_namespace(self, path: str) -> str:
        lowered = str(path or "").lower()

        if "purchase-budget-history" in lowered:
            return "purchaseBudgetHistory"

        return "purchasePriceHistory"

    def _route(self, path: str, key: str, **values: str) -> str:
        return self._host._route_presentation(self._route_namespace(path), key, **values)

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

    def _summary(self, root: dict) -> dict:
        summary = root.get("summary")

        if isinstance(summary, dict):
            return summary

        return {}

    def _items(self, root: dict) -> list:
        items = root.get("items")

        if isinstance(items, list):
            return items

        return []

    def _present_purchase_history(self, root: dict, path: str) -> dict:
        code, description = self._product_context(root, path)
        markdown = self._build_purchase_history_text_presentation(root, path)
        linhas = []

        if isinstance(markdown, dict) and markdown.get("markdown"):
            linhas = [
                line
                for line in str(markdown["markdown"]).splitlines()
                if line.strip() and not line.startswith("###")
            ]

        if not linhas:
            summary = self._summary(root)
            items = self._items(root)

            if summary:
                for key, value in list(summary.items())[:6]:
                    linhas.append(
                        f"{self._host._humanize_key(str(key))}: "
                        f"{self._host._format_field_value(str(key), value)}"
                    )

            if items:
                linhas.append(
                    self._host._presenter_text(
                        "playbookReports",
                        "itemsReturnedLine",
                        count=str(len(items)),
                    )
                )

        title = (
            self._route(path, "titleWithCode", code=code)
            if code
            else self._route(path, "titleGeneric")
        )

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
            "humanizedMarkdown": markdown.get("markdown") if isinstance(markdown, dict) else None,
        }

    def _build_purchase_history_text_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_rich_presentation_text_service import (
            ChatRichPresentationTextService,
        )

        code, description = self._product_context(root, path)
        title = (
            self._route(path, "titleWithCode", code=code)
            if code
            else self._route(path, "titleGeneric")
        )
        auxiliary_tables = self.build_purchase_history_table_presentations(root, path)
        compact_for_rich_ui = ChatRichPresentationTextService.should_compact_narrative(
            table_presentations=auxiliary_tables,
        )
        body = self._build_markdown_body(
            root,
            path=path,
            code=code,
            description=description,
            compact_for_rich_ui=compact_for_rich_ui,
        )

        if not body:
            return None

        markdown_parts = [f"### {title}", "", body]

        return {
            "type": "markdown",
            "title": title,
            "markdown": "\n".join(markdown_parts).strip(),
        }

    def _build_markdown_body(
        self,
        root: dict,
        *,
        path: str,
        code: str,
        description: str,
        compact_for_rich_ui: bool,
    ) -> str:
        parts: list[str] = []
        summary = self._summary(root)
        items = self._items(root)

        if compact_for_rich_ui and code:
            parts.append(self._route(path, "tableVisualizationHint"))
        elif description:
            parts.append(
                self._route(
                    path,
                    "introWithDescription",
                    code=code,
                    description=description,
                )
            )
        elif code:
            parts.append(self._route(path, "introCodeOnly", code=code))

        if self._route_namespace(path) == "purchasePriceHistory":
            if summary.get("avg_unit_price") is not None:
                parts.append(
                    self._route(
                        path,
                        "avgPriceLine",
                        value=str(summary.get("avg_unit_price")),
                    )
                )

            if summary.get("last_variation_percent") is not None:
                parts.append(
                    self._route(
                        path,
                        "variationLine",
                        value=str(summary.get("last_variation_percent")),
                    )
                )
        else:
            if summary.get("total_requisitions") is not None:
                parts.append(
                    self._route(
                        path,
                        "requisitionsLine",
                        count=str(summary.get("total_requisitions")),
                    )
                )

            if summary.get("total_purchase_orders") is not None:
                parts.append(
                    self._route(
                        path,
                        "purchaseOrdersLine",
                        count=str(summary.get("total_purchase_orders")),
                    )
                )

        if items:
            parts.append(
                self._route(path, "itemsPreviewLine", count=str(len(items)))
            )
        else:
            parts.append(self._route(path, "itemsEmptyLine"))

        return _OpsTable.join_narrative_lines(parts)

    def build_purchase_history_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_overview_table(root, path)

        if overview:
            overview["role"] = "profile"
            tables.append(overview)

        items = [item for item in self._items(root) if isinstance(item, dict)]

        if items:
            shown, total = _OpsTable.limit_items(items, sort_key="issue_date")
            title = (
                self._route(
                    path,
                    "itemsTableTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route(path, "itemsTableTitle")
            )
            table_id = (
                "purchaseBudgetHistoryDetail"
                if self._route_namespace(path) == "purchaseBudgetHistory"
                else "mpPriceHistoryDetail"
            )
            table = _OpsTable.build_fixed_items_table(
                self._host,
                shown,
                table_id=table_id,
                title=title,
                role="list",
            )

            if table:
                tables.append(table)

        return [table for table in tables if isinstance(table, dict)]

    def _build_overview_table(self, root: dict, path: str) -> dict | None:
        summary = self._summary(root)

        if not summary:
            return None

        columns = self._host._column_labels.kv_table_column_defs()
        rows = [
            {
                "campo": self._host._humanize_key(str(key)),
                "valor": self._host._format_field_value(str(key), value),
            }
            for key, value in summary.items()
        ]

        period_start = str(root.get("date_start") or "").strip()
        period_end = str(root.get("date_end_exclusive") or "").strip()

        if period_start and period_end:
            rows.insert(
                0,
                {
                    "campo": "Período",
                    "valor": f"{period_start} até {period_end} (fim exclusivo)",
                },
            )

        return {
            "type": "table",
            "title": self._route(path, "overviewTableTitle"),
            "columns": columns,
            "rows": rows,
            "role": "profile",
        }

    def build_purchase_history_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        code, _description = self._product_context(root, path)
        summary = self._summary(root)
        items = self._items(root)

        if not summary and not items:
            return None

        title = (
            self._route(path, "kpiTitle", code=code)
            if code
            else self._route(path, "kpiTitleGeneric")
        )
        cards: list[dict[str, Any]] = []
        namespace = self._route_namespace(path)

        if namespace == "purchasePriceHistory":
            if summary.get("total_purchases") is not None:
                cards.append(
                    ChatPresentationKpiAssemblyService.metric_card(
                        label=self._route(path, "kpiTotalPurchases"),
                        value=int(summary.get("total_purchases") or 0),
                        unit="NF",
                        color="#6366f1",
                        key="total_purchases",
                    )
                )

            if summary.get("avg_unit_price") is not None:
                cards.append(
                    ChatPresentationKpiAssemblyService.metric_card(
                        label=self._route(path, "kpiAvgPrice"),
                        value=float(summary.get("avg_unit_price") or 0),
                        unit="R$",
                        color="#10b981",
                        key="avg_unit_price",
                    )
                )

            if summary.get("last_variation_percent") is not None:
                cards.append(
                    ChatPresentationKpiAssemblyService.metric_card(
                        label=self._route(path, "kpiLastVariation"),
                        value=float(summary.get("last_variation_percent") or 0),
                        unit="%",
                        color="#f59e0b",
                        key="last_variation_percent",
                    )
                )
        else:
            if summary.get("total_items") is not None:
                cards.append(
                    ChatPresentationKpiAssemblyService.metric_card(
                        label=self._route(path, "kpiTotalItems"),
                        value=int(summary.get("total_items") or 0),
                        unit="",
                        color="#6366f1",
                        key="total_items",
                    )
                )

            if summary.get("total_requisitions") is not None:
                cards.append(
                    ChatPresentationKpiAssemblyService.metric_card(
                        label=self._route(path, "kpiRequisitions"),
                        value=int(summary.get("total_requisitions") or 0),
                        unit="SC",
                        color="#0ea5e9",
                        key="total_requisitions",
                    )
                )

            if summary.get("total_purchase_orders") is not None:
                cards.append(
                    ChatPresentationKpiAssemblyService.metric_card(
                        label=self._route(path, "kpiPurchaseOrders"),
                        value=int(summary.get("total_purchase_orders") or 0),
                        unit="PC",
                        color="#8b5cf6",
                        key="total_purchase_orders",
                    )
                )

        return ChatPresentationKpiAssemblyService.build(title=title, cards=cards, min_cards=2)

    def build_purchase_history_chart_presentation(self, root: dict, path: str) -> dict | None:
        items = [item for item in self._items(root) if isinstance(item, dict)]

        if len(items) < 2:
            return None

        code, _description = self._product_context(root, path)
        namespace = self._route_namespace(path)

        if namespace == "purchasePriceHistory":
            unit_label = self._route(path, "chartUnitPriceLabel")
            chart_data: list[dict[str, Any]] = []

            for index, item in enumerate(items[:20], start=1):
                supplier = str(item.get("supplier_code") or "").strip()
                label = supplier or f"#{index}"
                chart_data.append(
                    {
                        "name": label,
                        unit_label: float(item.get("unit_price") or 0),
                    }
                )

            return {
                "type": "chart",
                "title": (
                    self._route(path, "chartTitle", code=code)
                    if code
                    else self._route(path, "chartTitleGeneric")
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

        quantity_label = self._host._humanize_key("unit_price")
        chart_data = []

        for item in items[:20]:
            source = str(item.get("source") or "—")
            chart_data.append(
                {
                    "name": source,
                    quantity_label: float(item.get("unit_price") or 0),
                }
            )

        if len(chart_data) < 2:
            return None

        return {
            "type": "chart",
            "title": (
                self._route(path, "chartTitle", code=code)
                if code
                else self._route(path, "chartTitleGeneric")
            ),
            "chartType": "horizontal_bar",
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": [quantity_label],
                "colors": ["#8b5cf6"],
                "legend": False,
            },
        }

    def build_purchase_history_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_hierarchy_tree_service import (
            ChatPresentationHierarchyTreeService,
        )

        items = [item for item in self._items(root) if isinstance(item, dict)]

        if not items:
            return None

        code, _description = self._product_context(root, path)
        namespace = self._route_namespace(path)
        title = (
            self._route(path, "treeTitle", code=code)
            if code
            else self._route(path, "treeTitleGeneric")
        )
        group_keys = ["supplier_code"] if namespace == "purchasePriceHistory" else ["source"]

        def _leaf(item: dict[str, Any]) -> dict[str, Any]:
            if namespace == "purchasePriceHistory":
                supplier = str(item.get("supplier_code") or "—")
                price = str(item.get("unit_price") or "—")

                return ChatPresentationHierarchyTreeService._serialize_node(
                    node_id=f"nf:{supplier}:{price}",
                    label=self._route(path, "treePriceLeafLabel", supplier=supplier, price=price),
                    subtitle=str(item.get("variation_percent") or "").strip(),
                )

            source = str(item.get("source") or "—")
            document = str(item.get("document_number") or item.get("purchase_order") or "—")

            return ChatPresentationHierarchyTreeService._serialize_node(
                node_id=f"budget:{source}:{document}",
                label=self._route(path, "treeBudgetLeafLabel", source=source, document=document),
                subtitle=str(item.get("supplier_code") or "").strip(),
            )

        return ChatPresentationHierarchyTreeService.build_multi_level(
            title=title,
            root_id=code or "purchase-history",
            root_label=(
                self._route(path, "treeRootLabel", code=code)
                if code
                else title
            ),
            items=items,
            group_keys=group_keys,
            leaf_builder=_leaf,
        )

    def build_purchase_history_dashboard_presentation(
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
            self._route(path, "dashboardTitle", code=code)
            if code
            else self._route(path, "dashboardTitleGeneric")
        )
        panels: list[dict] = []

        if isinstance(kpi, dict) and kpi.get("type") == "kpi":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="summary",
                    title=str(kpi.get("title") or self._route(path, "overviewTableTitle")),
                    presentation=kpi,
                )
            )

        if isinstance(chart, dict) and chart.get("type") == "chart":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="chart",
                    title=str(chart.get("title") or self._route(path, "chartTitleGeneric")),
                    presentation=chart,
                    chart_presentation=chart,
                )
            )

        if isinstance(table, dict) and table.get("type") == "table":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="detail",
                    title=str(table.get("title") or self._route(path, "itemsTableTitle")),
                    presentation=table,
                )
            )

        return ChatPresentationDashboardAssemblyService.build(title=title, panels=panels, min_panels=2)
