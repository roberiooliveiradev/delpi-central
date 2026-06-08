"""Billing, estoque valorizado e PMR — Fase 3A lote 8"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionBillingPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _present_stock_value_summary(
            self,
            root: dict,
            path: str,
            *,
            entity: str | None = None,
        ) -> dict | None:
            if entity != "supplies_stock_value" and "stock-value" not in str(path or "").lower():
                return None

            summary = root.get("summary")

            if not isinstance(summary, dict):
                return None

            title = self._host._kpi_title(path)
            linhas = self._stock_value_summary_lines(summary, root.get("by_branch"))

            kpi = self._build_stock_value_kpi(root, path)

            return {
                "titulo": title,
                "linhas": linhas,
                "dados": root,
                "apresentacao": kpi,
            }

    def _present_product_billing_summary(
            self,
            root: dict,
            path: str,
            *,
            entity: str | None = None,
        ) -> dict | None:
            lowered = str(path or "").lower()

            if entity != "product_billing" and "/sales/billing" not in lowered:
                return None

            if "value" not in root and "documents" not in root:
                return None

            title = self._billing_title(path)
            linhas: list[str] = []

            if root.get("value") is not None:
                linhas.append(
                    self._host._presenter_text(
                        "productBilling",
                        "billedValue",
                        value=self._host._format_currency(root.get("value")),
                    )
                )

            if root.get("documents") is not None:
                linhas.append(
                    self._host._presenter_text(
                        "productBilling",
                        "documents",
                        count=str(root.get("documents")),
                    )
                )

            first_date = self._host._format_protheus_date(root.get("first_billing_date"))

            if first_date:
                linhas.append(
                    self._host._presenter_text("productBilling", "firstIssue", date=first_date)
                )

            last_date = self._host._format_protheus_date(root.get("last_billing_date"))

            if last_date:
                linhas.append(
                    self._host._presenter_text("productBilling", "lastIssue", date=last_date)
                )

            return {
                "titulo": title,
                "linhas": linhas,
                "dados": root,
            }

    def _present_financial_pmr(
            self,
            root: dict,
            path: str,
            *,
            entity: str | None = None,
        ) -> dict | None:
            if entity != "financial_pmr" and "pmr" not in str(path or "").lower():
                return None

            if "branch" not in root and "pmr_days" not in root:
                return None

            title = self._host._kpi_title(path)
            branch = str(
                root.get("branch")
                or self._host._presenter_text("financialPmr", "branchFallback")
            ).strip()
            linhas = [
                self._host._presenter_text("financialPmr", "branchLine", branch=branch)
            ]
            pmr_days = root.get("pmr_days")

            if pmr_days is None:
                linhas.append(self._host._analyser_markdown("pmrUnavailable"))
            else:
                linhas.append(
                    self._host._presenter_text(
                        "financialPmr",
                        "pmrLine",
                        days=self._host._format_num(pmr_days),
                    )
                )

            return {
                "titulo": title,
                "linhas": linhas,
                "dados": root,
            }

    def _build_stock_value_kpi(self, root: dict, path: str) -> dict | None:
            summary = root.get("summary")

            if not isinstance(summary, dict):
                return None

            cards = self._host._kpi_chart().kpi_cards_from_presenter_section("stockValue", summary)

            if not cards:
                return None

            return {
                "type": "kpi",
                "title": self._host._kpi_chart().kpi_title(path),
                "cards": cards,
            }

    def _build_stock_value_branch_table(
            self,
            root: dict,
            path: str,
            *,
            entity: str | None = None,
        ) -> dict | None:
            if entity != "supplies_stock_value" and "stock-value" not in str(path or "").lower():
                return None

            by_branch = root.get("by_branch")

            if not isinstance(by_branch, list):
                return None

            rows = [
                item
                for item in by_branch
                if isinstance(item, dict) and str(item.get("branch") or "").strip()
            ]

            if not rows:
                return None

            return {
                "type": "table",
                "title": self._host._presenter_text("stockValue", "branchTableTitle"),
                "columns": self._host._fixed_columns("stockValueByBranch"),
                "rows": rows,
            }

    def _build_product_billing_table(
            self,
            root: dict,
            path: str,
            *,
            entity: str | None = None,
        ) -> dict | None:
            if entity != "product_billing" and "/sales/billing" not in str(path or "").lower():
                return None

            if root.get("value") is None and root.get("documents") is None:
                return None

            return {
                "type": "table",
                "title": self._billing_title(path),
                "columns": self._host._column_labels.kv_table_column_defs(),
                "rows": self._billing_table_rows(root),
            }

    def _billing_title(self, path: str) -> str:
            product_code = self._host._extract_product_code_from_path(path)

            if product_code:
                return self._host._presenter_text(
                    "productBilling",
                    "titleWithCode",
                    code=product_code,
                )

            return self._host._presenter_text("productBilling", "titleGeneric")

    def _billing_table_rows(self, root: dict) -> list[dict]:
            from app.domain.services.chat_assistant_content_service import (
                ChatAssistantContentService,
            )

            rows_cfg = ChatAssistantContentService.get_node(
                "presenter_content",
                "productBilling",
                "tableRows",
            )

            if not isinstance(rows_cfg, list):
                return []

            rows: list[dict] = []

            for item in rows_cfg:
                if not isinstance(item, dict):
                    continue

                root_key = str(item.get("rootKey") or "").strip()
                campo = str(item.get("campo") or "").strip()

                if not root_key or not campo:
                    continue

                valor = root.get(root_key)
                valor_type = item.get("valorType")

                if valor_type == "date":
                    valor = self._host._format_protheus_date(valor)

                row: dict = {"campo": campo, "valor": valor}

                if isinstance(valor_type, str) and valor_type.strip():
                    row["valorType"] = valor_type.strip()

                rows.append(row)

            return rows

    def _stock_value_summary_lines(
            self,
            summary: dict,
            by_branch: object,
        ) -> list[str]:
            linhas = [
                self._host._presenter_text(
                    "stockValue",
                    "summaryLines",
                    "totalValue",
                    value=self._host._format_currency(summary.get("total_stock_value")),
                ),
                self._host._presenter_text(
                    "stockValue",
                    "summaryLines",
                    "totalQuantity",
                    qty=self._host._format_num(summary.get("total_stock_quantity")),
                ),
                self._host._presenter_text(
                    "stockValue",
                    "summaryLines",
                    "distinctProducts",
                    count=str(summary.get("total_products")),
                ),
                self._host._presenter_text(
                    "stockValue",
                    "summaryLines",
                    "records",
                    count=str(summary.get("total_records")),
                ),
                self._host._presenter_text(
                    "stockValue",
                    "summaryLines",
                    "locations",
                    count=str(summary.get("total_locations")),
                ),
            ]

            if isinstance(by_branch, list):
                for item in by_branch:
                    if not isinstance(item, dict):
                        continue

                    branch = str(item.get("branch") or "").strip()

                    if not branch:
                        continue

                    linhas.append(
                        self._host._presenter_text(
                            "stockValue",
                            "summaryLines",
                            "branchItem",
                            branch=branch,
                            value=self._host._format_currency(item.get("total_stock_value")),
                            qty=self._host._format_num(item.get("total_stock_quantity")),
                        )
                    )

            return linhas
