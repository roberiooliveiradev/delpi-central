"""Análise produtiva (PA/PI/OP/apontamentos) — perfil generalizável."""

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


class ExternalActionProductProductionStatusPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _insight(self, key: str, **values: str) -> str:
        return self._host._presenter_text("compositeAnalysisInsights", "productionStatus", key, **values)

    def _route(self, key: str, **values: str) -> str:
        return self._host._route_presentation("productionStatus", key, **values)

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

    def _present_production_status(self, root: dict, path: str) -> dict:
        code, description = self._product_context(root, path)
        linhas = self._build_narrative_lines(root, code=code, description=description)
        markdown_body = self._build_markdown_body(root, code=code, description=description)

        return {
            "titulo": (
                self._route("titleWithCode", code=code)
                if code
                else self._route("titleGeneric")
            ),
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
            "humanizedMarkdown": markdown_body,
        }

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

    def _build_narrative_lines(
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
                    "introWithDescription",
                    code=code,
                    description=description,
                )
            )
        elif code:
            linhas.append(self._route("introCodeOnly", code=code))

        reference_date = str(root.get("reference_date") or "").strip()

        if reference_date:
            linhas.append(self._route("referenceDateLine", date=reference_date))

        summary = self._summary(root)

        if summary:
            linhas.append(
                self._route(
                    "paStartedLine",
                    value=_Narrative.format_production_flag(summary.get("pa_production_started")),
                )
            )
            linhas.append(
                self._route(
                    "piStartedLine",
                    value=_Narrative.format_production_flag(summary.get("pi_production_started")),
                )
            )
            linhas.append(
                self._route(
                    "ordersLine",
                    paOrders=str(summary.get("total_pa_orders") or 0),
                    piOrders=str(summary.get("total_pi_orders") or 0),
                )
            )
            linhas.append(
                self._route(
                    "reportedLine",
                    paQty=_Narrative.format_quantity(
                        self._host,
                        summary.get("total_pa_reported_quantity"),
                        field_key="total_pa_reported_quantity",
                    ),
                    piQty=_Narrative.format_quantity(
                        self._host,
                        summary.get("total_pi_reported_quantity"),
                        field_key="total_pi_reported_quantity",
                    ),
                )
            )

        items = self._items(root)

        _Narrative.append_item_preview(
            self._host,
            linhas,
            items,
            compact_for_rich_ui=compact_for_rich_ui,
            preview_line=self._route("itemsPreviewLine", count=str(len(items))),
            empty_line=self._route("itemsEmptyLine"),
            table_hint=self._route("tableVisualizationHint"),
            format_item_line=self._format_op_preview_line,
        )

        return linhas or [self._host._presenter_text("generic", "apiAuthorized")]

    def _format_op_preview_line(self, item: dict) -> str:
        return self._route(
            "opLine",
            level=str(item.get("level") or "—"),
            order=str(item.get("production_order") or "—"),
            product=str(item.get("product_code") or item.get("order_product_code") or "—"),
            started=_Narrative.format_production_flag(item.get("production_started")),
            reported=_Narrative.format_quantity(
                self._host,
                item.get("reported_quantity"),
            ),
        )

    def _build_highlights(self, root: dict) -> list[str]:
        highlights: list[str] = []
        reference_date = str(root.get("reference_date") or "—")
        highlights.append(self._insight("scopeHeadline", date=reference_date))

        summary = self._summary(root)
        pa_started = str(summary.get("pa_production_started") or "").upper()
        pi_started = str(summary.get("pi_production_started") or "").upper()
        items = self._items(root)

        if items:
            with_reports = [
                item
                for item in items
                if isinstance(item, dict) and int(item.get("total_reports") or 0) > 0
            ]

            if with_reports:
                highlights.append(
                    self._insight("hasAppointments", count=str(len(with_reports)))
                )

        if pa_started not in {"SIM", "SIM_SC2", "TRUE", "1"}:
            highlights.append(self._insight("paNotStarted"))

        if pi_started in {"SIM", "SIM_SC2", "TRUE", "1"} and pa_started not in {
            "SIM",
            "SIM_SC2",
            "TRUE",
            "1",
        }:
            highlights.append(self._insight("piWithoutPa"))

        return highlights

    def _build_attention(self, root: dict) -> list[str]:
        attention: list[str] = []

        for item in self._items(root):
            if not isinstance(item, dict):
                continue

            started = str(item.get("production_started") or "").upper()
            order = str(item.get("production_order") or "").strip()
            try:
                reported = float(str(item.get("reported_quantity") or 0).replace(",", "."))
            except ValueError:
                reported = 0.0

            try:
                order_qty = float(str(item.get("order_quantity") or 0).replace(",", "."))
            except ValueError:
                order_qty = 0.0

            if order and started in {"NAO", "NÃO", "FALSE", "0"}:
                attention.append(self._insight("attentionStaleOp"))
                break

            if order_qty > 0 and 0 < reported < order_qty:
                attention.append(self._insight("attentionLowReport"))
                break

        return attention

    def _build_markdown_body(
        self,
        root: dict,
        *,
        code: str,
        description: str,
        compact_for_rich_ui: bool = False,
    ) -> str:
        parts: list[str] = []
        parts.extend(
            self._build_narrative_lines(
                root,
                code=code,
                description=description,
                compact_for_rich_ui=compact_for_rich_ui,
            )
        )

        highlights = self._build_highlights(root)

        if highlights:
            parts.extend(["", self._insight("highlightsHeader"), ""])
            parts.extend(f"- {line}" for line in highlights)

        attention = self._build_attention(root)

        if attention:
            parts.extend(["", self._insight("attentionHeader"), ""])
            parts.extend(f"{index}. {line}" for index, line in enumerate(attention, start=1))

        return _OpsTable.join_markdown_blocks(parts)

    def _build_production_status_text_presentation(self, root: dict, path: str) -> dict | None:
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
                "productionStatusWithCode",
                code=code,
            )
            if code
            else self._host._presenter_text(
                "productPresentationTitles",
                "productionStatusGeneric",
            )
        )
        auxiliary_tables = self.build_production_status_table_presentations(root, path)
        compact_for_rich_ui = ChatRichPresentationTextService.should_compact_narrative(
            table_presentations=auxiliary_tables,
        )
        body = self._build_markdown_body(
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
                "productionStatus",
                "scopeIntro",
            )
            markdown_parts.extend([scope_line, ""])

        markdown_parts.append(body)

        return {
            "type": "markdown",
            "title": title,
            "markdown": "\n".join(markdown_parts).strip(),
        }

    def build_production_status_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_overview_table(root)

        if overview:
            overview["role"] = "profile"
            tables.append(overview)

        items = [item for item in self._items(root) if isinstance(item, dict)]

        if items:
            shown, total = _OpsTable.limit_items(items, sort_key="production_order")
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
                self._host,
                shown,
                profile_name="factoryProductionDetail",
                title=title,
                role="list",
            )

            if table:
                tables.append(table)

        return [table for table in tables if isinstance(table, dict)]

    def _build_overview_table(self, root: dict) -> dict | None:
        summary = self._summary(root)

        if not summary:
            return None

        columns = self._host._column_labels.kv_table_column_defs()
        rows = _OpsTable.summary_kv_rows(self._host, summary)

        reference_date = str(root.get("reference_date") or "").strip()

        if reference_date:
            rows.insert(0, {"campo": "Referência", "valor": reference_date})

        return {
            "type": "table",
            "title": self._route("overviewTableTitle"),
            "columns": columns,
            "rows": rows,
            "role": "profile",
        }

    def build_production_status_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_kpi(
            self._host,
            root,
            path,
            profile_key="production_status",
        )

    def build_production_status_chart_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_chart(
            self._host,
            root,
            path,
            profile_key="production_status",
        )

    def build_production_status_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_tree(
            self._host,
            root,
            path,
            profile_key="production_status",
        )

    def build_production_status_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_dashboard(
            self._host,
            root,
            path,
            profile_key="production_status",
            kpi=kpi,
            chart=chart,
            table=table,
        )
