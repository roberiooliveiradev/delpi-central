"""Apresentação humanizada — preço MP, simulador de custos PA e rotas granulares."""

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
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}
        linhas: list[str] = []

        compact = _Narrative.compact_product_line(
            self._host,
            code=code,
            description=description,
        )

        if compact:
            linhas.append(compact)

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
            tables.append(overview)

        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

        if last_purchase:
            tables.append(self._build_kv_table(last_purchase, self._route("rawMaterialPriceIntelligence", "lastPurchaseTableTitle")))

        price_items = self._section_block(root, "price_history").get("items")

        if isinstance(price_items, list) and price_items:
            tables.append(
                self._host._build_items_table(
                    price_items,
                    title=self._route("rawMaterialPriceIntelligence", "priceHistoryTableTitle"),
                    path=path,
                )
            )

        budget_items = self._section_block(root, "budget_history").get("items")

        if isinstance(budget_items, list) and budget_items:
            tables.append(
                self._host._build_items_table(
                    budget_items,
                    title=self._route("rawMaterialPriceIntelligence", "budgetHistoryTableTitle"),
                    path=path,
                )
            )

        return [table for table in tables if isinstance(table, dict)]

    def build_cost_impact_simulation_table_presentations(
        self,
        root: dict,
        path: str,
    ) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_cost_impact_overview_table(root, path)

        if overview:
            tables.append(overview)

        material_items = self._section_block(root, "materials").get("items")

        if isinstance(material_items, list) and material_items:
            tables.append(
                self._host._build_items_table(
                    material_items,
                    title=self._route("costImpactSimulation", "materialsTableTitle"),
                    path=path,
                )
            )

        return [table for table in tables if isinstance(table, dict)]

    def build_last_purchase_table_presentation(self, root: dict, path: str) -> dict | None:
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

        if not last_purchase:
            return None

        return self._build_kv_table(last_purchase, self._route("lastPurchase", "tableTitle"))

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
