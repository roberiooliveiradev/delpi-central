"""Relatórios playbook (situação produtiva, expedição, exclusividade) — Fase 3A lote 9"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionPlaybookReportPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _present_playbook_report(
            self,
            root: dict,
            path: str,
            *,
            entity: str,
        ) -> dict | None:
            product = root.get("product") if isinstance(root.get("product"), dict) else {}
            code = str(product.get("product_code") or product.get("code") or "").strip()
            summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
            items = root.get("items") if isinstance(root.get("items"), list) else []
            linhas: list[str] = []

            if summary:
                for key, value in list(summary.items())[:8]:
                    linhas.append(
                        f"{self._host._humanize_key(str(key))}: {self._host._format_field_value(str(key), value)}"
                    )

            if items:
                linhas.append(f"Itens retornados: {len(items)}")

            if not linhas:
                return None

            titles = {
                "product_production_status": "Situação produtiva",
                "product_shipping_status": "Status de expedição",
                "product_structure_exclusivity": "Estrutura com exclusividade",
            }

            title = titles.get(entity, "Relatório do produto")

            if code:
                title = f"{title} — {code}"

            return {
                "titulo": title,
                "linhas": linhas,
                "dados": root,
                "sourcePath": path,
            }

    def _build_playbook_report_table(
            self,
            root: dict,
            path: str,
            *,
            entity: str,
        ) -> dict | None:
            summary = root.get("summary") if isinstance(root.get("summary"), dict) else None
            items = root.get("items") if isinstance(root.get("items"), list) else None

            if items and isinstance(items[0], dict):
                title = self._host._infer_items_title(items, path)
                return self._host._build_items_table(items, title=title, path=path)

            if not summary:
                return None

            columns = self._host._column_labels.kv_table_column_defs()
            rows = [
                {"campo": self._host._humanize_key(str(key)), "valor": str(value)}
                for key, value in summary.items()
            ]

            titles = {
                "product_production_status": "Situação produtiva",
                "product_shipping_status": "Expedição",
                "product_structure_exclusivity": "Exclusividade de MPs",
            }

            return {
                "type": "table",
                "title": titles.get(entity, "Relatório"),
                "columns": columns,
                "rows": rows,
            }
