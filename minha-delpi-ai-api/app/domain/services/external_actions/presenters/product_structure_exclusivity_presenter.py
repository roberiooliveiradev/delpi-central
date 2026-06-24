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
    is_exclusive_raw_material_item,
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

    def _raw_material_items(self, root: dict) -> list[dict]:
        return [
            item
            for item in self._items(root)
            if isinstance(item, dict)
            and str(item.get("component_type") or "").upper() == "MP"
        ]

    def _exclusive_raw_material_items(self, root: dict) -> list[dict]:
        return [
            item
            for item in self._raw_material_items(root)
            if self._is_exclusive(item)
        ]

    def _exclusive_count(self, root: dict) -> int:
        return int(self._summary(root).get("total_exclusive_raw_materials") or 0)

    def _build_verdict_line(self, root: dict) -> str | None:
        summary = self._summary(root)
        exclusive_count = int(summary.get("total_exclusive_raw_materials") or 0)
        mp_count = int(summary.get("total_raw_materials") or 0)
        exclusive_mps = [
            item
            for item in self._raw_material_items(root)
            if self._is_exclusive(item)
        ]

        if exclusive_count > 0:
            if len(exclusive_mps) == 1:
                item = exclusive_mps[0]

                return self._route(
                    "exclusivityVerdictYesSingle",
                    code=str(item.get("product_code") or item.get("component_code") or "—"),
                    description=str(
                        item.get("description") or item.get("component_description") or "—"
                    ),
                )

            listing = self._format_exclusive_mp_list(exclusive_mps)

            return self._route(
                "exclusivityVerdictYesNamed",
                count=str(exclusive_count),
                list=listing,
            )

        if self._items(root) or mp_count > 0:
            return self._route(
                "exclusivityVerdictNo",
                count=str(mp_count),
            )

        return None

    def _format_exclusive_mp_list(self, items: list[dict], *, preview_limit: int = 8) -> str:
        parts: list[str] = []

        for item in items[:preview_limit]:
            code = str(item.get("product_code") or item.get("component_code") or "—")
            description = str(
                item.get("description") or item.get("component_description") or ""
            ).strip()
            parts.append(f"**{code}** ({description})" if description else f"**{code}**")

        remaining = len(items) - preview_limit

        if remaining > 0:
            parts.append(self._route("exclusiveListMore", count=str(remaining)))

        return "; ".join(parts)

    def _format_mp_item_line(self, item: dict) -> str:
        code = str(item.get("component_code") or item.get("product_code") or "—")
        description = str(item.get("component_description") or item.get("description") or "—")
        unit = str(item.get("component_unit") or item.get("unit") or "").strip()
        exclusive_suffix = (
            self._route("mpExclusiveSuffix")
            if self._is_exclusive(item)
            else self._route("mpSharedSuffix")
        )

        return self._route(
            "mpItemLine",
            code=code,
            description=description,
            quantity=_Narrative.format_quantity(
                self._host,
                item.get("accumulated_quantity") or item.get("quantity"),
                field_key="accumulated_quantity",
            ),
            unit=f" {unit}" if unit else "",
            exclusiveSuffix=exclusive_suffix,
        )

    def _build_mp_section_lines(
        self,
        root: dict,
        *,
        compact_for_rich_ui: bool = False,
    ) -> list[str]:
        if self._exclusive_count(root) <= 0:
            return []

        mp_items = self._sort_mp_exclusive_first(self._exclusive_raw_material_items(root))

        if not mp_items:
            return []

        preview_limit = 3 if compact_for_rich_ui else _Narrative._PREVIEW_MAX
        lines = [self._route("mpSectionTitleExclusive")]

        for item in mp_items[:preview_limit]:
            lines.append(self._format_mp_item_line(item))

        remaining = len(mp_items) - preview_limit

        if remaining > 0:
            lines.append(
                self._route("mpMoreLine", count=str(remaining))
            )

        return lines

    def _is_exclusive(self, item: dict) -> bool:
        return is_exclusive_raw_material_item(item)

    def _sort_mp_exclusive_first(self, items: list[dict]) -> list[dict]:
        return sorted(
            items,
            key=lambda item: (
                0 if self._is_exclusive(item) else 1,
                int(item.get("level") or 0),
            ),
        )

    def _build_narrative_lines(
        self,
        root: dict,
        *,
        code: str,
        description: str,
        compact_for_rich_ui: bool = False,
    ) -> list[str]:
        linhas: list[str] = []

        verdict = self._build_verdict_line(root)

        if verdict:
            linhas.append(verdict)

        exclusive_count = self._exclusive_count(root)

        if compact_for_rich_ui:
            compact_line = _Narrative.compact_product_line(
                self._host,
                code=code,
                description=description,
            )

            if compact_line:
                linhas.append(compact_line)
        elif description:
            intro_key = (
                "introWithDescription"
                if exclusive_count > 0
                else "introWithDescriptionNeutral"
            )
            linhas.append(
                self._route(
                    intro_key,
                    code=code,
                    description=description,
                )
            )
        elif code:
            intro_key = "introCodeOnly" if exclusive_count > 0 else "introCodeOnlyNeutral"
            linhas.append(self._route(intro_key, code=code))

        summary = self._summary(root)

        if summary and not compact_for_rich_ui:
            linhas.append(
                self._route(
                    "componentsLine",
                    total=str(summary.get("total_components") or 0),
                    intermediates=str(summary.get("total_intermediates") or 0),
                    rawMaterials=str(summary.get("total_raw_materials") or 0),
                )
            )

        mp_section = self._build_mp_section_lines(
            root,
            compact_for_rich_ui=compact_for_rich_ui,
        )

        if mp_section:
            linhas.extend(["", *mp_section])

        if not self._items(root):
            linhas.append(self._route("itemsEmptyLine"))

        return linhas or [self._host._presenter_text("generic", "apiAuthorized")]

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

        conclusion = self._build_conclusion_lines(root)

        if conclusion:
            parts.extend(["", *conclusion])

        return _OpsTable.join_markdown_blocks(parts)

    def _build_conclusion_lines(self, root: dict) -> list[str]:
        summary = self._summary(root)
        exclusive_count = int(summary.get("total_exclusive_raw_materials") or 0)
        lines: list[str] = []
        _SHARED_MP_PREVIEW_MAX = 5

        if exclusive_count == 0 and self._items(root):
            lines.append(f"**{self._route('sharedMpConclusionLine')}**")

            shared_count = 0

            for item in self._items(root):
                if not isinstance(item, dict):
                    continue

                if str(item.get("component_type") or "").upper() != "MP":
                    continue

                usage = item.get("total_valid_finished_products_using_mp")

                if usage in (None, "", 0):
                    continue

                if shared_count >= _SHARED_MP_PREVIEW_MAX:
                    remaining = sum(
                        1
                        for candidate in self._items(root)
                        if isinstance(candidate, dict)
                        and str(candidate.get("component_type") or "").upper() == "MP"
                        and candidate.get("total_valid_finished_products_using_mp")
                        not in (None, "", 0)
                    ) - _SHARED_MP_PREVIEW_MAX

                    if remaining > 0:
                        lines.append(
                            self._route("mpMoreLine", count=str(remaining))
                        )

                    break

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
                shared_count += 1

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

        markdown_parts.append(body)

        return {
            "type": "markdown",
            "title": title,
            "markdown": "\n".join(markdown_parts).strip(),
        }

    def build_structure_exclusivity_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_overview_table(root, path)

        if overview:
            overview["role"] = "profile"
            tables.append(overview)

        exclusive_count = self._exclusive_count(root)
        mp_items = enrich_structure_rows(
            self._sort_mp_exclusive_first(self._exclusive_raw_material_items(root))
        )

        if mp_items:
            shown, total = _OpsTable.limit_items(mp_items)
            mp_title = (
                self._route(
                    "exclusiveRawMaterialsTableTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("exclusiveRawMaterialsTableTitle")
            )
            mp_table = _OpsTable.build_items_table(
                self._host.column_label_context,
                shown,
                profile_name="structureExclusivityDetail",
                title=mp_title,
                role="structure",
            )

            if mp_table:
                tables.append(mp_table)

        items = enrich_structure_rows(
            [
                item
                for item in self._items(root)
                if isinstance(item, dict)
            ]
        )
        items.sort(
            key=lambda item: (
                0 if item.get("row_emphasis") else 1,
                int(item.get("level") or 0),
            )
        )

        if exclusive_count > 0 and items and len(items) > len(mp_items):
            shown, total = _OpsTable.limit_items(items)
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

    def _build_overview_table(self, root: dict, path: str) -> dict | None:
        summary = self._summary(root)

        if not summary:
            return None

        columns = self._host._column_labels.kv_table_column_defs()
        rows = _OpsTable.summary_kv_rows(
            self._host.column_label_context,
            summary,
            path=path,
            profile_name="structureExclusivityOverview",
        )

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
