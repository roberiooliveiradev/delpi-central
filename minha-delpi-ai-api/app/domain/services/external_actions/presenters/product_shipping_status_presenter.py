"""Expedição / inspeção final do PA (playbook SHB010 + SH6010) — perfil generalizável."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


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

        period_line = self._period_label(root)

        if period_line:
            linhas.append(period_line)

        summary = self._summary(root)

        if summary:
            linhas.append(
                self._route(
                    "shippedLine",
                    value=str(summary.get("total_shipped_quantity") or 0),
                )
            )
            linhas.append(
                self._route(
                    "lossLine",
                    value=str(summary.get("total_inspection_loss_quantity") or 0),
                )
            )
            linhas.append(
                self._route(
                    "reportsLine",
                    value=str(summary.get("total_reports") or 0),
                )
            )

        items = self._items(root)

        if items:
            linhas.append(self._route("itemsPreviewLine", count=str(len(items))))

            for item in items[:6]:
                if not isinstance(item, dict):
                    continue

                linhas.append(
                    self._route(
                        "movementLine",
                        order=str(item.get("production_order") or "—"),
                        shipped=str(item.get("shipped_quantity") or "0"),
                        loss=str(item.get("inspection_loss_quantity") or "0"),
                    )
                )
        else:
            linhas.append(self._route("itemsEmptyLine"))

        return linhas or [self._host._presenter_text("generic", "apiAuthorized")]

    def _build_highlights(self, root: dict) -> list[str]:
        highlights: list[str] = []
        period = self._period_label(root) or "—"
        highlights.append(self._insight("playbookHeadline", period=period))

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
            highlights.append(self._insight("hasShipped", quantity=str(summary.get("total_shipped_quantity") or 0)))

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

    def _build_shipping_status_text_presentation(self, root: dict, path: str) -> dict | None:
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
        body = self._build_markdown_body(root, code=code, description=description)

        if not body:
            return None

        return {
            "type": "markdown",
            "title": title,
            "markdown": f"### {title}\n\n{body}",
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
