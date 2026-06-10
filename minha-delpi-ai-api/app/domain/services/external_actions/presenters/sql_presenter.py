"""Resultados SQL do ExternalActionResultPresenter — Fase 3A lote 7."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionSqlPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _present_sql_rows(self, rows: list) -> dict | None:
            if isinstance(rows, dict):
                rows = ExternalActionSqlPresenter._coerce_sql_row_list(rows)

            if not isinstance(rows, list):
                return None

            default_title = ExternalActionResponseContentService.get("sql", "defaultTitle")

            if not rows:
                return {
                    "titulo": default_title,
                    "linhas": [
                        ExternalActionResponseContentService.get("sql", "emptyNoRows")
                    ],
                    "dados": {"rows": []},
                }

            if not isinstance(rows[0], dict):
                return {
                    "titulo": default_title,
                    "linhas": [
                        ExternalActionResponseContentService.format(
                            "sql",
                            "rowsCount",
                            count=len(rows),
                        )
                    ],
                    "dados": {"rows": rows},
                }

            return self._present_sql_dict_rows(rows)

    def _present_sql_resultsets(self, root: dict, path: str) -> dict | None:
            resultsets = root.get("resultsets")

            if not isinstance(resultsets, list):
                return None

            rows = self._collect_sql_resultset_rows(resultsets)
            record_total = ExternalActionSqlPresenter._sql_resultset_record_total(resultsets)
            title = self._sql_result_title(root, path)

            if not rows:
                return {
                    "titulo": title,
                    "linhas": [self._sql_empty_message(root, path)],
                    "dados": root,
                    "sqlRows": [],
                }

            presented = self._present_sql_dict_rows(
                rows,
                title=title,
                record_total=record_total,
                root=root,
            )
            presented["dados"] = root
            presented["sqlRows"] = rows
            return presented

    def _collect_sql_resultset_rows(self, resultsets: list) -> list[dict]:
            rows: list[dict] = []

            for resultset in resultsets:
                if not isinstance(resultset, dict):
                    continue

                data = resultset.get("data")

                if not isinstance(data, list):
                    continue

                for row in data:
                    if isinstance(row, dict):
                        rows.append(row)

            return rows

    @staticmethod
    def _sql_resultset_record_total(resultsets: list) -> int | None:
            best: int | None = None

            for resultset in resultsets:
                if not isinstance(resultset, dict):
                    continue

                try:
                    total = int(resultset.get("total"))
                except (TypeError, ValueError):
                    continue

                if total < 0:
                    continue

                best = max(best or 0, total)

            return best

    def _sql_result_title(self, root: dict, path: str) -> str:
            if self._looks_like_inventory_below_minimum_sql_context(root, path):
                return ExternalActionResponseContentService.get(
                    "inventoryBelowMinimum",
                    "title",
                )

            if self._looks_like_production_sql_context(root, path):
                schedule = self._resolve_production_schedule_from_root(root)

                if schedule and self._looks_like_production_branch_breakdown(root):
                    return ExternalActionResponseContentService.format(
                        "productionSchedule",
                        "titleByBranchBreakdown",
                        default=f"{schedule.title} — por filial",
                        label=schedule.label,
                    )

                if schedule:
                    return schedule.title

                return ExternalActionResponseContentService.get(
                    "productionSchedule",
                    "titleTodayFallback",
                )

            if ExternalActionSqlCapabilityService.is_sql_execution_context(path=path) or (
                ExternalActionSqlCapabilityService.is_sql_result_payload(root)
            ):
                return ExternalActionResponseContentService.get("sql", "defaultTitle")

            return ExternalActionResponseContentService.get("sql", "defaultTitle")

    def _sql_empty_message(self, root: dict, path: str) -> str:
            if self._looks_like_inventory_below_minimum_sql_context(root, path):
                return ExternalActionResponseContentService.get(
                    "inventoryBelowMinimum",
                    "emptyMessage",
                )

            if self._looks_like_production_sql_context(root, path):
                schedule = self._resolve_production_schedule_from_root(root)
                if schedule:
                    return schedule.empty_message
                return ExternalActionResponseContentService.get(
                    "productionSchedule",
                    "emptyTodayFallback",
                )

            if ExternalActionSqlCapabilityService.is_sql_execution_context(path=path) or (
                ExternalActionSqlCapabilityService.is_sql_result_payload(root)
            ):
                total = root.get("total_resultsets")

                if total is not None:
                    return ExternalActionResponseContentService.format(
                        "sql",
                        "emptyWithResultsets",
                        total=total,
                    )

                return ExternalActionResponseContentService.get("sql", "emptyNoRows")

            total = root.get("total_resultsets")

            if total is not None:
                return ExternalActionResponseContentService.format(
                    "sql",
                    "emptyWithResultsets",
                    total=total,
                )

            return ExternalActionResponseContentService.get("sql", "emptyNoRows")

    def _resolve_production_schedule_from_root(self, root: dict):
            from app.domain.services.chat_sql_production_schedule_date_service import (
                ChatSqlProductionScheduleDateService,
            )

            if not isinstance(root, dict):
                return None

            for key in ("sql", "query", "statement", "executedSql"):
                value = root.get(key)
                if isinstance(value, str) and value.strip():
                    return ChatSqlProductionScheduleDateService.infer_from_sql(value)

            dados = root.get("dados")

            if isinstance(dados, dict):
                for key in ("sql", "query", "statement", "executedSql"):
                    value = dados.get(key)

                    if isinstance(value, str) and value.strip():
                        return ChatSqlProductionScheduleDateService.infer_from_sql(value)

            return None

    def _looks_like_production_sql_context(self, root: dict, path: str) -> bool:
            rows = self._collect_sql_resultset_rows(root.get("resultsets") or [])

            if rows and self._looks_like_production_schedule_row(rows[0]):
                return True

            resultsets = root.get("resultsets") if isinstance(root, dict) else None
            if isinstance(resultsets, list):
                for resultset in resultsets:
                    if not isinstance(resultset, dict):
                        continue
                    columns = resultset.get("columns") or []
                    if any(
                        column in columns
                        for column in (
                            "COD_PRODUTO",
                            "DESCRICAO_PRODUTO",
                            "QTD_PLANEJADA",
                        )
                    ):
                        return True

            if not isinstance(root, dict):
                return False

            for key in ("sql", "query", "statement"):
                value = root.get(key)
                if isinstance(value, str) and ExternalActionSqlCapabilityService.looks_like_production_schedule_sql(
                    value
                ):
                    return True

            return False

    def _looks_like_inventory_below_minimum_sql_context(self, root: dict, path: str) -> bool:
            rows = self._collect_sql_resultset_rows(root.get("resultsets") or [])

            if rows and self._looks_like_inventory_below_minimum_row(rows[0]):
                return True

            resultsets = root.get("resultsets") if isinstance(root, dict) else None

            if isinstance(resultsets, list):
                for resultset in resultsets:
                    if not isinstance(resultset, dict):
                        continue

                    columns = {
                        str(column).lower()
                        for column in (resultset.get("columns") or [])
                    }

                    if {"product_code", "minimum_stock"}.issubset(columns):
                        return True

            if not isinstance(root, dict):
                return False

            for key in ("sql", "query", "statement"):
                value = root.get(key)

                if isinstance(value, str) and ExternalActionSqlCapabilityService.looks_like_inventory_below_minimum_sql(
                    value
                ):
                    return True

            return False

    def _looks_like_inventory_below_minimum_row(self, row: dict) -> bool:
            if not isinstance(row, dict):
                return False

            keys = {str(key).lower() for key in row.keys()}

            return "product_code" in keys and (
                "minimum_stock" in keys or "available_quantity" in keys
            )

    def _present_sql_dict_rows(
            self,
            rows: list[dict],
            *,
            title: str | None = None,
            record_total: int | None = None,
            root: dict | None = None,
        ) -> dict:
            resolved_title = title or ExternalActionResponseContentService.get(
                "sql",
                "defaultTitle",
            )
            shown = len(rows)
            total_count = record_total if record_total is not None and record_total >= shown else shown

            if rows and self._looks_like_production_schedule_row(rows[0]):
                from app.domain.services.chat_sql_production_schedule_presentation_service import (
                    ChatSqlProductionSchedulePresentationService,
                )

                schedule = self._resolve_production_schedule_from_root(root or {})
                linhas = ChatSqlProductionSchedulePresentationService.build_linhas(
                    rows,
                    schedule=schedule,
                    record_total=total_count,
                    include_branch_breakdown=self._looks_like_production_branch_breakdown(
                        root or {}
                    ),
                    format_row=self._format_production_schedule_row,
                )

                return {
                    "titulo": resolved_title,
                    "linhas": linhas,
                    "dados": {"rows": rows, "total": total_count, "shown": shown},
                    "sqlRows": rows,
                }

            linhas = [
                ExternalActionResponseContentService.format(
                    "sql",
                    "rowsCount",
                    count=total_count,
                )
            ]

            if total_count > shown:
                linhas.append(
                    ExternalActionResponseContentService.format(
                        "sql",
                        "moreProducts",
                        count=total_count - shown,
                    )
                )

            return {
                "titulo": resolved_title,
                "linhas": linhas,
                "dados": {"rows": rows, "total": total_count, "shown": shown},
                "sqlRows": rows,
            }

    def _looks_like_production_schedule_row(self, row: dict) -> bool:
            if not isinstance(row, dict):
                return False

            keys = {str(key).upper() for key in row.keys()}

            return "COD_PRODUTO" in keys and (
                "DESCRICAO_PRODUTO" in keys or "QTD_PLANEJADA" in keys
            )

    def _looks_like_production_branch_breakdown(self, root: dict) -> bool:
            rows = self._collect_sql_resultset_rows(root.get("resultsets") or [])

            if rows and "FILIAL" in {str(key).upper() for key in rows[0].keys()}:
                return True

            if not isinstance(root, dict):
                return False

            for key in ("sql", "query", "statement", "executedSql"):
                value = root.get(key)

                if isinstance(value, str) and self._looks_like_production_branch_breakdown_sql(
                    value
                ):
                    return True

            dados = root.get("dados")

            if isinstance(dados, dict):
                for key in ("sql", "query", "statement", "executedSql"):
                    value = dados.get(key)

                    if isinstance(value, str) and self._looks_like_production_branch_breakdown_sql(
                        value
                    ):
                        return True

            return False

    @staticmethod
    def _looks_like_production_branch_breakdown_sql(sql: str) -> bool:
            normalized = str(sql or "").upper()

            if "C2_FILIAL AS FILIAL" in normalized:
                return True

            return "C2_FILIAL IN (" in normalized

    def _format_production_schedule_row(self, row: dict) -> str:
            code = str(
                row.get("COD_PRODUTO")
                or row.get("cod_produto")
                or "?"
            ).strip()
            description = str(
                row.get("DESCRICAO_PRODUTO")
                or row.get("descricao_produto")
                or ""
            ).strip()
            quantity = row.get("QTD_PLANEJADA")
            unit = str(row.get("UNIDADE") or row.get("unidade") or "").strip()
            start_at = row.get("DATA_INICIO_OPERACAO") or row.get("data_inicio_operacao")

            parts = [
                ExternalActionResponseContentService.format(
                    "productionSchedule",
                    "rowCode",
                    code=code,
                )
            ]

            if description:
                parts.append(description)

            line = ExternalActionResponseContentService.get(
                "productionSchedule",
                "rowSeparator",
            ).join(parts)

            if quantity is not None:
                qty_text = self._host._format_num(quantity)
                unit_suffix = f" {unit}".rstrip()
                line += ExternalActionResponseContentService.format(
                    "productionSchedule",
                    "rowQuantity",
                    quantity=qty_text,
                    unit_suffix=unit_suffix,
                )

            if start_at:
                line += (
                    ExternalActionResponseContentService.get(
                        "sql",
                        "operationStartPrefix",
                    )
                    + str(start_at)
                )

            return line

    def _build_sql_resultset_empty_table(
            self,
            root: dict,
            *,
            title: str,
            path: str = "",
        ) -> dict | None:
            resultsets = root.get("resultsets")

            if not isinstance(resultsets, list) or not resultsets:
                return None

            first = resultsets[0]

            if not isinstance(first, dict):
                return None

            columns_raw = first.get("columns")

            if not isinstance(columns_raw, list) or not columns_raw:
                return None

            sample = {str(column): None for column in columns_raw}
            profile_name = self._host._column_labels.detect_table_profile(sample, path=path)
            preferred = None

            if profile_name:
                preferred = self._host._column_labels.preferred_columns(
                    profile_name,
                    sample,
                    schema_labels=self._host._active_schema_labels,
                )

            if preferred:
                columns = [
                    self._host._enrich_column(key, label)
                    for key, label in preferred
                ]
            else:
                columns = [
                    self._host._enrich_column(str(column), self._host._humanize_key(str(column)))
                    for column in columns_raw[:15]
                ]

            return {
                "type": "table",
                "title": title,
                "columns": columns,
                "rows": [],
            }

    @staticmethod
    def _coerce_sql_row_list(root: dict) -> list | None:
        rows = root.get("rows")

        if isinstance(rows, list):
            return rows

        items = root.get("items")

        if isinstance(items, list):
            return items

        return None
