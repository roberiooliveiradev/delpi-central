"""Apresentação humanizada — preço de venda do produto (/pricing)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)

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
            shown, total = _OpsTable.limit_items(prices, sort_key="table_code", reverse=False)
            title = (
                self._route(
                    "pricesTableTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("pricesTableTitle")
            )
            prices_table = _OpsTable.build_fixed_items_table(
                self._host,
                shown,
                table_id="salePricingDetail",
                title=title,
                role="list",
            )

            if prices_table:
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
        code, description, unit = self._product_context(root, path)
        title = (
            self._route("titleWithCode", code=code)
            if code
            else self._route("titleGeneric")
        )
        body = self._build_pricing_markdown_body(
            root,
            code=code,
            description=description,
            unit=unit,
        )

        if not body:
            return None

        intro = (
            self._route("introWithDescription", code=code, description=description)
            if description
            else self._route("introCodeOnly", code=code)
            if code
            else ""
        )
        markdown_parts = [f"### {title}", "", "<!-- section:scope -->", ""]

        if intro:
            markdown_parts.append(intro)

        markdown_parts.append("")
        markdown_parts.append(body)

        return {
            "type": "markdown",
            "title": title,
            "markdown": "\n".join(markdown_parts).strip(),
        }

    def _price_extremes(self, prices: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
        ordered = sorted(prices, key=lambda item: float(item.get("sale_price") or 0))
        return ordered[0], ordered[-1]

    def _build_pricing_markdown_body(
        self,
        root: dict,
        *,
        code: str,
        description: str,
        unit: str,
    ) -> str:
        prices = self._prices(root)

        if not prices:
            return ""

        parts: list[str | None] = []
        min_item, max_item = self._price_extremes(prices)
        min_price = float(min_item.get("sale_price") or 0)
        max_price = float(max_item.get("sale_price") or 0)
        panorama_lines = [self._route("sectionPanoramaHeader")]

        if description or unit:
            panorama_lines.append(
                self._route(
                    "panoramaProductLine",
                    code=code or "—",
                    description=description or "—",
                    unit=unit or "—",
                    count=str(len(prices)),
                )
            )

        panorama_lines.append(
            self._route(
                "panoramaMinLine",
                price=self._host._format_field_value("sale_price", min_price),
                tableCode=str(min_item.get("table_code") or "—"),
                table=str(min_item.get("table_description") or min_item.get("table_code") or "—"),
            )
        )

        if len(prices) > 1:
            panorama_lines.append(
                self._route(
                    "panoramaMaxLine",
                    price=self._host._format_field_value("sale_price", max_price),
                    tableCode=str(max_item.get("table_code") or "—"),
                    table=str(max_item.get("table_description") or max_item.get("table_code") or "—"),
                )
            )

            delta = max_price - min_price
            percent = (delta / min_price * 100) if min_price else 0.0
            panorama_lines.append(
                self._route(
                    "panoramaRangeLine",
                    delta=self._host._format_field_value("sale_price", delta),
                    percent=self._host._format_field_value("discount_percent", round(percent, 1)),
                )
            )

        parts.append("\n".join(panorama_lines))

        reading_lines = [self._route("sectionQuickReadingHeader")]

        if len(prices) > 1:
            reading_lines.append(
                self._route(
                    "quickReadingEscalationLine",
                    tableCode=str(min_item.get("table_code") or "—"),
                )
            )
        else:
            reading_lines.append(self._route("quickReadingSingleTableLine"))

        parts.append("\n".join(reading_lines))

        attention = self._build_pricing_attention_lines(prices)

        if attention:
            parts.append(self._route("attentionHeader"))
            parts.extend(f"{index}. {line}" for index, line in enumerate(attention, start=1))

        parts.append(
            self._route(
                "conclusionHeader",
            )
        )
        parts.append(
            self._route(
                "conclusionEntryPrice",
                code=code or "—",
                price=self._host._format_field_value("sale_price", min_price),
            )
        )

        return _OpsTable.join_markdown_blocks(parts)

    def _build_pricing_attention_lines(self, prices: list[dict[str, Any]]) -> list[str]:
        lines: list[str] = []

        if prices and all(float(item.get("max_price") or 0) == 0 for item in prices):
            lines.append(self._route("attentionZeroMaxPrice"))

        if prices and all(float(item.get("discount_percent") or 0) == 0 for item in prices):
            lines.append(self._route("attentionNoDiscount"))

        validity_dates = [
            str(item.get("valid_from") or "").strip()
            for item in prices
            if str(item.get("valid_from") or "").strip()
        ]

        if validity_dates and min(validity_dates) < "20200101":
            lines.append(
                self._route(
                    "attentionOldValidity",
                    date=self._host._format_field_value("valid_from", min(validity_dates)),
                )
            )

        return lines

    def build_product_pricing_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_kpi(
            self._host,
            root,
            path,
            profile_key="sale_pricing"
        )

    def build_product_pricing_chart_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_chart(
            self._host,
            root,
            path,
            profile_key="sale_pricing"
        )

    def build_product_pricing_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_tree(
            self._host,
            root,
            path,
            profile_key="sale_pricing"
        )

    def build_product_pricing_dashboard_presentation(self, root: dict, path: str, *, kpi: dict | None = None, chart: dict | None = None, table: dict | None = None) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_dashboard(
            self._host,
            root,
            path,
            profile_key="sale_pricing",
            kpi=kpi,
            chart=chart,
            table=table
        )
