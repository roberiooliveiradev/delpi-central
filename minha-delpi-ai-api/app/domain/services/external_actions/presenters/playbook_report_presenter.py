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

    def _playbook_entity_title(self, entity: str, *, table: bool) -> str:
        title_key = "tableTitle" if table else "textTitle"
        title = self._host._presenter_text(
            "playbookReports",
            "entities",
            entity,
            title_key,
        )

        if title:
            return title

        fallback_key = "defaultTableTitle" if table else "defaultTextTitle"
        return self._host._presenter_text("playbookReports", fallback_key)

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
                linhas.append(
                    self._host._presenter_text(
                        "playbookReports",
                        "itemsReturnedLine",
                        count=str(len(items)),
                    )
                )

            if not linhas:
                return None

            title = self._playbook_entity_title(entity, table=False)

            if code:
                title = self._host._presenter_text(
                    "playbookReports",
                    "titleWithCode",
                    title=title,
                    code=code,
                )

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

            return {
                "type": "table",
                "title": self._playbook_entity_title(entity, table=True),
                "columns": columns,
                "rows": rows,
            }
