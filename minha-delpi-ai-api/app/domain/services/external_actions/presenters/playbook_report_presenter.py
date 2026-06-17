"""Relatórios playbook (situação produtiva, expedição, exclusividade) — Fase 3A lote 9"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.services.chat_operational_result_completeness_service import (
    ChatOperationalResultCompletenessService,
)

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
                    if key in {"is_complete", "branch_filter_applied"}:
                        continue

                    linhas.append(
                        f"{self._host._humanize_key(str(key))}: {self._host._format_field_value(str(key), value)}"
                    )

            incomplete_lines = ChatOperationalResultCompletenessService.build_notice_lines(
                root,
                text=lambda key, **values: self._host._presenter_text(
                    "playbookReports",
                    key,
                    **values,
                ),
            )
            linhas.extend(incomplete_lines)

            if items:
                for item in items[:12]:
                    if not isinstance(item, dict):
                        continue

                    label = str(item.get("description") or "").strip()

                    if not label:
                        for key in (
                            "product_code",
                            "item_code",
                            "material_code",
                            "component_code",
                            "production_order",
                            "work_center",
                        ):
                            token = str(item.get(key) or "").strip()

                            if token:
                                label = token
                                break

                    if label:
                        linhas.append(f"- {label}")

                if len(items) > 12:
                    linhas.append(
                        self._host._presenter_text(
                            "playbookReports",
                            "itemsReturnedLine",
                            count=str(len(items)),
                        )
                    )
                elif not linhas:
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
                title = self._playbook_entity_title(entity, table=True)
                table = self._host._build_items_table(items, title=title, path=path)

                if table and ChatOperationalResultCompletenessService.is_incomplete(root):
                    notice_lines = ChatOperationalResultCompletenessService.build_notice_lines(
                        root,
                        text=lambda key, **values: self._host._presenter_text(
                            "playbookReports",
                            key,
                            **values,
                        ),
                    )

                    if notice_lines:
                        table = dict(table)
                        table["incompleteNotice"] = " ".join(notice_lines)

                return table

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
