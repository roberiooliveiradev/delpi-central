"""Apresentação humanizada para respostas composite_analysis (factory-status e similares)."""

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


class ExternalActionProductCompositeAnalysisPresenter:
    """Perfil configurável via `presenter_content.json` — reutilizável por outras APIs."""

    _FACTORY_ENTITY = "product_factory_status"

    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _insight(self, profile: str, key: str, **values: str) -> str:
        return self._host._presenter_text("compositeAnalysisInsights", profile, key, **values)

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

    def _present_factory_status(self, root: dict, path: str) -> dict:
        code, description = self._product_context(root, path)
        linhas = self._build_factory_narrative_lines(root, code=code, description=description)
        markdown_body = self._build_factory_markdown_body(root, code=code, description=description)

        return {
            "titulo": (
                self._route("factoryStatus", "titleWithCode", code=code)
                if code
                else self._route("factoryStatus", "titleGeneric")
            ),
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
            "humanizedMarkdown": markdown_body,
        }

    def _build_factory_narrative_lines(
        self,
        root: dict,
        *,
        code: str,
        description: str,
        compact_for_rich_ui: bool = False,
        skip_product_intro: bool = False,
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
        elif skip_product_intro:
            pass
        elif description:
            linhas.append(
                self._route(
                    "factoryStatus",
                    "introWithDescription",
                    code=code,
                    description=description,
                )
            )
        elif code:
            linhas.append(
                self._route("factoryStatus", "introCodeOnly", code=code)
            )

        status = str(root.get("factory_status") or "").strip()

        if status:
            linhas.append(self._route("factoryStatus", "statusLine", status=status))

        reference_date = str(root.get("reference_date") or "").strip()

        if reference_date:
            linhas.append(
                self._route("factoryStatus", "referenceDateLine", date=reference_date)
            )

        structure_summary = self._section_block(root, "structure").get("summary")

        if isinstance(structure_summary, dict):
            linhas.append(
                self._route(
                    "factoryStatus",
                    "structureSummary",
                    components=str(structure_summary.get("total_components") or 0),
                    intermediates=str(structure_summary.get("total_intermediates") or 0),
                    rawMaterials=str(structure_summary.get("total_raw_materials") or 0),
                    exclusive=str(structure_summary.get("total_exclusive_raw_materials") or 0),
                )
            )

        stock_summary = self._section_block(root, "raw_material_stock").get("summary")

        if isinstance(stock_summary, dict):
            linhas.append(
                self._route(
                    "factoryStatus",
                    "stockSummary",
                    withoutStock=str(stock_summary.get("total_without_stock_for_one_pa") or 0),
                )
            )

        production_summary = self._section_block(root, "production").get("summary")

        if isinstance(production_summary, dict):
            linhas.append(
                self._route(
                    "factoryStatus",
                    "productionSummary",
                    paStarted=_Narrative.format_production_flag(
                        production_summary.get("pa_production_started")
                    ),
                    piStarted=_Narrative.format_production_flag(
                        production_summary.get("pi_production_started")
                    ),
                    paOrders=str(production_summary.get("total_pa_orders") or 0),
                    piOrders=str(production_summary.get("total_pi_orders") or 0),
                )
            )

        shipping_summary = self._section_block(root, "shipping").get("summary")

        if isinstance(shipping_summary, dict):
            linhas.append(
                self._route(
                    "factoryStatus",
                    "shippingSummary",
                    shipped=_Narrative.format_quantity(
                        self._host,
                        shipping_summary.get("total_shipped_quantity"),
                        field_key="total_shipped_quantity",
                    ),
                    loss=_Narrative.format_quantity(
                        self._host,
                        shipping_summary.get("total_inspection_loss_quantity"),
                        field_key="total_inspection_loss_quantity",
                    ),
                )
            )

        if compact_for_rich_ui:
            linhas.append(self._route("factoryStatus", "tableVisualizationHint"))

        return linhas or [self._host._presenter_text("generic", "apiAuthorized")]

    def _resolve_factory_commentary(self, root: dict) -> dict | None:
        from app.domain.services.chat_operational_data_commentary_service import (
            ChatOperationalDataCommentaryService,
        )

        return ChatOperationalDataCommentaryService.build(
            "factory_status",
            root,
            format_quantity=lambda value, field_key=None: _Narrative.format_quantity(
                self._host,
                value,
                field_key=str(field_key or "available_quantity"),
            ),
        )

    def _build_factory_highlights(self, root: dict) -> list[str]:
        commentary = self._resolve_factory_commentary(root)

        if not commentary:
            return []

        return list(commentary.get("highlights") or [])

    def _build_factory_attention(self, root: dict) -> list[str]:
        commentary = self._resolve_factory_commentary(root)

        if not commentary:
            return []

        return list(commentary.get("attention") or [])

    def _build_factory_markdown_body(
        self,
        root: dict,
        *,
        code: str,
        description: str,
        compact_for_rich_ui: bool = False,
        skip_product_intro: bool = False,
    ) -> str:
        parts: list[str] = []
        narrative_lines = self._build_factory_narrative_lines(
            root,
            code=code,
            description=description,
            compact_for_rich_ui=compact_for_rich_ui,
            skip_product_intro=skip_product_intro,
        )

        if narrative_lines:
            parts.append("\n\n".join(line for line in narrative_lines if line))

        commentary = self._resolve_factory_commentary(root)
        highlights = list((commentary or {}).get("highlights") or [])
        attention = list((commentary or {}).get("attention") or [])

        if highlights:
            parts.extend(["", self._insight("factoryStatus", "highlightsHeader"), ""])
            parts.extend(f"- {line}" for line in highlights)

        if attention:
            parts.extend(["", self._insight("factoryStatus", "attentionHeader"), ""])
            parts.extend(f"{index}. {line}" for index, line in enumerate(attention, start=1))

        return _OpsTable.join_markdown_blocks(parts)

    def _build_factory_status_text_presentation(self, root: dict, path: str) -> dict | None:
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
                "factoryStatusWithCode",
                code=code,
            )
            if code
            else self._host._presenter_text(
                "productPresentationTitles",
                "factoryStatusGeneric",
            )
        )
        auxiliary_tables = self.build_factory_status_table_presentations(root, path)
        compact_for_rich_ui = ChatRichPresentationTextService.should_compact_narrative(
            table_presentations=auxiliary_tables,
        )
        scope_line = ""

        if not compact_for_rich_ui:
            scope_line = ChatProductOperationalContentService.get(
                "presenter",
                "factoryStatus",
                "scopeIntro",
            ).strip()

        body = self._build_factory_markdown_body(
            root,
            code=code,
            description=description,
            compact_for_rich_ui=compact_for_rich_ui,
            skip_product_intro=bool(scope_line),
        )

        if not body:
            return None

        markdown_parts = [f"### {title}", ""]

        if scope_line:
            markdown_parts.extend([scope_line, ""])

        markdown_parts.append(body)

        markdown = "\n".join(markdown_parts).strip()
        markdown = self._dedupe_factory_scope_intro(
            markdown,
            scope_line=scope_line,
            code=code,
            description=description,
        )

        return {
            "type": "markdown",
            "title": title,
            "markdown": markdown,
        }

    def _dedupe_factory_scope_intro(
        self,
        markdown: str,
        *,
        scope_line: str,
        code: str,
        description: str,
    ) -> str:
        """Evita escopo genérico + intro do produto na mesma resposta em modo Texto."""
        normalized = str(markdown or "").strip()
        scope = str(scope_line or "").strip()

        if not normalized or not scope:
            return normalized

        candidates: list[str] = []

        if code and description:
            candidates.append(
                self._route(
                    "factoryStatus",
                    "introWithDescription",
                    code=code,
                    description=description,
                )
            )

        if code:
            candidates.append(self._route("factoryStatus", "introCodeOnly", code=code))

        for intro in candidates:
            token = str(intro or "").strip()

            if not token or token not in normalized:
                continue

            normalized = normalized.replace(f"\n\n{token}", "\n", 1)
            normalized = normalized.replace(f"{token}\n\n", "", 1)
            normalized = normalized.replace(token, "", 1)

        return _OpsTable.join_markdown_blocks([normalized])

    def build_factory_status_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_factory_overview_table(root, path)

        if overview:
            overview["role"] = "profile"
            tables.append(overview)

        structure_items = self._section_block(root, "structure").get("items")

        if isinstance(structure_items, list) and structure_items:
            enriched = _OpsTable.enrich_structure_rows(
                [item for item in structure_items if isinstance(item, dict)]
            )
            shown, total = _OpsTable.limit_items(enriched, sort_key="level", reverse=False)
            structure_title = (
                self._route(
                    "factoryStatus",
                    "sectionStructureTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("factoryStatus", "sectionStructureTitle")
            )
            structure_table = _OpsTable.build_items_table(
                self._host,
                shown,
                profile_name="structureExclusivityDetail",
                title=structure_title,
                role="structure",
            )

            if structure_table:
                tables.append(structure_table)

        stock_items = self._section_block(root, "raw_material_stock").get("items")

        if isinstance(stock_items, list) and stock_items:
            mp_summary_table = self._build_factory_mp_stock_summary_table(stock_items)

            if mp_summary_table:
                tables.append(mp_summary_table)

            stock_table = self._build_factory_stock_detail_table(stock_items)

            if stock_table:
                tables.append(stock_table)

        production_items = self._section_block(root, "production").get("items")

        if isinstance(production_items, list) and production_items:
            production_table = self._build_factory_production_table(production_items)

            if production_table:
                tables.append(production_table)

        shipping_items = self._section_block(root, "shipping").get("items")

        if isinstance(shipping_items, list) and shipping_items:
            shipping_dicts = [item for item in shipping_items if isinstance(item, dict)]
            shown, total = _OpsTable.limit_items(
                shipping_dicts,
                sort_key="production_order",
            )
            shipping_title = (
                self._route(
                    "factoryStatus",
                    "sectionShippingTitleTruncated",
                    shown=str(len(shown)),
                    total=str(total),
                )
                if total > len(shown)
                else self._route("factoryStatus", "sectionShippingTitle")
            )
            shipping_table = _OpsTable.build_items_table(
                self._host,
                shown,
                profile_name="shippingStatusDetail",
                title=shipping_title,
                role="other",
            )

            if shipping_table:
                tables.append(shipping_table)

        return [table for table in tables if isinstance(table, dict)]

    def _aggregate_mp_stock_rows(self, stock_items: object) -> list[dict[str, Any]]:
        from app.domain.services.chat_operational_data_commentary_service import (
            ChatOperationalDataCommentaryService,
        )

        return ChatOperationalDataCommentaryService.aggregate_mp_stock_rows(stock_items)

    def _build_factory_mp_stock_summary_table(self, stock_items: list) -> dict | None:
        rows = self._aggregate_mp_stock_rows(stock_items)

        return _OpsTable.build_items_table(
            self._host,
            rows,
            profile_name="factoryMpStockSummary",
            title=self._route("factoryStatus", "sectionMpStockSummaryTitle"),
            role="stock",
        )

    def _build_factory_stock_detail_table(self, stock_items: list) -> dict | None:
        return _OpsTable.build_items_table(
            self._host,
            [item for item in stock_items if isinstance(item, dict)],
            profile_name="factoryRawMaterialStockDetail",
            title=self._route("factoryStatus", "sectionStockTitle"),
            role="stock",
        )

    def _build_factory_production_table(self, production_items: list) -> dict | None:
        items = [item for item in production_items if isinstance(item, dict)]
        shown_items, total = _OpsTable.limit_items(items, sort_key="production_order")
        title = (
            self._route(
                "factoryStatus",
                "sectionProductionTitleTruncated",
                shown=str(len(shown_items)),
                total=str(total),
            )
            if total > len(shown_items)
            else self._route("factoryStatus", "sectionProductionTitle")
        )

        return _OpsTable.build_items_table(
            self._host,
            shown_items,
            profile_name="factoryProductionDetail",
            title=title,
            role="list",
        )

    def _build_factory_overview_table(self, root: dict, path: str) -> dict | None:
        code, description = self._product_context(root, path)
        columns = self._host._column_labels.kv_table_column_defs()
        rows = [
            {
                "campo": "Situação consolidada",
                "valor": str(root.get("factory_status") or "—"),
            },
            {
                "campo": "Produto",
                "valor": f"{code} — {description}".strip(" —") or code or "—",
            },
        ]

        reference_date = str(root.get("reference_date") or "").strip()

        if reference_date:
            rows.append({"campo": "Referência", "valor": reference_date})

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}

        for key, value in list(indicators.items())[:8]:
            rows.append(
                {
                    "campo": self._host._column_labels.label_for(str(key)),
                    "valor": self._host._format_field_value(str(key), value),
                }
            )

        return {
            "type": "table",
            "title": self._route("factoryStatus", "overviewTableTitle"),
            "columns": columns,
            "rows": rows,
            "role": "profile",
        }

    def build_factory_kpi_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_kpi(
            self._host,
            root,
            path,
            profile_key="factory_status"
        )


    def build_factory_chart_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_chart(
            self._host,
            root,
            path,
            profile_key="factory_status",
        )

    def build_factory_tree_presentation(self, root: dict, path: str) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_tree(
            self._host,
            root,
            path,
            profile_key="factory_status"
        )

    def build_factory_dashboard_presentation(self, root: dict, path: str, *, kpi: dict | None = None, tree: dict | None = None, chart: dict | None = None, table: dict | None = None) -> dict | None:
        from app.domain.services.chat_presentation_profile_composite_visual_service import (
            ChatPresentationProfileCompositeVisualService,
        )

        return ChatPresentationProfileCompositeVisualService.build_dashboard(
            self._host,
            root,
            path,
            profile_key="factory_status",
            kpi=kpi,
            tree=tree,
            chart=chart,
            table=table
        )
