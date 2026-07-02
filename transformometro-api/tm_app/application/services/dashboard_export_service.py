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
    ("filial_id", "Unidade"),
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
    def __init__(self) -> None:
        self._live = DashboardLiveService()

    def _fetch_rows(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._live.query_export_rows(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )

    def _fetch_summary_row(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> dict[str, Any]:
        summary = self._live.build_summary(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        liquida = float(summary.get("economia_liquida_total") or 0)
        investimento = float(summary.get("investimento_total") or 0)
        roi = (liquida / investimento * 100) if investimento > 0 else 0.0

        return {
            "codigo_processo": "TOTAIS DO RECORTE",
            "competencia": f"ROI acumulado {round(roi, 1)}%",
            "economia_bruta": summary.get("economia_bruta_total"),
            "economia_liquida_mes": summary.get("economia_liquida_total"),
            "investimento_unico_mes": summary.get("investimento_unico_total"),
            "custo_recorrente_mes": summary.get("custo_recorrente_total"),
            "custo_recursos_compartilhados_mes": summary.get(
                "custo_recursos_compartilhados_total"
            ),
            "investimento_total_mes": summary.get("investimento_total"),
        }

    def build_csv(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> str:
        rows = self._fetch_rows(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        summary = self._fetch_summary_row(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )

        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow([label for _, label in EXPORT_COLUMNS])
        for row in rows:
            writer.writerow([row.get(key) for key, _ in EXPORT_COLUMNS])
        writer.writerow([])
        writer.writerow([summary.get(key, "") for key, _ in EXPORT_COLUMNS])
        return buffer.getvalue()

    def build_excel_html(
        self,
        *,
        view: str | None = None,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> str:
        """Planilha HTML compatível com Excel (sem dependência openpyxl)."""
        rows = self._fetch_rows(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        summary = self._fetch_summary_row(
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
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

        summary_cells = "".join(
            f"<td><strong>{html.escape(str(summary.get(key, '')))}</strong></td>"
            for key, _ in EXPORT_COLUMNS
        )

        return f"""<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office"
      xmlns:x="urn:schemas-microsoft-com:office:excel">
<head><meta charset="UTF-8"/>
<style>
  table {{ border-collapse: collapse; font-family: Calibri, Arial, sans-serif; font-size: 11pt; }}
  th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; }}
  th {{ background: #1e3a5f; color: #fff; font-weight: 600; }}
  tr:nth-child(even) td {{ background: #f8fafc; }}
  tr.tm-summary td {{ background: #e8f4fc; }}
</style>
</head>
<body>
<table>
  <thead><tr>{header_cells}</tr></thead>
  <tbody>
    {"".join(body_rows)}
    <tr class="tm-summary">{summary_cells}</tr>
  </tbody>
</table>
</body>
</html>"""
