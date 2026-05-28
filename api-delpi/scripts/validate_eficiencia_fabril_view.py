#!/usr/bin/env python3
"""
Validação Fase 0 — view dbo.vw_Apontamentos_Eficiencia (TOTVS).

Executa queries de referência e imprime relatório JSON no stdout.

Uso (container api-delpi com VPN/rede TOTVS):
  docker exec delpi-api-delpi python scripts/validate_eficiencia_fabril_view.py

Uso (host, com venv e TOTVS_DB_* ou DB_* no ambiente):
  cd api-delpi && python scripts/validate_eficiencia_fabril_view.py

Opções:
  --markdown PATH   grava relatório em Markdown (ex.: docs/.../FASE0-VALIDACAO.md)
  --json PATH       grava relatório JSON
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.infrastructure.persistence.totvs.base_repository import BaseRepository  # noqa: E402


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


class _ValidationRepository(BaseRepository):
    def run(self, query: str, params: tuple = ()) -> list[dict]:
        with self:
            return self.execute_query(query, params)


def _query(repo: _ValidationRepository, name: str, sql: str, params: tuple = ()) -> dict:
    try:
        rows = repo.run(sql, params)
        return {"name": name, "ok": True, "row_count": len(rows), "rows": rows}
    except Exception as exc:
        return {"name": name, "ok": False, "error": str(exc), "rows": []}


def build_report() -> dict:
    repo = _ValidationRepository()
    checks: list[dict] = []

    checks.append(
        _query(
            repo,
            "sample_top_100",
            """
            SELECT TOP 100
                FILIAL, OP, DATA_PRODUCAO, CENTRO_TRABALHO, NOME_OPERADOR,
                TEMPO_REAL_HORAS, TEMPO_PREVISTO_HORAS, EFICIENCIA_PERCENTUAL,
                RESULTADO_MOD, STATUS_REGISTRO
            FROM dbo.vw_Apontamentos_Eficiencia
            ORDER BY DATA_PRODUCAO DESC, HORA_INICIO DESC, HORA_FINAL DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "status_registro",
            """
            SELECT STATUS_REGISTRO, COUNT(*) AS total
            FROM dbo.vw_Apontamentos_Eficiencia
            GROUP BY STATUS_REGISTRO
            ORDER BY total DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "status_mod",
            """
            SELECT STATUS_MOD, COUNT(*) AS total
            FROM dbo.vw_Apontamentos_Eficiencia
            GROUP BY STATUS_MOD
            ORDER BY total DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "status_resultado_mod",
            """
            SELECT STATUS_RESULTADO_MOD, COUNT(*) AS total
            FROM dbo.vw_Apontamentos_Eficiencia
            GROUP BY STATUS_RESULTADO_MOD
            ORDER BY total DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "branches",
            """
            SELECT FILIAL, COUNT(*) AS total,
                   MIN(DATA_PRODUCAO) AS data_min,
                   MAX(DATA_PRODUCAO) AS data_max
            FROM dbo.vw_Apontamentos_Eficiencia
            GROUP BY FILIAL
            ORDER BY FILIAL
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "volume_last_30_days",
            """
            SELECT DATA_PRODUCAO, COUNT(*) AS linhas_dia
            FROM dbo.vw_Apontamentos_Eficiencia
            WHERE DATA_PRODUCAO >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
            GROUP BY DATA_PRODUCAO
            ORDER BY DATA_PRODUCAO DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "volume_last_12_months",
            """
            SELECT YEAR(DATA_PRODUCAO) AS ano, MONTH(DATA_PRODUCAO) AS mes,
                   COUNT(*) AS linhas_mes
            FROM dbo.vw_Apontamentos_Eficiencia
            WHERE DATA_PRODUCAO >= DATEADD(MONTH, -12, CAST(GETDATE() AS DATE))
            GROUP BY YEAR(DATA_PRODUCAO), MONTH(DATA_PRODUCAO)
            ORDER BY ano DESC, mes DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "kpi_reference_7d_ok",
            """
            SELECT
                COUNT(*) AS appointment_count,
                SUM(CASE WHEN STATUS_REGISTRO <> 'OK' THEN 1 ELSE 0 END) AS invalid_record_count,
                CASE
                    WHEN SUM(TEMPO_REAL_HORAS) > 0
                    THEN ROUND(SUM(TEMPO_PREVISTO_HORAS) / SUM(TEMPO_REAL_HORAS) * 100.0, 2)
                    ELSE NULL
                END AS weighted_efficiency_pct,
                ROUND(SUM(RESULTADO_MOD), 2) AS total_mod_result
            FROM dbo.vw_Apontamentos_Eficiencia
            WHERE DATA_PRODUCAO >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
              AND STATUS_REGISTRO = 'OK'
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "sanity_ct00_absent",
            """
            SELECT COUNT(*) AS ct00_count
            FROM dbo.vw_Apontamentos_Eficiencia
            WHERE CENTRO_TRABALHO = 'CT-00'
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "sanity_zero_real_time",
            """
            SELECT STATUS_REGISTRO, COUNT(*) AS total
            FROM dbo.vw_Apontamentos_Eficiencia
            WHERE TEMPO_REAL_HORAS = 0 OR TEMPO_REAL_HORAS IS NULL
            GROUP BY STATUS_REGISTRO
            ORDER BY total DESC
            """,
        )
    )

    ok_count = sum(1 for c in checks if c["ok"])
    sample = next((c for c in checks if c["name"] == "sample_top_100"), None)
    has_data = bool(sample and sample.get("row_count", 0) > 0)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "view": "dbo.vw_Apontamentos_Eficiencia",
        "phase": "0",
        "checks_passed": ok_count,
        "checks_total": len(checks),
        "has_sample_data": has_data,
        "ready_for_phase_1": ok_count == len(checks) and has_data,
        "checks": checks,
    }


def _format_table(rows: list[dict], max_rows: int = 20) -> str:
    if not rows:
        return "_Sem linhas._\n"
    keys = list(rows[0].keys())
    lines = [
        "| " + " | ".join(keys) + " |",
        "| " + " | ".join("---" for _ in keys) + " |",
    ]
    for row in rows[:max_rows]:
        lines.append("| " + " | ".join(str(row.get(k, "")) for k in keys) + " |")
    if len(rows) > max_rows:
        lines.append(f"\n_… mais {len(rows) - max_rows} linha(s)._")
    return "\n".join(lines) + "\n"


def report_to_markdown(report: dict) -> str:
    status = "✅ Pronto para Fase 1" if report["ready_for_phase_1"] else "⚠️ Pendências"
    lines = [
        "# Fase 0 — Validação TOTVS (Eficiência Fabril)",
        "",
        f"> Gerado em: `{report['generated_at']}`",
        f"> View: `{report['view']}`",
        f"> Status: **{status}**",
        "",
        f"Checks: {report['checks_passed']}/{report['checks_total']} OK | "
        f"Amostra com dados: {'sim' if report['has_sample_data'] else 'não'}",
        "",
        "## Resultados por check",
        "",
    ]

    titles = {
        "sample_top_100": "Amostra TOP 100",
        "status_registro": "Literais STATUS_REGISTRO",
        "status_mod": "Literais STATUS_MOD",
        "status_resultado_mod": "Literais STATUS_RESULTADO_MOD",
        "branches": "Filiais",
        "volume_last_30_days": "Volume — últimos 30 dias",
        "volume_last_12_months": "Volume — últimos 12 meses",
        "kpi_reference_7d_ok": "KPI referência (7 dias, STATUS_REGISTRO = OK)",
        "sanity_ct00_absent": "Sanidade — CT-00 ausente",
        "sanity_zero_real_time": "Sanidade — tempo real zero",
    }

    for check in report["checks"]:
        title = titles.get(check["name"], check["name"])
        lines.append(f"### {title}")
        lines.append("")
        if not check["ok"]:
            lines.append(f"**Erro:** `{check.get('error', 'desconhecido')}`")
            lines.append("")
            continue
        lines.append(f"Linhas: **{check.get('row_count', 0)}**")
        lines.append("")
        lines.append(_format_table(check.get("rows") or []))

    lines.extend(
        [
            "## Como regenerar",
            "",
            "```bash",
            "docker exec delpi-api-delpi python scripts/validate_eficiencia_fabril_view.py \\",
            "  --markdown docs/12-roadmap-e-evolucao/eficiencia-fabril/FASE0-VALIDACAO.md",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validação Fase 0 — vw_Apontamentos_Eficiencia")
    parser.add_argument("--markdown", type=Path, help="Caminho para gravar relatório Markdown")
    parser.add_argument("--json", type=Path, help="Caminho para gravar relatório JSON")
    args = parser.parse_args()

    try:
        report = build_report()
    except Exception as exc:
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "view": "dbo.vw_Apontamentos_Eficiencia",
            "phase": "0",
            "ready_for_phase_1": False,
            "error": str(exc),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2, default=_json_default))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )

    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(report_to_markdown(report), encoding="utf-8")

    return 0 if report["ready_for_phase_1"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
