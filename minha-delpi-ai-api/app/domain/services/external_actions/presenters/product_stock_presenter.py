"""Apresentação humanizada de estoque por filial/armazém — perfil dedicado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


@dataclass(frozen=True)
class _StockAggregation:
    product_code: str
    branches: tuple[str, ...]
    warehouses: tuple[str, ...]
    positions: int
    total_available: float
    total_current: float
    total_committed: float
    has_available: bool
    has_current: bool
    negative_positions: int
    zero_available_positions: int
    committed_over_current_positions: int
    top_branch: str
    top_branch_available: float
    total_records: int | None
    page: int | None
    page_size: int | None


class ExternalActionProductStockPresenter:
    _DETAIL_PREVIEW_MAX = 8

    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _insight(self, key: str, **values: str) -> str:
        return self._host._presenter_text("compositeAnalysisInsights", "stock", key, **values)

    def _route(self, key: str, **values: str) -> str:
        return self._host._route_presentation("stock", key, **values)

    def _aggregate(self, items: list, *, path: str, root: dict | None = None) -> _StockAggregation:
        product_code = self._host._extract_product_code_from_path(path)

        if not product_code:
            for item in items:
                if not isinstance(item, dict):
                    continue

                candidate = str(item.get("product_code") or item.get("code") or "").strip()

                if candidate:
                    product_code = candidate
                    break
        branches: set[str] = set()
        warehouses: set[str] = set()
        total_available = 0.0
        total_current = 0.0
        total_committed = 0.0
        has_available = False
        has_current = False
        negative_positions = 0
        zero_available_positions = 0
        committed_over_current_positions = 0
        branch_available: dict[str, float] = {}

        for item in items:
            if not isinstance(item, dict):
                continue

            branch = str(item.get("branch") or "").strip()
            warehouse = str(item.get("warehouse") or "").strip()

            if branch:
                branches.add(branch)

            if warehouse:
                warehouses.add(warehouse)

            available_raw = item.get("available_quantity")
            current_raw = item.get("current_quantity")
            committed_raw = item.get("committed_quantity")
            available = float(available_raw or 0) if available_raw is not None else None
            current = float(current_raw or 0) if current_raw is not None else None
            committed = float(committed_raw or 0) if committed_raw is not None else 0.0

            if available is not None:
                has_available = True
                total_available += available

                if branch:
                    branch_available[branch] = branch_available.get(branch, 0.0) + available

                if available < 0:
                    negative_positions += 1

                if available == 0:
                    zero_available_positions += 1

            if current is not None:
                has_current = True
                total_current += current

                if committed > current:
                    committed_over_current_positions += 1

            total_committed += committed

        top_branch = ""
        top_branch_available = 0.0

        if branch_available:
            top_branch, top_branch_available = max(
                branch_available.items(),
                key=lambda pair: pair[1],
            )

        meta = root if isinstance(root, dict) else {}
        total_records = meta.get("total")
        page = meta.get("page")
        page_size = meta.get("page_size")

        return _StockAggregation(
            product_code=product_code,
            branches=tuple(sorted(branches)),
            warehouses=tuple(sorted(warehouses)),
            positions=len(items),
            total_available=total_available,
            total_current=total_current,
            total_committed=total_committed,
            has_available=has_available,
            has_current=has_current,
            negative_positions=negative_positions,
            zero_available_positions=zero_available_positions,
            committed_over_current_positions=committed_over_current_positions,
            top_branch=top_branch,
            top_branch_available=top_branch_available,
            total_records=int(total_records) if total_records is not None else None,
            page=int(page) if page is not None else None,
            page_size=int(page_size) if page_size is not None else None,
        )

    def _summary_line(self, agg: _StockAggregation) -> str:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        if agg.product_code:
            summary = ChatProductOperationalContentService.format(
                "presenter",
                "stock",
                "summaryWithCode",
                code=agg.product_code,
                positions=agg.positions,
            )

            if agg.branches:
                summary += ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "summaryBranches",
                    count=len(agg.branches),
                    branches=", ".join(agg.branches),
                )

            if agg.warehouses:
                summary += ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "summaryWarehouses",
                    count=len(agg.warehouses),
                    warehouses=", ".join(agg.warehouses),
                )

            summary += "."

            if agg.has_available:
                summary += ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "summaryAvailableTotal",
                    total=self._host._format_num(agg.total_available),
                )
            elif agg.has_current:
                summary += ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "summaryCurrentTotal",
                    total=self._host._format_num(agg.total_current),
                )
            else:
                summary += ChatProductOperationalContentService.get(
                    "presenter",
                    "stock",
                    "summaryNoAvailable",
                )

            return summary

        summary = ChatProductOperationalContentService.format(
            "presenter",
            "stock",
            "summaryWithoutCode",
            positions=agg.positions,
        )

        if agg.branches:
            summary += ChatProductOperationalContentService.format(
                "presenter",
                "stock",
                "summaryWithoutCodeBranches",
                count=len(agg.branches),
            )
        else:
            summary += "."

        return summary

    def _detail_lines(self, items: list) -> list[str]:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        detail_lines: list[str] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            detail_lines.append(
                ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "detailLine",
                    branch=item.get("branch") or "—",
                    warehouse=item.get("warehouse") or "—",
                    current=self._host._format_num(item.get("current_quantity")),
                    available=self._host._format_num(item.get("available_quantity")),
                    committed=self._host._format_num(item.get("committed_quantity")),
                    location=item.get("physical_location")
                    or ChatProductOperationalContentService.get(
                        "presenter",
                        "stock",
                        "locationFallback",
                    ),
                )
            )

        return detail_lines

    def _build_highlights(self, agg: _StockAggregation) -> list[str]:
        highlights: list[str] = []

        if agg.has_available:
            highlights.append(
                self._insight(
                    "headlineAvailable",
                    total=self._host._format_num(agg.total_available),
                    positions=str(agg.positions),
                )
            )

        if agg.total_available < 0:
            highlights.append(
                self._insight(
                    "negativeTotal",
                    total=self._host._format_num(agg.total_available),
                )
            )

        if agg.top_branch and agg.top_branch_available != 0:
            highlights.append(
                self._insight(
                    "topBranch",
                    branch=agg.top_branch,
                    quantity=self._host._format_num(agg.top_branch_available),
                )
            )

        if agg.zero_available_positions:
            highlights.append(
                self._insight(
                    "zeroPositions",
                    count=str(agg.zero_available_positions),
                )
            )

        if agg.committed_over_current_positions:
            highlights.append(
                self._insight(
                    "committedOverCurrent",
                    count=str(agg.committed_over_current_positions),
                )
            )

        if (
            agg.total_records is not None
            and agg.positions < agg.total_records
            and agg.page_size
        ):
            highlights.append(
                self._insight(
                    "paginatedResult",
                    shown=str(agg.positions),
                    total=str(agg.total_records),
                )
            )

        return highlights

    def _build_attention(self, agg: _StockAggregation) -> list[str]:
        attention: list[str] = []

        if agg.total_available < 0 or agg.negative_positions:
            attention.append(self._insight("attentionNegative"))

        if agg.committed_over_current_positions:
            attention.append(self._insight("attentionCommitted"))

        if agg.total_committed > 0 and agg.has_available and agg.total_available <= 0:
            attention.append(self._insight("attentionFullyCommitted"))

        if (
            agg.total_records is not None
            and agg.positions < agg.total_records
        ):
            attention.append(self._insight("attentionPagination"))

        return attention

    def _build_markdown_body(
        self,
        items: list,
        *,
        path: str,
        root: dict | None,
        compact_for_rich_ui: bool = False,
    ) -> str:
        agg = self._aggregate(items, path=path, root=root)
        parts: list[str] = [self._summary_line(agg)]
        detail_lines = self._detail_lines(items)

        if compact_for_rich_ui:
            parts.append(self._route("tableVisualizationHint"))
        elif detail_lines:
            parts.append("")
            parts.append(f"**{self._host._presenter_text('generic', 'stockTextDetailHeader')}**")

            preview = detail_lines[: self._DETAIL_PREVIEW_MAX]

            for line in preview:
                parts.append(f"- {line}")

            remaining = len(detail_lines) - len(preview)

            if remaining > 0:
                parts.append(
                    self._host._presenter_text(
                        "pagination",
                        "moreDetailRecords",
                        count=str(remaining),
                    )
                )

        highlights = self._build_highlights(agg)

        if highlights:
            parts.extend(["", self._insight("highlightsHeader"), ""])
            parts.extend(f"- {line}" for line in highlights)

        attention = self._build_attention(agg)

        if attention:
            parts.extend(["", self._insight("attentionHeader"), ""])
            parts.extend(f"{index}. {line}" for index, line in enumerate(attention, start=1))

        return _OpsTable.join_markdown_blocks(parts)

    def _present_product_stock(
        self,
        items: list,
        *,
        path: str = "",
        title: str | None = None,
        root: dict | None = None,
    ) -> dict:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        agg = self._aggregate(items, path=path, root=root)

        if agg.product_code:
            titulo = self._host._presenter_text(
                "productPresentationTitles",
                "stockWithCode",
                code=agg.product_code,
            )
        else:
            titulo = (
                title
                or self._host._infer_items_title(items, path)
                or ChatAssistantContentService.get(
                    "presenter_content",
                    "titlesByPathFragment",
                    "/stock",
                )
            )

        linhas = [self._summary_line(agg)]
        detail_lines = self._detail_lines(items)

        if len(detail_lines) > self._DETAIL_PREVIEW_MAX:
            from app.domain.services.chat_product_operational_content_service import (
                ChatProductOperationalContentService,
            )

            linhas.append(
                ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "textModeDetailHint",
                    lines=len(detail_lines),
                )
            )

        markdown_body = self._build_markdown_body(
            items,
            path=path,
            root=root,
            compact_for_rich_ui=False,
        )

        return {
            "titulo": titulo,
            "linhas": linhas,
            "linhas_detalhe": detail_lines,
            "dados": {
                "items": items,
                "product_code": agg.product_code,
                "total": len(items),
            },
            "sourcePath": path,
            "humanizedMarkdown": markdown_body,
        }

    def _build_overview_table(self, items: list, *, path: str, root: dict | None) -> dict | None:
        agg = self._aggregate(items, path=path, root=root)
        columns = self._host._column_labels.kv_table_column_defs()
        rows: list[dict[str, str]] = [
            {
                "campo": self._route("overviewFieldProduct"),
                "valor": agg.product_code or "—",
            },
            {
                "campo": self._route("overviewFieldPositions"),
                "valor": str(agg.positions),
            },
            {
                "campo": self._route("overviewFieldBranches"),
                "valor": ", ".join(agg.branches) if agg.branches else "—",
            },
            {
                "campo": self._route("overviewFieldWarehouses"),
                "valor": ", ".join(agg.warehouses) if agg.warehouses else "—",
            },
        ]

        if agg.has_available:
            rows.append(
                {
                    "campo": self._route("overviewFieldAvailable"),
                    "valor": self._host._format_num(agg.total_available),
                }
            )

        if agg.has_current:
            rows.append(
                {
                    "campo": self._route("overviewFieldCurrent"),
                    "valor": self._host._format_num(agg.total_current),
                }
            )

        if agg.total_committed:
            rows.append(
                {
                    "campo": self._route("overviewFieldCommitted"),
                    "valor": self._host._format_num(agg.total_committed),
                }
            )

        if agg.total_records is not None:
            rows.append(
                {
                    "campo": self._route("overviewFieldTotalRecords"),
                    "valor": str(agg.total_records),
                }
            )

        return {
            "type": "table",
            "title": self._route("overviewTableTitle"),
            "columns": columns,
            "rows": rows,
            "role": "profile",
        }

    def build_stock_table_presentations(self, root: dict, path: str) -> list[dict]:
        items = root.get("items") if isinstance(root.get("items"), list) else []

        if not items:
            return []

        tables: list[dict] = []
        overview = self._build_overview_table(items, path=path, root=root)

        if overview:
            tables.append(overview)

        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        product_code = str(
            product.get("product_code")
            or product.get("code")
            or self._host._extract_product_code_from_path(path)
            or ""
        ).strip()
        description = str(product.get("description") or "").strip()
        enriched = _OpsTable.enrich_stock_position_rows(
            [item for item in items if isinstance(item, dict)],
            product_code=product_code,
            description=description,
        )
        shown, total = _OpsTable.limit_items(enriched, sort_key="branch", reverse=False)
        title = (
            self._route(
                "positionsTableTitleTruncated",
                shown=str(len(shown)),
                total=str(total),
            )
            if total > len(shown)
            else self._route("positionsTableTitle")
        )
        positions = _OpsTable.build_fixed_items_table(
            self._host,
            shown,
            table_id="stockProductPositions",
            title=title,
            role="list",
        )

        if positions:
            tables.append(positions)

        return tables

    def _build_stock_text_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )
        from app.domain.services.chat_rich_presentation_text_service import (
            ChatRichPresentationTextService,
        )

        items = root.get("items") if isinstance(root.get("items"), list) else []

        if not items:
            return None

        agg = self._aggregate(items, path=path, root=root)
        title = (
            self._host._presenter_text(
                "productPresentationTitles",
                "stockWithCode",
                code=agg.product_code,
            )
            if agg.product_code
            else self._host._presenter_text(
                "productPresentationTitles",
                "stockGeneric",
            )
        )
        auxiliary_tables = self.build_stock_table_presentations(root, path)
        compact_for_rich_ui = ChatRichPresentationTextService.should_compact_narrative(
            table_presentations=auxiliary_tables,
        )
        body = self._build_markdown_body(
            items,
            path=path,
            root=root,
            compact_for_rich_ui=compact_for_rich_ui,
        )

        if not body:
            return None

        markdown_parts = [f"### {title}", ""]

        if not compact_for_rich_ui:
            scope_line = ChatProductOperationalContentService.get(
                "presenter",
                "stock",
                "scopeIntro",
            )
            markdown_parts.extend([scope_line, ""])

        markdown_parts.append(body)

        return {
            "type": "markdown",
            "title": title,
            "markdown": "\n".join(markdown_parts).strip(),
        }

    def build_stock_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        items = root.get("items") if isinstance(root.get("items"), list) else []

        if not items:
            return None

        agg = self._aggregate(items, path=path, root=root)
        title = (
            self._route("kpiTitle", code=agg.product_code)
            if agg.product_code
            else self._route("kpiTitleGeneric")
        )
        cards = [
            ChatPresentationKpiAssemblyService.metric_card(
                label=self._route("kpiAvailable"),
                value=agg.total_available if agg.has_available else 0,
                unit="un.",
                color="#10b981",
                key="available_total",
            ),
            ChatPresentationKpiAssemblyService.metric_card(
                label=self._route("kpiCurrent"),
                value=agg.total_current if agg.has_current else 0,
                unit="un.",
                color="#0ea5e9",
                key="current_total",
            ),
            ChatPresentationKpiAssemblyService.metric_card(
                label=self._route("kpiCommitted"),
                value=agg.total_committed,
                unit="un.",
                color="#f59e0b",
                key="committed_total",
            ),
            ChatPresentationKpiAssemblyService.metric_card(
                label=self._route("kpiPositions"),
                value=agg.positions,
                unit="",
                color="#8b5cf6",
                key="positions",
            ),
            ChatPresentationKpiAssemblyService.metric_card(
                label=self._route("kpiBranches"),
                value=len(agg.branches),
                unit="",
                color="#6366f1",
                key="branches",
            ),
        ]

        return ChatPresentationKpiAssemblyService.build(title=title, cards=cards, min_cards=2)

    def build_stock_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_hierarchy_tree_service import (
            ChatPresentationHierarchyTreeService,
        )

        items = root.get("items") if isinstance(root.get("items"), list) else []

        if not items:
            return None

        agg = self._aggregate(items, path=path, root=root)
        title = (
            self._route("treeTitle", code=agg.product_code)
            if agg.product_code
            else self._route("treeTitleGeneric")
        )

        def _leaf(item: dict[str, Any]) -> dict[str, Any]:
            warehouse = str(item.get("warehouse") or "—")
            return ChatPresentationHierarchyTreeService._serialize_node(
                node_id=f"wh:{item.get('branch')}:{warehouse}",
                label=self._route("treeLeafLabel", warehouse=warehouse),
                subtitle=str(item.get("physical_location") or "").strip(),
                meta={
                    "available_quantity": float(item.get("available_quantity") or 0),
                    "current_quantity": float(item.get("current_quantity") or 0),
                    "committed_quantity": float(item.get("committed_quantity") or 0),
                },
            )

        return ChatPresentationHierarchyTreeService.build_multi_level(
            title=title,
            root_id=agg.product_code or "stock",
            root_label=(
                self._route("treeRootLabel", code=agg.product_code)
                if agg.product_code
                else title
            ),
            items=items,
            group_keys=["branch", "warehouse"],
            leaf_builder=_leaf,
        )

    def build_stock_dashboard_presentation(
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

        items = root.get("items") if isinstance(root.get("items"), list) else []

        if not items:
            return None

        agg = self._aggregate(items, path=path, root=root)
        title = (
            self._route("dashboardTitle", code=agg.product_code)
            if agg.product_code
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
                    title=str(chart.get("title") or self._host._presenter_text("charts", "stockByLocationTitle")),
                    presentation=chart,
                    chart_presentation=chart,
                )
            )

        if isinstance(table, dict) and table.get("type") == "table":
            panels.append(
                ChatPresentationDashboardAssemblyService.panel(
                    panel_id="positions",
                    title=str(table.get("title") or self._route("positionsTableTitle")),
                    presentation=table,
                )
            )

        return ChatPresentationDashboardAssemblyService.build(title=title, panels=panels)
