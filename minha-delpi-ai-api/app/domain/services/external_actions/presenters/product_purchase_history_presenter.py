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

    def _enriched_items(self, root: dict, path: str) -> list[dict[str, Any]]:
        from app.domain.services.chat_presentation_detail_action_service import (
            ChatPresentationDetailActionService,
        )
        from app.domain.services.chat_presentation_supplier_display_service import (
            ChatPresentationSupplierDisplayService,
        )

        code, _description = self._product_context(root, path)
        enriched: list[dict[str, Any]] = []

        for raw in self._items(root):
            if not isinstance(raw, dict):
                continue

            item = ChatPresentationSupplierDisplayService.enrich_item(raw)

            if code:
                item["product_code"] = code

            document = str(item.get("document_number") or item.get("purchase_order") or "").strip()
            source = str(item.get("source") or "").strip()

            if code and document and source:
                item["_detailMeta"] = ChatPresentationDetailActionService.purchase_record_detail_meta(
                    product_code=code,
                    document_number=document,
                    source=source,
                    supplier_code=ChatPresentationSupplierDisplayService.supplier_code(item),
                    supplier_store=ChatPresentationSupplierDisplayService.supplier_store(item),
                )

            enriched.append(item)

        return enriched

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

        if description:
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

        items = self._enriched_items(root, path)

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
            profile_name = (
                "purchaseBudgetHistoryDetail"
                if self._route_namespace(path) == "purchaseBudgetHistory"
                else "mpPriceHistoryDetail"
            )
            table = _OpsTable.build_items_table(
                self._host.column_label_context,
                shown,
                profile_name=profile_name,
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
        rows = _OpsTable.summary_kv_rows(
            self._host.column_label_context,
            summary,
            path=path,
            profile_name="purchaseHistoryOverview",
        )

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
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_kpi(
            self._host,
            root,
            path
        )

    def build_purchase_history_chart_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_chart(
            self._host,
            root,
            path
        )

    def build_purchase_history_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_tree(
            self._host,
            root,
            path
        )

    def build_purchase_history_dashboard_presentation(self, root: dict, path: str, *, kpi: dict | None = None, chart: dict | None = None, table: dict | None = None) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_dashboard(
            self._host,
            root,
            path,
            kpi=kpi,
            chart=chart,
            table=table
        )
