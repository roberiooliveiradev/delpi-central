"""Tabelas e colunas Protheus (SX2/SX3) — Fase 3A lote 8"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionSystemTablesPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _present_system_tables_search(
            self,
            root: dict,
            path: str,
            *,
            entity: str | None = None,
        ) -> dict | None:
            if entity != "protheus_table" and "/tables/search" not in str(path or "").lower():
                return None

            results = root.get("results")

            if not isinstance(results, list):
                return None

            total = root.get("total_records", len(results))
            linhas = [
                self._host._presenter_text(
                    "systemTablesNarrative",
                    "tablesFound",
                    total=str(total),
                )
            ]

            for item in results[:12]:
                if not isinstance(item, dict):
                    continue

                table_code = (
                    item.get("X2_ARQUIVO")
                    or item.get("table_name")
                    or item.get("name")
                )
                label = item.get("X2_NOME") or item.get("description") or item.get("title")
                score = item.get("total_score") or item.get("score")

                if table_code and label:
                    line = self._host._presenter_text(
                        "systemTablesNarrative",
                        "tableLineBoth",
                        table_code=str(table_code),
                        label=str(label),
                    )
                elif table_code:
                    line = self._host._presenter_text(
                        "systemTablesNarrative",
                        "tableLineCode",
                        table_code=str(table_code),
                    )
                elif label:
                    line = self._host._presenter_text(
                        "systemTablesNarrative",
                        "tableLineLabel",
                        label=str(label),
                    )
                else:
                    continue

                if score is not None:
                    try:
                        line += self._host._presenter_text(
                            "systemTablesNarrative",
                            "relevanceSuffix",
                            score=f"{float(score):.0f}",
                        )
                    except (TypeError, ValueError):
                        pass

                linhas.append(line)

            if len(results) > 12:
                linhas.append(
                    self._host._presenter_text(
                        "pagination", "moreTables", count=str(len(results) - 12)
                    )
                )

            if len(linhas) <= 1:
                linhas.append(
                    self._host._route_presentation("systemTables", "noMatch")
                )

            return {
                "titulo": self._host._route_presentation("systemTables", "searchTitle"),
                "linhas": linhas,
                "dados": root,
            }

    def _present_system_table_columns(
            self,
            root: dict,
            path: str,
            *,
            entity: str | None = None,
        ) -> dict | None:
            if entity != "protheus_column" and "/columns" not in str(path or "").lower():
                return None

            results = root.get("results")

            if not isinstance(results, list) or not results:
                return None

            table_name = str(path or "").rstrip("/").split("/")[-2]
            total = root.get("total", len(results))
            linhas = [
                self._host._presenter_text(
                    "systemTablesNarrative",
                    "columnsTotal",
                    total=str(total),
                )
            ]

            for item in results:
                if not isinstance(item, dict):
                    continue

                field = item.get("X3_CAMPO") or item.get("column_name") or item.get("field")
                label = item.get("X3_DESCRIC") or item.get("column_description") or item.get("label")

                if field and label:
                    linhas.append(
                        self._host._presenter_text(
                            "systemTablesNarrative",
                            "columnLineBoth",
                            field=str(field),
                            label=str(label),
                        )
                    )
                elif field:
                    linhas.append(
                        self._host._presenter_text(
                            "systemTablesNarrative",
                            "columnLineField",
                            field=str(field),
                        )
                    )

            if len(results) > 8:
                linhas.append(
                    self._host._presenter_text(
                        "systemTablesNarrative",
                        "moreColumns",
                        count=str(len(results) - 8),
                    )
                )

            return {
                "titulo": self._host._route_presentation(
                    "systemTables",
                    "columnsTitle",
                    table=table_name.upper(),
                ),
                "linhas": linhas,
                "dados": root,
            }

    def _build_system_columns_table(
            self,
            root: dict,
            path: str,
            *,
            entity: str | None = None,
        ) -> dict | None:
            if entity != "protheus_column" and "/columns" not in str(path or "").lower():
                return None

            results = root.get("results")

            if not isinstance(results, list) or not results:
                return None

            table_name = str(path or "").rstrip("/").split("/")[-2]
            rows = []

            for item in results:
                if not isinstance(item, dict):
                    continue

                rows.append(
                    {
                        "campo": item.get("X3_CAMPO") or item.get("column_name") or item.get("field"),
                        "descricao": item.get("X3_DESCRIC") or item.get("column_description") or item.get("label"),
                        "tipo": item.get("X3_TIPO") or item.get("type"),
                        "tamanho": item.get("X3_TAMANHO") or item.get("size"),
                    }
                )

            if not rows:
                return None

            return {
                "type": "table",
                "title": self._host._route_presentation(
                    "systemTables",
                    "columnsTitle",
                    table=table_name.upper(),
                ),
                "columns": self._host._fixed_columns("systemSx2Columns"),
                "rows": rows,
            }
