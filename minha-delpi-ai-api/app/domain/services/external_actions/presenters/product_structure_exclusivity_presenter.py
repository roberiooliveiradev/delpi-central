"""Estrutura vigente com exclusividade de MPs — perfil generalizável."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)
from app.domain.services.external_actions.operational_route_narrative_service import (
    ExternalActionOperationalRouteNarrativeService,
)
from app.domain.services.external_actions.presenters.product_operational_table_row_enrichment import (
    enrich_structure_rows,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

_Narrative = ExternalActionOperationalRouteNarrativeService


class ExternalActionProductStructureExclusivityPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _insight(self, key: str, **values: str) -> str:
        return self._host._presenter_text(
            "compositeAnalysisInsights",
            "structureExclusivity",
            key,
            **values,
        )

    def _route(self, key: str, **values: str) -> str:
        return self._host._route_presentation("structureExclusivity", key, **values)

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

    def _present_structure_exclusivity(self, root: dict, path: str) -> dict:
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

    def _is_exclusive(self, item: dict) -> bool:
        value = item.get("exclusive_raw_material")

        if isinstance(value, bool):
            return value

        return str(value or "").strip().upper() in {"SIM", "S", "TRUE", "1"}

    def _exclusive_items(self, root: dict) -> list[dict]:
        return [item for item in self._items(root) if isinstance(item, dict) and self._is_exclusive(item)]

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

        summary = self._summary(root)

        if summary:
            linhas.append(
                self._route(
                    "componentsLine",
                    total=str(summary.get("total_components") or 0),
                    intermediates=str(summary.get("total_intermediates") or 0),
                    rawMaterials=str(summary.get("total_raw_materials") or 0),
                )
            )
            linhas.append(
                self._route(
                    "exclusiveLine",
                    count=str(summary.get("total_exclusive_raw_materials") or 0),
                )
            )

        exclusive_items = self._exclusive_items(root)

        if exclusive_items:
            linhas.append(
                self._route("exclusivePreviewLine", count=str(len(exclusive_items)))
            )

            if compact_for_rich_ui:
                linhas.append(self._route("treeVisualizationHint"))
            else:
                for item in exclusive_items[: _Narrative._PREVIEW_MAX]:
                    linhas.append(self._format_exclusive_preview_line(item))

                remaining = len(exclusive_items) - min(len(exclusive_items), _Narrative._PREVIEW_MAX)

                if remaining > 0:
                    linhas.append(
                        self._host._presenter_text(
                            "pagination",
                            "moreDetailRecords",
                            count=str(remaining),
                        )
                    )

                if len(exclusive_items) > _Narrative._PREVIEW_MAX:
                    linhas.append(
                        self._route(
                            "treeVisualizationHint"
                            if compact_for_rich_ui
                            else "tableVisualizationHint"
                        )
                    )
        elif self._items(root):
            linhas.append(self._route("noExclusiveLine"))

            if compact_for_rich_ui:
                linhas.append(self._route("treeVisualizationHint"))
        else:
            linhas.append(self._route("itemsEmptyLine"))

        return linhas or [self._host._presenter_text("generic", "apiAuthorized")]

    def _format_exclusive_preview_line(self, item: dict) -> str:
        return self._route(
            "exclusiveItemLine",
            code=str(item.get("product_code") or item.get("component_code") or "—"),
            quantity=_Narrative.format_quantity(
                self._host,
                item.get("accumulated_quantity") or item.get("quantity"),
                field_key="accumulated_quantity",
            ),
            level=str(item.get("level") or "—"),
        )

    def _build_highlights(self, root: dict) -> list[str]:
        highlights: list[str] = []
        summary = self._summary(root)
        exclusive_count = int(summary.get("total_exclusive_raw_materials") or 0)
        raw_materials = int(summary.get("total_raw_materials") or 0)

        highlights.append(
            self._insight(
                "scopeHeadline",
                exclusive=str(exclusive_count),
                rawMaterials=str(raw_materials),
            )
        )

        if exclusive_count > 0:
            highlights.append(self._insight("hasExclusive", count=str(exclusive_count)))

        if raw_materials > 0 and exclusive_count == 0:
            highlights.append(self._insight("noExclusiveMps"))

        if not self._items(root):
            highlights.append(self._insight("noStructure"))

        return highlights

    def _build_attention(self, root: dict) -> list[str]:
        attention: list[str] = []
        exclusive_count = int(self._summary(root).get("total_exclusive_raw_materials") or 0)

        if exclusive_count > 0:
            attention.append(self._insight("attentionExclusiveSupply"))

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

        conclusion = self._build_conclusion_lines(root)

        if conclusion:
            parts.extend(["", *conclusion])

        if compact_for_rich_ui:
            parts.append(self._route("treeVisualizationHint"))

        return _OpsTable.join_markdown_blocks(parts)

    def _build_conclusion_lines(self, root: dict) -> list[str]:
        summary = self._summary(root)
        exclusive_count = int(summary.get("total_exclusive_raw_materials") or 0)
        lines: list[str] = []

        if exclusive_count == 0 and self._items(root):
            lines.append(f"**{self._route('sharedMpConclusionLine')}**")

            for item in self._items(root):
                if not isinstance(item, dict):
                    continue

                if str(item.get("component_type") or "").upper() != "MP":
                    continue

                usage = item.get("total_valid_finished_products_using_mp")

                if usage in (None, "", 0):
                    continue

                code = str(
                    item.get("component_code")
                    or item.get("product_code")
                    or "—"
                )
                lines.append(
                    self._route(
                        "sharedMpUsageLine",
                        code=code,
                        count=str(usage),
                    )
                )

        return lines

    def _build_structure_exclusivity_text_presentation(self, root: dict, path: str) -> dict | None:
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
                "structureExclusivityWithCode",
                code=code,
            )
            if code
            else self._host._presenter_text(
                "productPresentationTitles",
                "structureExclusivityGeneric",
            )
        )
        auxiliary_tables = self.build_structure_exclusivity_table_presentations(root, path)
        tree_presentation = self.build_structure_exclusivity_tree_presentation(root, path)
        compact_for_rich_ui = ChatRichPresentationTextService.should_compact_narrative(
            table_presentations=auxiliary_tables,
            tree_presentation=tree_presentation,
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
                "structureExclusivity",
                "scopeIntro",
            )
            markdown_parts.extend([scope_line, ""])

        markdown_parts.append(body)

        return {
            "type": "markdown",
            "title": title,
            "markdown": "\n".join(markdown_parts).strip(),
        }

    def build_structure_exclusivity_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_overview_table(root)

        if overview:
            overview["role"] = "profile"
            tables.append(overview)

        items = enrich_structure_rows(
            [item for item in self._items(root) if isinstance(item, dict)]
        )

        if items:
            shown, total = _OpsTable.limit_items(items, sort_key="level", reverse=False)
            title = (
                self._route(
                    "componentsTableTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("componentsTableTitle")
            )
            table = _OpsTable.build_items_table(
                self._host.column_label_context,
                shown,
                profile_name="structureExclusivityDetail",
                title=title,
                role="structure",
            )

            if table:
                tables.append(table)

        return [table for table in tables if isinstance(table, dict)]

    def _build_overview_table(self, root: dict) -> dict | None:
        summary = self._summary(root)

        if not summary:
            return None

        columns = self._host._column_labels.kv_table_column_defs()
        rows = _OpsTable.summary_kv_rows(self._host.column_label_context, summary)

        return {
            "type": "table",
            "title": self._route("overviewTableTitle"),
            "columns": columns,
            "rows": rows,
            "role": "profile",
        }

    def build_structure_exclusivity_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_kpi(
            self._host,
            root,
            path,
            profile_key="structure_exclusivity"
        )

    def build_structure_exclusivity_chart_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_chart(
            self._host,
            root,
            path,
            profile_key="structure_exclusivity"
        )

    def build_structure_exclusivity_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_tree(
            self._host,
            root,
            path,
            profile_key="structure_exclusivity"
        )

    def build_structure_exclusivity_dashboard_presentation(self, root: dict, path: str, *, kpi: dict | None = None, tree: dict | None = None, chart: dict | None = None, table: dict | None = None) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_dashboard(
            self._host,
            root,
            path,
            profile_key="structure_exclusivity", kpi=kpi, tree=tree, chart=chart, table=table
        )
