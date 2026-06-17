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

    def _product_unit(self, root: dict) -> str:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        unit = str(product.get("unit") or "").strip()

        return unit or "PA"

    def _section_block(self, root: dict, key: str) -> dict[str, Any]:
        block = root.get(key)

        if isinstance(block, dict):
            return block

        return {}

    def _enrich_history_items(
        self,
        items: list[dict[str, Any]],
        *,
        product_code: str,
    ) -> list[dict[str, Any]]:
        from app.domain.services.chat_presentation_detail_action_service import (
            ChatPresentationDetailActionService,
        )
        from app.domain.services.chat_presentation_supplier_display_service import (
            ChatPresentationSupplierDisplayService,
        )

        enriched: list[dict[str, Any]] = []

        for raw in items:
            if not isinstance(raw, dict):
                continue

            item = ChatPresentationSupplierDisplayService.enrich_item(raw)

            if product_code:
                item["product_code"] = product_code

            document = str(item.get("document_number") or item.get("purchase_order") or "").strip()
            source = str(item.get("source") or "").strip()

            if product_code and document and source:
                item["_detailMeta"] = ChatPresentationDetailActionService.purchase_record_detail_meta(
                    product_code=product_code,
                    document_number=document,
                    source=source,
                    supplier_code=ChatPresentationSupplierDisplayService.supplier_code(item),
                    supplier_store=ChatPresentationSupplierDisplayService.supplier_store(item),
                )

            enriched.append(item)

        return enriched

    def _insight(self, key: str, **values: str) -> str:
        return self._host._presenter_text(
            "compositeAnalysisInsights",
            "rawMaterialPrice",
            key,
            **values,
        )

    def _product_details(self, root: dict) -> dict[str, Any]:
        product = root.get("product")

        if isinstance(product, dict):
            return product

        return {}

    def _indicators(self, root: dict) -> dict[str, Any]:
        indicators = root.get("indicators")

        if isinstance(indicators, dict):
            return indicators

        return {}

    def _normalize_price_history_summary(self, root: dict) -> dict[str, Any]:
        block = self._section_block(root, "price_history")
        summary = block.get("summary") if isinstance(block.get("summary"), dict) else {}
        variation = root.get("price_variation")

        if not isinstance(variation, dict):
            variation = {}

        min_unit_price = summary.get("min_unit_price")
        max_unit_price = summary.get("max_unit_price")
        items = block.get("items") if isinstance(block.get("items"), list) else []

        if items and (min_unit_price is None or max_unit_price is None):
            prices = [
                float(item.get("unit_price"))
                for item in items
                if isinstance(item, dict) and item.get("unit_price") is not None
            ]

            if prices:
                if min_unit_price is None:
                    min_unit_price = min(prices)

                if max_unit_price is None:
                    max_unit_price = max(prices)

        return {
            "total_purchases": summary.get("total_purchases") or summary.get("total_records"),
            "avg_unit_price": summary.get("avg_unit_price") or summary.get("average_unit_price"),
            "min_unit_price": min_unit_price,
            "max_unit_price": max_unit_price,
            "last_variation_percent": (
                summary.get("last_variation_percent")
                or variation.get("last_variation_percent")
            ),
        }

    def _normalize_budget_summary(self, root: dict) -> dict[str, Any]:
        block = self._section_block(root, "budget_history")
        summary = block.get("summary") if isinstance(block.get("summary"), dict) else {}

        return {
            "total_items": summary.get("total_items") or summary.get("total_records"),
            "total_requisitions": summary.get("total_requisitions"),
            "total_purchase_orders": summary.get("total_purchase_orders"),
        }

    def _format_price(self, value: object) -> str:
        if value is None or value == "":
            return "—"

        return self._host._format_field_value("unit_price", value)

    def _registered_price_is_stale(self, product: dict[str, Any], *, diff_percent: float) -> bool:
        registered_date = str(product.get("registered_last_purchase_date") or "").strip()

        if registered_date and len(registered_date) >= 4:
            try:
                year = int(registered_date[:4])

                if year < 2020:
                    return True
            except ValueError:
                pass

        return diff_percent >= 50.0

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

        price_summary = self._normalize_price_history_summary(root)

        if price_summary.get("total_purchases"):
            linhas.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "priceHistorySummaryLine",
                    count=str(price_summary.get("total_purchases")),
                    avg=str(price_summary.get("avg_unit_price") or "—"),
                )
            )

        budget_summary = self._normalize_budget_summary(root)

        if budget_summary.get("total_items"):
            linhas.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "budgetHistorySummaryLine",
                    count=str(budget_summary.get("total_items")),
                )
            )

        indicators = self._indicators(root)

        if indicators.get("dominant_supplier_code"):
            linhas.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "dominantSupplierLine",
                    supplier=str(indicators.get("dominant_supplier_code")),
                    share=str(indicators.get("dominant_supplier_share_percent") or "—"),
                )
            )

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
            purchase_table = _OpsTable.build_items_table(
                self._host.column_label_context,
                [last_purchase],
                profile_name="lastPurchaseDetail",
                title=self._route("rawMaterialPriceIntelligence", "lastPurchaseTableTitle"),
                role="pricing",
            )

            if purchase_table:
                tables.append(purchase_table)

        price_items = self._section_block(root, "price_history").get("items")

        code, _description = self._product_context(root, path)

        if isinstance(price_items, list) and price_items:
            price_dicts = self._enrich_history_items(
                [item for item in price_items if isinstance(item, dict)],
                product_code=code,
            )
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
            history_table = _OpsTable.build_items_table(
                self._host.column_label_context,
                shown,
                profile_name="mpPriceHistoryDetail",
                title=history_title,
                role="list",
            )

            if history_table:
                tables.append(history_table)

        budget_items = self._section_block(root, "budget_history").get("items")

        if isinstance(budget_items, list) and budget_items:
            budget_dicts = self._enrich_history_items(
                [item for item in budget_items if isinstance(item, dict)],
                product_code=code,
            )
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
            budget_table = _OpsTable.build_items_table(
                self._host.column_label_context,
                shown,
                profile_name="purchaseBudgetHistoryDetail",
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
            materials_table = _OpsTable.build_items_table(
                self._host.column_label_context,
                shown,
                path=path,
                profile_name="costImpactMaterials",
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
            detail = _OpsTable.build_items_table(
                self._host.column_label_context,
                [last_purchase],
                profile_name="lastPurchaseDetail",
                title=self._route("lastPurchase", "tableTitle"),
                role="list",
            )

            if detail:
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

        rows.extend(
            _OpsTable.kv_rows_from_mapping(
                self._host.column_label_context,
                {
                    key: last_purchase[key]
                    for key in (
                        "unit_price",
                        "supplier_code",
                        "supplier_name",
                        "icms_rate",
                        "invoice_date",
                    )
                    if key in last_purchase
                },
                path=path,
                profile_name="lastPurchaseOverview",
            )
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
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_kpi(
            self._host,
            root,
            path,
            profile_key="last_purchase"
        )

    def build_last_purchase_chart_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_chart(
            self._host,
            root,
            path,
            profile_key="last_purchase"
        )

    def build_last_purchase_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_tree(
            self._host,
            root,
            path,
            profile_key="last_purchase"
        )

    def build_last_purchase_dashboard_presentation(self, root: dict, path: str, *, kpi: dict | None = None, chart: dict | None = None, table: dict | None = None) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_dashboard(
            self._host,
            root,
            path,
            profile_key="last_purchase",
            kpi=kpi,
            chart=chart,
            table=table
        )

    def _build_intelligence_overview_table(self, root: dict, path: str) -> dict | None:
        code, description = self._product_context(root, path)
        product = self._product_details(root)
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

        product_fields = {
            key: product.get(key)
            for key in (
                "product_type",
                "unit",
                "group_code",
                "standard_cost",
                "registered_last_purchase_price",
                "registered_last_purchase_date",
            )
            if product.get(key) not in (None, "")
        }
        rows.extend(
            _OpsTable.summary_kv_rows(
                self._host.column_label_context,
                product_fields,
                path=path,
                profile_name="rawMaterialPriceOverview",
            )
        )

        price_summary = self._normalize_price_history_summary(root)
        rows.extend(
            _OpsTable.summary_kv_rows(
                self._host.column_label_context,
                {
                    key: price_summary[key]
                    for key in (
                        "total_purchases",
                        "avg_unit_price",
                        "min_unit_price",
                        "max_unit_price",
                        "last_variation_percent",
                    )
                    if price_summary.get(key) not in (None, "")
                },
                path=path,
                profile_name="rawMaterialPriceOverview",
            )
        )

        indicators = self._indicators(root)

        rows.extend(
            _OpsTable.summary_kv_rows(
                self._host.column_label_context,
                indicators,
                path=path,
                profile_name="rawMaterialPriceOverview",
            )[:6]
        )

        return {
            "type": "table",
            "title": self._route("rawMaterialPriceIntelligence", "overviewTableTitle"),
            "columns": columns,
            "rows": rows,
        }

    def _build_cost_impact_overview_table(self, root: dict, path: str) -> dict | None:
        code, description = self._product_context(root, path)
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        simulation = root.get("simulation") if isinstance(root.get("simulation"), dict) else {}
        columns = self._host._column_labels.kv_table_column_defs()
        rows = [
            {
                "campo": self._route("costImpactSimulation", "overviewProductField"),
                "valor": f"{code} — {description}".strip(" —") or code or "—",
            },
        ]
        merged: dict[str, Any] = {}
        skip_product = {"product_code", "code", "description"}

        for key, value in product.items():
            if str(key) in skip_product or value in (None, ""):
                continue

            merged[str(key)] = value

        for block in (summary, simulation):
            for key, value in block.items():
                if value in (None, ""):
                    continue

                merged[str(key)] = value

        rows.extend(
            _OpsTable.summary_kv_rows(
                self._host.column_label_context,
                merged,
                path=path,
                profile_name="costImpactOverview",
            )
        )

        return {
            "type": "table",
            "title": self._route("costImpactSimulation", "overviewTableTitle"),
            "columns": columns,
            "rows": rows,
        }

    def _build_kv_table(self, payload: dict, title: str, *, path: str = "") -> dict:
        columns = self._host._column_labels.kv_table_column_defs()

        return {
            "type": "table",
            "title": title,
            "columns": columns,
            "rows": _OpsTable.kv_rows_from_mapping(
                self._host.column_label_context,
                payload,
                path=path,
            ),
        }

    def _build_intelligence_text_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_rich_presentation_text_service import (
            ChatRichPresentationTextService,
        )

        code, description = self._product_context(root, path)
        title = (
            self._route("rawMaterialPriceIntelligence", "titleWithCode", code=code)
            if code
            else self._route("rawMaterialPriceIntelligence", "titleGeneric")
        )
        auxiliary_tables = self.build_raw_material_price_intelligence_table_presentations(
            root,
            path,
        )
        compact_for_rich_ui = ChatRichPresentationTextService.should_compact_narrative(
            table_presentations=auxiliary_tables,
        )
        body = self._build_intelligence_markdown_body(
            root,
            code=code,
            description=description,
            compact_for_rich_ui=compact_for_rich_ui,
        )

        if not body:
            return None

        return {
            "type": "markdown",
            "title": title,
            "markdown": f"### {title}\n\n{body}".strip(),
        }

    def _build_intelligence_markdown_body(
        self,
        root: dict,
        *,
        code: str,
        description: str,
        compact_for_rich_ui: bool = False,
    ) -> str:
        parts: list[str | None] = []
        parts.extend(
            self._build_intelligence_narrative_sections(
                root,
                code=code,
                description=description,
                compact_for_rich_ui=compact_for_rich_ui,
            )
        )

        highlights = self._build_intelligence_highlight_lines(root)

        if highlights:
            parts.append(self._insight("highlightsHeader"))
            parts.extend(f"- {line}" for line in highlights)

        attention = self._build_intelligence_attention_lines(root)

        if attention:
            parts.append(self._insight("attentionHeader"))
            parts.extend(f"{index}. {line}" for index, line in enumerate(attention, start=1))

        recommendation = self._build_intelligence_recommendation_lines(root)

        if recommendation:
            parts.extend(recommendation)

        return _OpsTable.join_markdown_blocks(parts)

    def _build_intelligence_narrative_sections(
        self,
        root: dict,
        *,
        code: str,
        description: str,
        compact_for_rich_ui: bool,
    ) -> list[str]:
        sections: list[str] = []
        product = self._product_details(root)
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}
        price_summary = self._normalize_price_history_summary(root)
        indicators = self._indicators(root)
        route = "rawMaterialPriceIntelligence"

        product_lines: list[str] = [
            self._route(route, "sectionProductSummaryHeader"),
            self._route(route, "productCodeLine", code=code or "—"),
        ]

        if description:
            product_lines.append(
                self._route(route, "productDescriptionLine", description=description)
            )

        product_type = str(product.get("product_type") or "").strip()
        unit = str(product.get("unit") or "").strip()

        if product_type or unit:
            product_lines.append(
                self._route(
                    route,
                    "productTypeLine",
                    type=product_type or "—",
                    unit=unit or "—",
                )
            )

        group_code = str(product.get("group_code") or "").strip()

        if group_code:
            product_lines.append(self._route(route, "productGroupLine", group=group_code))

        registered_price = product.get("registered_last_purchase_price")

        if registered_price is not None:
            product_lines.append(
                self._route(
                    route,
                    "registeredPriceLine",
                    price=self._format_price(registered_price),
                )
            )

        registered_date = str(product.get("registered_last_purchase_date") or "").strip()

        if registered_date:
            product_lines.append(
                self._route(
                    route,
                    "registeredDateLine",
                    date=self._host._format_field_value(
                        "registered_last_purchase_date",
                        registered_date,
                    ),
                )
            )

        sections.append("\n".join(product_lines))

        price_status = str(root.get("price_status") or "").strip()

        if price_status:
            sections.append(self._insight("headlinePriceStatus", status=price_status))

        if last_purchase and not compact_for_rich_ui:
            last_lines = [self._route(route, "sectionLastPurchaseHeader")]

            if last_purchase.get("invoice_number") or last_purchase.get("issue_date"):
                last_lines.append(
                    self._route(
                        route,
                        "lastPurchaseNfLine",
                        invoice=str(last_purchase.get("invoice_number") or "—"),
                        series=str(last_purchase.get("invoice_series") or "—"),
                        issueDate=self._host._format_field_value(
                            "issue_date",
                            last_purchase.get("issue_date"),
                        ),
                        entryDate=self._host._format_field_value(
                            "entry_date",
                            last_purchase.get("entry_date"),
                        ),
                    )
                )

            if last_purchase.get("supplier_name") or last_purchase.get("quantity") is not None:
                last_lines.append(
                    self._route(
                        route,
                        "lastPurchaseSupplierLine",
                        supplier=str(
                            last_purchase.get("supplier_name")
                            or last_purchase.get("supplier_code")
                            or "—"
                        ),
                        quantity=self._host._format_field_value(
                            "quantity",
                            last_purchase.get("quantity"),
                        ),
                    )
                )

            if last_purchase.get("unit_price") is not None:
                last_lines.append(
                    self._route(
                        route,
                        "lastPurchaseAmountLine",
                        unitPrice=self._format_price(last_purchase.get("unit_price")),
                        totalValue=self._host._format_field_value(
                            "total_value",
                            last_purchase.get("total_value"),
                        ),
                        icmsRate=str(last_purchase.get("icms_rate") or "—"),
                    )
                )

            if last_purchase.get("purchase_order") or last_purchase.get("supplier_part_number"):
                last_lines.append(
                    self._route(
                        route,
                        "lastPurchasePoLine",
                        purchaseOrder=str(last_purchase.get("purchase_order") or "—"),
                        partNumber=str(last_purchase.get("supplier_part_number") or "—"),
                    )
                )

            sections.append("\n".join(last_lines))
        elif last_purchase and compact_for_rich_ui:
            sections.append(
                self._route(
                    route,
                    "lastPurchaseLine",
                    price=str(last_purchase.get("unit_price") or "—"),
                    supplier=str(
                        last_purchase.get("supplier_name")
                        or last_purchase.get("supplier_code")
                        or "—"
                    ),
                )
            )

        diff_percent = indicators.get("registered_vs_last_nf_diff_percent")

        if diff_percent is not None:
            variation_lines = [self._route(route, "sectionPriceVariationHeader")]
            variation_lines.append(
                self._route(
                    route,
                    "registeredVsLastLine",
                    diffPercent=self._host._format_field_value(
                        "registered_vs_last_nf_diff_percent",
                        diff_percent,
                    ),
                    registeredPrice=self._format_price(
                        product.get("registered_last_purchase_price")
                        or product.get("standard_cost"),
                    ),
                )
            )

            if self._registered_price_is_stale(
                product,
                diff_percent=float(diff_percent or 0),
            ):
                variation_lines.append(
                    self._route(
                        route,
                        "registeredVsLastStaleLine",
                        registeredDate=self._host._format_field_value(
                            "registered_last_purchase_date",
                            registered_date or "—",
                        ),
                    )
                )

            sections.append("\n".join(variation_lines))

        if price_summary.get("total_purchases") and not compact_for_rich_ui:
            history_lines = [self._route(route, "sectionPriceHistoryHeader")]
            history_lines.append(
                self._route(
                    route,
                    "priceHistoryStatsLine",
                    minPrice=self._format_price(price_summary.get("min_unit_price")),
                    maxPrice=self._format_price(price_summary.get("max_unit_price")),
                    avgPrice=self._format_price(price_summary.get("avg_unit_price")),
                    count=str(price_summary.get("total_purchases")),
                )
            )

            if price_summary.get("last_variation_percent") is not None:
                history_lines.append(
                    self._route(
                        route,
                        "lastVariationLine",
                        variation=self._host._format_field_value(
                            "variation_percent",
                            price_summary.get("last_variation_percent"),
                        ),
                    )
                )

            sections.append("\n".join(history_lines))
        elif price_summary.get("total_purchases"):
            sections.append(
                self._route(
                    route,
                    "priceHistorySummaryLine",
                    count=str(price_summary.get("total_purchases")),
                    avg=str(price_summary.get("avg_unit_price") or "—"),
                )
            )

        if indicators.get("dominant_supplier_code"):
            supplier_label = str(
                last_purchase.get("supplier_name")
                or indicators.get("dominant_supplier_code")
                or "—"
            )
            dominant_lines = [
                self._route(route, "sectionDominantSupplierHeader"),
                self._route(
                    route,
                    "dominantSupplierDetailLine",
                    supplier=supplier_label,
                    share=str(indicators.get("dominant_supplier_share_percent") or "—"),
                ),
            ]
            sections.append("\n".join(dominant_lines))

        history_reading = self._build_intelligence_history_reading_lines(
            root,
            code=code,
            description=description,
        )

        if history_reading:
            sections.append("\n".join(history_reading))

        return sections

    def _build_intelligence_history_reading_lines(
        self,
        root: dict,
        *,
        code: str,
        description: str,
    ) -> list[str]:
        price_summary = self._normalize_price_history_summary(root)
        indicators = self._indicators(root)
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}
        min_price = price_summary.get("min_unit_price")
        max_price = price_summary.get("max_unit_price")
        route = "rawMaterialPriceIntelligence"

        if min_price is None or max_price is None:
            return []

        try:
            min_value = float(min_price)
            max_value = float(max_price)
        except (TypeError, ValueError):
            return []

        if min_value <= 0:
            return []

        spread_percent = self._host._format_field_value(
            "variation_percent",
            ((max_value - min_value) / min_value) * 100,
        )
        lines = [self._route(route, "sectionHistoryReadingHeader")]
        lines.append(
            self._route(
                route,
                "historyReadingRangeLine",
                minPrice=self._format_price(min_value),
                maxPrice=self._format_price(max_value),
                spreadPercent=str(spread_percent),
            )
        )

        dominant_code = str(indicators.get("dominant_supplier_code") or "").strip()
        dominant_share = indicators.get("dominant_supplier_share_percent")

        if dominant_code and dominant_share is not None:
            supplier_label = str(
                last_purchase.get("supplier_name") or dominant_code or "—"
            )
            lines.append(
                self._route(
                    route,
                    "historyReadingDominantLine",
                    supplier=supplier_label,
                    share=self._host._format_field_value(
                        "dominant_supplier_share_percent",
                        dominant_share,
                    ),
                )
            )

        return lines

    def _build_intelligence_highlight_lines(self, root: dict) -> list[str]:
        highlights: list[str] = []
        price_summary = self._normalize_price_history_summary(root)
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}

        if last_purchase.get("unit_price") is not None:
            highlights.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "lastPurchaseLine",
                    price=str(last_purchase.get("unit_price")),
                    supplier=str(
                        last_purchase.get("supplier_name")
                        or last_purchase.get("supplier_code")
                        or "—"
                    ),
                )
            )

        if price_summary.get("avg_unit_price") is not None:
            highlights.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "priceHistoryStatsLine",
                    minPrice=self._format_price(price_summary.get("min_unit_price")),
                    maxPrice=self._format_price(price_summary.get("max_unit_price")),
                    avgPrice=self._format_price(price_summary.get("avg_unit_price")),
                    count=str(price_summary.get("total_purchases") or "—"),
                )
            )

        return highlights

    def _build_intelligence_attention_lines(self, root: dict) -> list[str]:
        attention: list[str] = []
        product = self._product_details(root)
        indicators = self._indicators(root)
        price_summary = self._normalize_price_history_summary(root)
        price_status = str(root.get("price_status") or "").strip().upper()
        diff_percent = float(indicators.get("registered_vs_last_nf_diff_percent") or 0)
        last_variation = price_summary.get("last_variation_percent")

        if price_status == "ALTA DE PRECO" and last_variation is not None:
            attention.append(
                self._insight(
                    "attentionPriceIncrease",
                    variation=self._host._format_field_value(
                        "variation_percent",
                        last_variation,
                    ),
                )
            )

        registered_price = product.get("registered_last_purchase_price") or product.get(
            "standard_cost"
        )
        registered_date = str(product.get("registered_last_purchase_date") or "").strip()

        if self._registered_price_is_stale(product, diff_percent=diff_percent):
            attention.append(
                self._insight(
                    "attentionStaleRegistered",
                    registeredPrice=self._format_price(registered_price),
                    registeredDate=self._host._format_field_value(
                        "registered_last_purchase_date",
                        registered_date or "—",
                    ),
                    minPrice=self._format_price(price_summary.get("min_unit_price")),
                    maxPrice=self._format_price(price_summary.get("max_unit_price")),
                )
            )
        elif diff_percent >= 20:
            attention.append(
                self._insight(
                    "attentionRegisteredGap",
                    diffPercent=self._host._format_field_value(
                        "registered_vs_last_nf_diff_percent",
                        diff_percent,
                    ),
                )
            )

        warnings = root.get("warnings")

        if isinstance(warnings, list):
            for item in warnings:
                text = str(item).strip()

                if text:
                    attention.append(text)

        return attention

    def _build_intelligence_recommendation_lines(self, root: dict) -> list[str]:
        last_purchase = root.get("last_purchase") if isinstance(root.get("last_purchase"), dict) else {}
        price_summary = self._normalize_price_history_summary(root)
        lines: list[str] = []

        if last_purchase.get("unit_price") is None and price_summary.get("avg_unit_price") is None:
            return lines

        lines.append(self._route("rawMaterialPriceIntelligence", "recommendationHeader"))

        if last_purchase.get("unit_price") is not None:
            lines.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "recommendationConservativeLine",
                    lastPrice=self._format_price(last_purchase.get("unit_price")),
                )
            )

        if price_summary.get("avg_unit_price") is not None:
            lines.append(
                self._route(
                    "rawMaterialPriceIntelligence",
                    "recommendationAverageLine",
                    avgPrice=self._format_price(price_summary.get("avg_unit_price")),
                )
            )

        return lines

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
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_kpi(
            self._host,
            root,
            path,
            profile_key="raw_material_price_intelligence"
        )

    def build_raw_material_price_chart_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_chart(
            self._host,
            root,
            path,
            profile_key="raw_material_price_intelligence"
        )

    def build_raw_material_price_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_tree(
            self._host,
            root,
            path,
            profile_key="raw_material_price_intelligence"
        )

    def build_raw_material_price_dashboard_presentation(self, root: dict, path: str, *, kpi: dict | None = None, tree: dict | None = None, chart: dict | None = None, table: dict | None = None) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_dashboard(
            self._host,
            root,
            path,
            profile_key="raw_material_price_intelligence",
            kpi=kpi,
            tree=tree,
            chart=chart,
            table=table
        )

    def build_cost_impact_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_kpi(
            self._host,
            root,
            path,
            profile_key="cost_impact_simulation"
        )

    def build_cost_impact_chart_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_chart(
            self._host,
            root,
            path,
            profile_key="cost_impact_simulation"
        )

    def build_cost_impact_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_tree(
            self._host,
            root,
            path,
            profile_key="cost_impact_simulation"
        )

    def build_cost_impact_dashboard_presentation(self, root: dict, path: str, *, kpi: dict | None = None, chart: dict | None = None, table: dict | None = None) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_dashboard(
            self._host,
            root,
            path,
            profile_key="cost_impact_simulation",
            kpi=kpi,
            chart=chart,
            table=table
        )
