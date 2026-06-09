"""Expedição / inspeção final do PA — perfil generalizável."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.services.external_actions.operational_route_narrative_service import (
    ExternalActionOperationalRouteNarrativeService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

_Narrative = ExternalActionOperationalRouteNarrativeService


class ExternalActionProductShippingStatusPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _insight(self, key: str, **values: str) -> str:
        return self._host._presenter_text("compositeAnalysisInsights", "shippingStatus", key, **values)

    def _route(self, key: str, **values: str) -> str:
        return self._host._route_presentation("shippingStatus", key, **values)

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

    def _present_shipping_status(self, root: dict, path: str) -> dict:
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

    def _period_label(self, root: dict) -> str:
        date_start = str(root.get("date_start") or root.get("reference_date") or "").strip()
        date_end = str(root.get("date_end_exclusive") or "").strip()

        if date_start and date_end:
            return self._route("periodLine", start=date_start, end=date_end)

        if date_start:
            return self._route("referenceDateLine", date=date_start)

        return ""

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

        period_line = self._period_label(root)

        if period_line:
            linhas.append(period_line)

        summary = self._summary(root)

        if summary:
            linhas.append(
                self._route(
                    "shippedLine",
                    value=_Narrative.format_quantity(
                        self._host,
                        summary.get("total_shipped_quantity"),
                        field_key="total_shipped_quantity",
                    ),
                )
            )
            linhas.append(
                self._route(
                    "lossLine",
                    value=_Narrative.format_quantity(
                        self._host,
                        summary.get("total_inspection_loss_quantity"),
                        field_key="total_inspection_loss_quantity",
                    ),
                )
            )
            linhas.append(
                self._route(
                    "reportsLine",
                    value=str(summary.get("total_reports") or 0),
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
            format_item_line=self._format_movement_preview_line,
        )

        return linhas or [self._host._presenter_text("generic", "apiAuthorized")]

    def _format_movement_preview_line(self, item: dict) -> str:
        return self._route(
            "movementLine",
            order=str(item.get("production_order") or "—"),
            shipped=_Narrative.format_quantity(
                self._host,
                item.get("shipped_quantity"),
                field_key="shipped_quantity",
            ),
            loss=_Narrative.format_quantity(
                self._host,
                item.get("inspection_loss_quantity"),
                field_key="inspection_loss_quantity",
            ),
        )

    def _build_highlights(self, root: dict) -> list[str]:
        highlights: list[str] = []
        period = self._period_label(root) or "—"
        highlights.append(self._insight("scopeHeadline", period=period))

        summary = self._summary(root)

        try:
            shipped = float(str(summary.get("total_shipped_quantity") or 0).replace(",", "."))
        except ValueError:
            shipped = 0.0

        try:
            loss = float(str(summary.get("total_inspection_loss_quantity") or 0).replace(",", "."))
        except ValueError:
            loss = 0.0

        if shipped > 0:
            highlights.append(
                self._insight(
                    "hasShipped",
                    quantity=_Narrative.format_quantity(
                        self._host,
                        summary.get("total_shipped_quantity"),
                        field_key="total_shipped_quantity",
                    ),
                )
            )

        if loss > 0 and shipped == 0:
            highlights.append(self._insight("lossWithoutShip"))

        if shipped == 0 and loss == 0 and not self._items(root):
            highlights.append(self._insight("noMovement"))

        return highlights

    def _build_attention(self, root: dict) -> list[str]:
        attention: list[str] = []

        for item in self._items(root):
            if not isinstance(item, dict):
                continue

            try:
                shipped = float(str(item.get("shipped_quantity") or 0).replace(",", "."))
            except ValueError:
                shipped = 0.0

            try:
                loss = float(str(item.get("inspection_loss_quantity") or 0).replace(",", "."))
            except ValueError:
                loss = 0.0

            if loss > 0 and shipped == 0:
                attention.append(self._insight("attentionLossOnly"))
                break

            if loss > 0 and shipped > 0 and loss >= shipped:
                attention.append(self._insight("attentionHighLoss"))
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

        return "\n".join(part for part in parts if part is not None).strip()

    def _build_shipping_status_text_presentation(self, root: dict, path: str) -> dict | None:
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
                "shippingStatusWithCode",
                code=code,
            )
            if code
            else self._host._presenter_text(
                "productPresentationTitles",
                "shippingStatusGeneric",
            )
        )
        auxiliary_tables = self.build_shipping_status_table_presentations(root, path)
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
                "shippingStatus",
                "scopeIntro",
            )
            markdown_parts.extend([scope_line, ""])

        markdown_parts.append(body)

        return {
            "type": "markdown",
            "title": title,
            "markdown": "\n".join(markdown_parts).strip(),
        }

    def build_shipping_status_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_overview_table(root)

        if overview:
            tables.append(overview)

        items = self._items(root)

        if items:
            table = self._host._build_items_table(
                items,
                title=self._route("movementsTableTitle"),
                path=path,
            )

            if table:
                tables.append(table)

        return tables

    def _build_overview_table(self, root: dict) -> dict | None:
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

        period = self._period_label(root)

        if period:
            rows.insert(0, {"campo": "Período", "valor": period.replace("**", "")})

        return {
            "type": "table",
            "title": self._route("overviewTableTitle"),
            "columns": columns,
            "rows": rows,
        }
