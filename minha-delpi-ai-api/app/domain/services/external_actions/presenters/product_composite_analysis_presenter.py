"""Apresentação humanizada para respostas composite_analysis (factory-status e similares)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


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
    ) -> list[str]:
        linhas: list[str] = []

        if description:
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
                    paStarted=str(production_summary.get("pa_production_started") or "—"),
                    piStarted=str(production_summary.get("pi_production_started") or "—"),
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
                    shipped=str(shipping_summary.get("total_shipped_quantity") or 0),
                    loss=str(shipping_summary.get("total_inspection_loss_quantity") or 0),
                )
            )

        return linhas or [self._host._presenter_text("generic", "apiAuthorized")]

    def _build_factory_highlights(self, root: dict) -> list[str]:
        highlights: list[str] = []
        status = str(root.get("factory_status") or "").strip()

        if status:
            highlights.append(
                self._insight("factoryStatus", "headlineStatus", status=status)
            )

        if "SEM ESTRUTURA" in status.upper():
            highlights.append(self._insight("factoryStatus", "noStructure"))

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}
        without_stock = indicators.get("total_raw_materials_without_stock_for_one_pa")

        if without_stock not in (None, "", 0, "0"):
            highlights.append(
                self._insight(
                    "factoryStatus",
                    "exclusiveWithoutStock",
                    count=str(without_stock),
                )
            )

        production_summary = self._section_block(root, "production").get("summary")

        if isinstance(production_summary, dict):
            total_orders = int(production_summary.get("total_pa_orders") or 0) + int(
                production_summary.get("total_pi_orders") or 0
            )
            pa_started = str(production_summary.get("pa_production_started") or "").upper()
            pi_started = str(production_summary.get("pi_production_started") or "").upper()

            if total_orders == 0 and "SEM ESTRUTURA" not in status.upper():
                highlights.append(self._insight("factoryStatus", "noProductionOrders"))
            elif pa_started not in {"SIM", "SIM_SC2"} and pi_started not in {"SIM", "SIM_SC2"} and total_orders > 0:
                highlights.append(self._insight("factoryStatus", "productionNotStarted"))
            else:
                highlights.append(
                    self._insight(
                        "factoryStatus",
                        "productionStarted",
                        pa=pa_started or "NAO",
                        pi=pi_started or "NAO",
                    )
                )

        shipping_summary = self._section_block(root, "shipping").get("summary")

        if isinstance(shipping_summary, dict):
            shipped = float(shipping_summary.get("total_shipped_quantity") or 0)

            if shipped > 0:
                highlights.append(
                    self._insight(
                        "factoryStatus",
                        "shippingWithMovement",
                        shipped=str(shipped),
                    )
                )
            else:
                highlights.append(self._insight("factoryStatus", "shippingNoMovement"))

        return highlights

    def _build_factory_attention(self, root: dict) -> list[str]:
        attention: list[str] = []
        status = str(root.get("factory_status") or "").strip()

        if "SEM ESTRUTURA" in status.upper():
            attention.append(self._insight("factoryStatus", "attentionNoStructure"))

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}
        without_stock = indicators.get("total_raw_materials_without_stock_for_one_pa")

        if without_stock not in (None, "", 0, "0"):
            attention.append(self._insight("factoryStatus", "attentionExclusiveStock"))

        if "NÃO INICIADO" in status.upper() or "NAO INICIADO" in status.upper():
            attention.append(self._insight("factoryStatus", "attentionOpNotStarted"))

        return attention

    def _build_factory_markdown_body(
        self,
        root: dict,
        *,
        code: str,
        description: str,
    ) -> str:
        parts: list[str] = []
        parts.extend(self._build_factory_narrative_lines(root, code=code, description=description))

        highlights = self._build_factory_highlights(root)

        if highlights:
            parts.extend(["", self._insight("factoryStatus", "highlightsHeader"), ""])
            parts.extend(f"- {line}" for line in highlights)

        attention = self._build_factory_attention(root)

        if attention:
            parts.extend(["", self._insight("factoryStatus", "attentionHeader"), ""])
            parts.extend(f"{index}. {line}" for index, line in enumerate(attention, start=1))

        return "\n".join(part for part in parts if part is not None).strip()

    def _build_factory_status_text_presentation(self, root: dict, path: str) -> dict | None:
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
        body = self._build_factory_markdown_body(root, code=code, description=description)

        if not body:
            return None

        return {
            "type": "markdown",
            "title": title,
            "markdown": f"### {title}\n\n{body}",
        }

    def build_factory_status_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_factory_overview_table(root, path)

        if overview:
            tables.append(overview)

        structure_items = self._section_block(root, "structure").get("items")

        if isinstance(structure_items, list) and structure_items:
            tables.append(
                self._host._build_items_table(
                    structure_items,
                    title=self._route("factoryStatus", "sectionStructureTitle"),
                    path=path,
                )
            )

        stock_items = self._section_block(root, "raw_material_stock").get("items")

        if isinstance(stock_items, list) and stock_items:
            tables.append(
                self._host._build_items_table(
                    stock_items,
                    title=self._route("factoryStatus", "sectionStockTitle"),
                    path=path,
                )
            )

        production_items = self._section_block(root, "production").get("items")

        if isinstance(production_items, list) and production_items:
            tables.append(
                self._host._build_items_table(
                    production_items,
                    title=self._route("factoryStatus", "sectionProductionTitle"),
                    path=path,
                )
            )

        shipping_items = self._section_block(root, "shipping").get("items")

        if isinstance(shipping_items, list) and shipping_items:
            tables.append(
                self._host._build_items_table(
                    shipping_items,
                    title=self._route("factoryStatus", "sectionShippingTitle"),
                    path=path,
                )
            )

        return [table for table in tables if isinstance(table, dict)]

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
                    "campo": self._host._humanize_key(str(key)),
                    "valor": self._host._format_field_value(str(key), value),
                }
            )

        return {
            "type": "table",
            "title": self._route("factoryStatus", "overviewTableTitle"),
            "columns": columns,
            "rows": rows,
        }
