"""Apresentação humanizada — preço de venda do produto (/pricing)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionProductPricingPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _route(self, key: str, **values: str) -> str:
        return self._host._route_presentation("salePricing", key, **values)

    def _product_context(self, root: dict, path: str) -> tuple[str, str, str]:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        code = str(
            product.get("code")
            or product.get("product_code")
            or self._host._extract_product_code_from_path(path)
            or ""
        ).strip()
        description = str(product.get("description") or product.get("product_description") or "").strip()
        unit = str(product.get("unit") or "").strip()

        return code, description, unit

    def _prices(self, root: dict) -> list[dict[str, Any]]:
        prices = root.get("prices")

        if not isinstance(prices, list):
            return []

        return [item for item in prices if isinstance(item, dict)]

    def _present_product_pricing(self, root: dict, path: str) -> dict:
        code, description, _unit = self._product_context(root, path)
        linhas = self._build_pricing_lines(root, code=code, description=description)
        markdown = self._build_pricing_text_presentation(root, path)

        return {
            "titulo": (
                self._route("titleWithCode", code=code)
                if code
                else self._route("titleGeneric")
            ),
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
            "humanizedMarkdown": markdown.get("markdown") if isinstance(markdown, dict) else None,
        }

    def _build_pricing_lines(
        self,
        root: dict,
        *,
        code: str,
        description: str,
    ) -> list[str]:
        linhas: list[str] = []

        if description:
            linhas.append(
                self._route("introWithDescription", code=code, description=description)
            )
        elif code:
            linhas.append(self._route("introCodeOnly", code=code))

        prices = self._prices(root)

        if prices:
            top = prices[0]
            linhas.append(
                self._route(
                    "primarySalePriceLine",
                    table=str(top.get("table_description") or top.get("table_code") or "—"),
                    price=self._host._format_field_value("sale_price", top.get("sale_price")),
                )
            )

            if len(prices) > 1:
                linhas.append(
                    self._route("tablesCountLine", count=str(len(prices)))
                )

        linhas.append(self._route("tableVisualizationHint"))

        return linhas

    def build_product_pricing_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_pricing_overview_table(root, path)

        if overview:
            overview["role"] = "profile"
            tables.append(overview)

        prices = self._prices(root)

        if prices:
            prices_table = self._host._build_items_table(
                prices,
                title=self._route("pricesTableTitle"),
                path=path,
            )
            prices_table["role"] = "list"
            tables.append(prices_table)

        return tables

    def _build_pricing_overview_table(self, root: dict, path: str) -> dict | None:
        code, description, unit = self._product_context(root, path)
        prices = self._prices(root)

        if not prices:
            return None

        sale_values = [float(item.get("sale_price") or 0) for item in prices]
        columns = self._host._column_labels.kv_table_column_defs()
        rows = [
            {
                "campo": self._route("overviewProductField"),
                "valor": f"{code} — {description}".strip(" —") or code or "—",
            },
            {
                "campo": self._route("overviewUnitField"),
                "valor": unit or "—",
            },
            {
                "campo": self._route("overviewTablesField"),
                "valor": str(len(prices)),
            },
            {
                "campo": self._route("overviewMinSalePriceField"),
                "valor": self._host._format_field_value("sale_price", min(sale_values)),
            },
            {
                "campo": self._route("overviewMaxSalePriceField"),
                "valor": self._host._format_field_value("sale_price", max(sale_values)),
            },
        ]

        return {
            "type": "table",
            "title": self._route("overviewTableTitle"),
            "columns": columns,
            "rows": rows,
        }

    def _build_pricing_text_presentation(self, root: dict, path: str) -> dict | None:
        code, _description, _unit = self._product_context(root, path)
        title = (
            self._route("titleWithCode", code=code)
            if code
            else self._route("titleGeneric")
        )
        highlights = self._build_pricing_highlights(root)

        if not highlights:
            return None

        return {
            "type": "markdown",
            "title": title,
            "markdown": f"### {title}\n\n{highlights}".strip(),
        }

    def _build_pricing_highlights(self, root: dict) -> str:
        prices = self._prices(root)

        if not prices:
            return ""

        parts: list[str] = []
        top = prices[0]
        parts.append(
            self._route(
                "primarySalePriceLine",
                table=str(top.get("table_description") or top.get("table_code") or "—"),
                price=self._host._format_field_value("sale_price", top.get("sale_price")),
            )
        )

        if len(prices) > 1:
            parts.append(self._route("tablesCountLine", count=str(len(prices))))

        return "\n\n".join(parts)

    def build_product_pricing_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        code, _description, _unit = self._product_context(root, path)
        prices = self._prices(root)

        if not prices:
            return None

        sale_values = [float(item.get("sale_price") or 0) for item in prices]
        max_values = [float(item.get("max_price") or 0) for item in prices if item.get("max_price") is not None]
        discount_values = [
            float(item.get("discount_percent") or 0)
            for item in prices
            if item.get("discount_percent") not in (None, "", 0, 0.0)
        ]

        title = (
            self._route("kpiTitle", code=code)
            if code
            else self._route("kpiTitleGeneric")
        )
        cards = [
            ChatPresentationKpiAssemblyService.metric_card(
                label=self._route("kpiPrimarySalePrice"),
                value=min(sale_values),
                unit="R$",
                color="#10b981",
                key="primary_sale_price",
            ),
            ChatPresentationKpiAssemblyService.metric_card(
                label=self._route("kpiPriceTables"),
                value=len(prices),
                unit="",
                color="#6366f1",
                key="price_tables",
            ),
        ]

        if max_values:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("kpiMaxSalePrice"),
                    value=max(max_values),
                    unit="R$",
                    color="#0ea5e9",
                    key="max_sale_price",
                )
            )

        if discount_values:
            cards.append(
                ChatPresentationKpiAssemblyService.metric_card(
                    label=self._route("kpiMaxDiscount"),
                    value=max(discount_values),
                    unit="%",
                    color="#f59e0b",
                    key="max_discount_percent",
                )
            )

        return ChatPresentationKpiAssemblyService.build(title=title, cards=cards, min_cards=2)

    def build_product_pricing_chart_presentation(self, root: dict, path: str) -> dict | None:
        prices = self._prices(root)

        if len(prices) < 2:
            return None

        sale_label = self._route("chartSalePriceLabel")
        chart_data: list[dict[str, Any]] = []

        for item in prices[:20]:
            label = str(item.get("table_description") or item.get("table_code") or "—")
            chart_data.append(
                {
                    "name": label,
                    sale_label: float(item.get("sale_price") or 0),
                }
            )

        code, _description, _unit = self._product_context(root, path)

        return {
            "type": "chart",
            "title": (
                self._route("chartSalePriceTitle", code=code)
                if code
                else self._route("chartSalePriceTitleGeneric")
            ),
            "chartType": "horizontal_bar",
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": [sale_label],
                "colors": ["#10b981"],
                "legend": False,
            },
        }

    def build_product_pricing_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_hierarchy_tree_service import (
            ChatPresentationHierarchyTreeService,
        )

        prices = self._prices(root)

        if not prices:
            return None

        enriched = [{**item, "pricing_group": "tabelas"} for item in prices]
        code, _description, _unit = self._product_context(root, path)
        title = (
            self._route("treePricingTitle", code=code)
            if code
            else self._route("treePricingTitleGeneric")
        )

        def _leaf(item: dict[str, Any]) -> dict[str, Any]:
            table = str(item.get("table_description") or item.get("table_code") or "—")
            price = self._host._format_field_value("sale_price", item.get("sale_price"))

            return ChatPresentationHierarchyTreeService._serialize_node(
                node_id=f"price:{item.get('table_code')}:{item.get('state')}",
                label=self._route("treeTableLeafLabel", table=table, price=price),
                subtitle=str(item.get("state") or "").strip(),
                meta={
                    "max_price": item.get("max_price"),
                    "discount_percent": item.get("discount_percent"),
                },
            )

        return ChatPresentationHierarchyTreeService.build_multi_level(
            title=title,
            root_id=code or "product-pricing",
            root_label=(
                self._route("treeRootLabel", code=code)
                if code
                else title
            ),
            items=enriched,
            group_keys=["pricing_group"],
            leaf_builder=_leaf,
        )

    def build_product_pricing_dashboard_presentation(
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

        code, _description, _unit = self._product_context(root, path)
        title = (
            self._route("dashboardTitle", code=code)
            if code
            else self._route("dashboardTitleGeneric")
        )
        panels: list[dict] = []

        if isinstance(kpi, dict) and kpi.get("type") == "kpi":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="summary",
                    title=str(kpi.get("title") or self._route("overviewTableTitle")),
                    presentation=kpi,
                )
            )

        if isinstance(chart, dict) and chart.get("type") == "chart":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="chart",
                    title=str(chart.get("title") or self._route("chartSalePriceTitleGeneric")),
                    presentation=chart,
                    chart_presentation=chart,
                )
            )

        if isinstance(table, dict) and table.get("type") == "table":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="overview",
                    title=str(table.get("title") or self._route("overviewTableTitle")),
                    presentation=table,
                )
            )

        return ChatPresentationDashboardAssemblyService.build(title=title, panels=panels, min_panels=2)
