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
            from app.domain.services.chat_production_schedule_membership_presentation_service import (
                ChatProductionScheduleMembershipPresentationService,
            )

            membership = ChatProductionScheduleMembershipPresentationService.try_build_playbook_report(
                root,
                entity=entity,
            )

            if membership:
                membership["sourcePath"] = path
                return membership

            product = root.get("product") if isinstance(root.get("product"), dict) else {}
            code = str(product.get("product_code") or product.get("code") or "").strip()
            summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
            items = root.get("items") if isinstance(root.get("items"), list) else []
            linhas: list[str] = []

            if summary:
                from app.domain.services.chat_operational_summary_semantics_service import (
                    ChatOperationalSummarySemanticsService,
                )

                filtered = ChatOperationalSummarySemanticsService.filter_summary(summary)

                for key, value in list(filtered.items())[:8]:
                    linhas.append(
                        f"{self._host._humanize_key(str(key))}: {self._host._format_field_value(str(key), value)}"
                    )

            if items:
                for item in items[:12]:
                    if not isinstance(item, dict):
                        continue

                    product_code = str(
                        item.get("product_code")
                        or item.get("item_code")
                        or item.get("material_code")
                        or item.get("component_code")
                        or "",
                    ).strip()
                    description = str(item.get("description") or "").strip()
                    label = ""

                    if product_code and description:
                        label = f"{product_code} — {description}"
                    elif description:
                        label = description
                    elif product_code:
                        label = product_code

                    if not label:
                        for key in (
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
                return self._host._build_items_table(items, title=title, path=path)

            if not summary:
                return None

            from app.domain.services.chat_operational_summary_semantics_service import (
                ChatOperationalSummarySemanticsService,
            )

            columns = self._host._column_labels.kv_table_column_defs()
            rows = [
                {"campo": self._host._humanize_key(str(key)), "valor": str(value)}
                for key, value in ChatOperationalSummarySemanticsService.filter_summary(
                    summary,
                ).items()
            ]

            return {
                "type": "table",
                "title": self._playbook_entity_title(entity, table=True),
                "columns": columns,
                "rows": rows,
            }
