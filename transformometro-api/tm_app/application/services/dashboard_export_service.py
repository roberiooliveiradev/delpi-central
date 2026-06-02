from __future__ import annotations

import csv
import html
import io
from typing import Any

from tm_app.application.services.dashboard_live_service import DashboardLiveService

EXPORT_COLUMNS: tuple[tuple[str, str], ...] = (
    ("codigo_processo", "Código processo"),
    ("nome_processo", "Nome processo"),
    ("familia_processo", "Família"),
    ("agrupador_ferramenta", "Agrupador ferramenta"),
    ("filial_id", "Filial"),
    ("setor_id", "Setor"),
    ("competencia", "Competência"),
    ("cenario_tipo", "Cenário"),
    ("economia_bruta", "Economia bruta"),
    ("economia_liquida_mes", "Economia líquida mês"),
    ("investimento_unico_mes", "Investimento único mês"),
    ("custo_recorrente_mes", "Custo recorrente mês"),
    ("custo_recursos_compartilhados_mes", "Custo recursos compartilhados mês"),
    ("investimento_total_mes", "Investimento total mês"),
    ("horas_economizadas_mes", "Horas economizadas mês"),
)


class DashboardExportService:
    def _fetch_rows(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        return DashboardLiveService().query_export_rows(
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )

    def build_csv(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> str:
        rows = self._fetch_rows(
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )

        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow([key for key, _ in EXPORT_COLUMNS])
        for row in rows:
            writer.writerow([row.get(key) for key, _ in EXPORT_COLUMNS])
        return buffer.getvalue()

    def build_excel_html(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> str:
        """Planilha HTML compatível com Excel (sem dependência openpyxl)."""
        rows = self._fetch_rows(
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )

        header_cells = "".join(
            f"<th>{html.escape(label)}</th>" for _, label in EXPORT_COLUMNS
        )
        body_rows: list[str] = []
        for row in rows:
            cells = "".join(
                f"<td>{html.escape('' if row.get(key) is None else str(row.get(key)))}</td>"
                for key, _ in EXPORT_COLUMNS
            )
            body_rows.append(f"<tr>{cells}</tr>")

        return f"""<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office"
      xmlns:x="urn:schemas-microsoft-com:office:excel">
<head><meta charset="UTF-8"/>
<style>
  table {{ border-collapse: collapse; font-family: Calibri, Arial, sans-serif; font-size: 11pt; }}
  th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; }}
  th {{ background: #1e3a5f; color: #fff; font-weight: 600; }}
  tr:nth-child(even) td {{ background: #f8fafc; }}
</style>
</head>
<body>
<table>
  <thead><tr>{header_cells}</tr></thead>
  <tbody>{"".join(body_rows)}</tbody>
</table>
</body>
</html>"""
