"""Estrutura vigente com exclusividade de MPs (playbook BOM + flag exclusiva)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


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
    ) -> list[str]:
        linhas: list[str] = []

        if description:
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

            for item in exclusive_items[:6]:
                linhas.append(
                    self._route(
                        "exclusiveItemLine",
                        code=str(item.get("product_code") or item.get("component_code") or "—"),
                        quantity=str(item.get("accumulated_quantity") or item.get("quantity") or "—"),
                        level=str(item.get("level") or "—"),
                    )
                )
        elif self._items(root):
            linhas.append(self._route("noExclusiveLine"))
        else:
            linhas.append(self._route("itemsEmptyLine"))

        return linhas or [self._host._presenter_text("generic", "apiAuthorized")]

    def _build_highlights(self, root: dict) -> list[str]:
        highlights: list[str] = []
        summary = self._summary(root)
        exclusive_count = int(summary.get("total_exclusive_raw_materials") or 0)
        raw_materials = int(summary.get("total_raw_materials") or 0)

        highlights.append(
            self._insight(
                "playbookHeadline",
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
    ) -> str:
        parts: list[str] = []
        parts.extend(self._build_narrative_lines(root, code=code, description=description))

        highlights = self._build_highlights(root)

        if highlights:
            parts.extend(["", self._insight("highlightsHeader"), ""])
            parts.extend(f"- {line}" for line in highlights)

        attention = self._build_attention(root)

        if attention:
            parts.extend(["", self._insight("attentionHeader"), ""])
            parts.extend(f"{index}. {line}" for index, line in enumerate(attention, start=1))

        return "\n".join(part for part in parts if part is not None).strip()

    def _build_structure_exclusivity_text_presentation(self, root: dict, path: str) -> dict | None:
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
        body = self._build_markdown_body(root, code=code, description=description)

        if not body:
            return None

        return {
            "type": "markdown",
            "title": title,
            "markdown": f"### {title}\n\n{body}",
        }

    def build_structure_exclusivity_table_presentations(self, root: dict, path: str) -> list[dict]:
        tables: list[dict] = []
        overview = self._build_overview_table(root)

        if overview:
            tables.append(overview)

        items = self._items(root)

        if items:
            table = self._host._build_items_table(
                items,
                title=self._route("componentsTableTitle"),
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

        return {
            "type": "table",
            "title": self._route("overviewTableTitle"),
            "columns": columns,
            "rows": rows,
        }
