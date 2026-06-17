"""Listagem paginada de compras do produto — perfil generalizável."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionProductPurchasesPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _route(self, key: str, **values: str) -> str:
        return self._host._route_presentation("purchaseList", key, **values)

    def _items(self, root: dict) -> list:
        items = root.get("items")

        if isinstance(items, list):
            return items

        return []

    def _product_code(self, root: dict, path: str) -> str:
        items = self._items(root)

        if items and isinstance(items[0], dict):
            code = str(items[0].get("product_code") or "").strip()

            if code:
                return code

        return str(self._host._extract_product_code_from_path(path) or "").strip()

    def _present_product_purchases(self, root: dict, path: str) -> dict:
        code = self._product_code(root, path)
        items = self._items(root)
        total = int(root.get("total") or len(items))
        linhas: list[str] = []

        if code:
            linhas.append(self._route("introWithCode", code=code, total=str(total)))
        else:
            linhas.append(self._route("introGeneric", total=str(total)))

        if items:
            linhas.append(self._route("itemsPreviewLine", count=str(len(items))))
        else:
            linhas.append(self._route("itemsEmptyLine"))

        title = (
            self._route("titleWithCode", code=code)
            if code
            else self._route("titleGeneric")
        )

        markdown = self._build_purchases_text_presentation(root, path)

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
            "humanizedMarkdown": markdown.get("markdown") if isinstance(markdown, dict) else None,
        }

    def _build_purchases_text_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_rich_presentation_text_service import (
            ChatRichPresentationTextService,
        )

        code = self._product_code(root, path)
        title = (
            self._route("titleWithCode", code=code)
            if code
            else self._route("titleGeneric")
        )
        auxiliary_tables = self.build_purchases_table_presentations(root, path)
        compact_for_rich_ui = ChatRichPresentationTextService.should_compact_narrative(
            table_presentations=auxiliary_tables,
        )
        total = int(root.get("total") or len(self._items(root)))
        body_parts = []

        if code:
            body_parts.append(self._route("introWithCode", code=code, total=str(total)))
        else:
            body_parts.append(self._route("introGeneric", total=str(total)))

        items = self._items(root)

        if items:
            body_parts.append(self._route("itemsPreviewLine", count=str(len(items))))
        else:
            body_parts.append(self._route("itemsEmptyLine"))

        body = _OpsTable.join_narrative_lines(body_parts)

        if not body:
            return None

        return {
            "type": "markdown",
            "title": title,
            "markdown": f"### {title}\n\n{body}".strip(),
        }

    def build_purchases_table_presentations(self, root: dict, path: str) -> list[dict]:
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
                    "ordersTableTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("ordersTableTitle")
            )
            table = _OpsTable.build_items_table(
                self._host.column_label_context,
                shown,
                profile_name="purchaseOrderList",
                title=title,
                role="list",
            )

            if table:
                tables.append(table)

        return [table for table in tables if isinstance(table, dict)]

    def _build_overview_table(self, root: dict, path: str) -> dict | None:
        items = self._items(root)
        code = self._product_code(root, path)
        columns = self._host._column_labels.kv_table_column_defs()
        rows = [
            {
                "campo": self._route("overviewProductField"),
                "valor": code or "—",
            },
            {
                "campo": self._route("overviewTotalField"),
                "valor": str(root.get("total") or len(items)),
            },
            {
                "campo": self._route("overviewPageField"),
                "valor": f"{root.get('page') or 1} / {root.get('total_pages') or 1}",
            },
        ]

        if items:
            total_qty = sum(float(item.get("ordered_quantity") or 0) for item in items if isinstance(item, dict))
            rows.append(
                {
                    "campo": self._route("overviewQuantityField"),
                    "valor": self._host._format_field_value("ordered_quantity", total_qty),
                }
            )

        return {
            "type": "table",
            "title": self._route("overviewTableTitle"),
            "columns": columns,
            "rows": rows,
            "role": "profile",
        }

    def build_purchases_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_kpi(
            self._host,
            root,
            path,
            profile_key="purchase_list"
        )

    def build_purchases_chart_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_chart(
            self._host,
            root,
            path,
            profile_key="purchase_list"
        )

    def build_purchases_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_tree(
            self._host,
            root,
            path,
            profile_key="purchase_list"
        )

    def build_purchases_dashboard_presentation(self, root: dict, path: str, *, kpi: dict | None = None, chart: dict | None = None, table: dict | None = None) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_dashboard(
            self._host,
            root,
            path,
            profile_key="purchase_list",
            kpi=kpi,
            chart=chart,
            table=table
        )
