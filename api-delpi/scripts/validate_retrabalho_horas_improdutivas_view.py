#!/usr/bin/env python3
"""
Validação Fase 0 — view dbo.VW_BI_RT_HORAS_IMPRODUTIVAS (TOTVS).

Executa queries de referência (somente SELECT) e imprime relatório JSON no stdout.

Uso (container api-delpi com VPN/rede TOTVS):
  docker exec delpi-api-delpi python scripts/validate_retrabalho_horas_improdutivas_view.py

Uso (host, com venv e TOTVS_DB_* ou DB_* no ambiente):
  cd api-delpi && python scripts/validate_retrabalho_horas_improdutivas_view.py

Opções:
  --markdown PATH   grava relatório em Markdown
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

VIEW_SCHEMA = "dbo"
VIEW_NAME = "VW_BI_RT_HORAS_IMPRODUTIVAS"
VIEW_FQN = f"{VIEW_SCHEMA}.{VIEW_NAME}"

REQUIRED_COLUMNS = (
    "FILIAL",
    "DATA_REFERENCIA",
    "ANO_MES",
    "TEMPO_HORAS",
    "VALOR_PARADA_RS",
    "RECURSO",
    "CENTRO_CUSTO",
    "CODIGO_OPERADOR",
    "NOME_OPERADOR",
    "FONTE_CUSTO",
    "RECNO",
)

DATE_FILTER_12M = "DATA_REFERENCIA >= DATEADD(MONTH, -12, CAST(GETDATE() AS DATE))"


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
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


def _check_required_columns(column_rows: list[dict]) -> dict:
    found = {str(row.get("column_name", "")).upper() for row in column_rows}
    missing = [col for col in REQUIRED_COLUMNS if col not in found]
    return {
        "required": list(REQUIRED_COLUMNS),
        "found": sorted(found & set(REQUIRED_COLUMNS)),
        "missing": missing,
        "ok": len(missing) == 0,
    }


def build_report() -> dict:
    repo = _ValidationRepository()
    checks: list[dict] = []

    view_exists = _query(
        repo,
        "view_exists",
        """
        SELECT TOP 1
            LTRIM(RTRIM(TABLE_SCHEMA)) AS table_schema,
            LTRIM(RTRIM(TABLE_NAME)) AS table_name
        FROM INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_SCHEMA = ?
          AND TABLE_NAME = ?
        """,
        (VIEW_SCHEMA, VIEW_NAME),
    )
    checks.append(view_exists)

    columns = _query(
        repo,
        "required_columns",
        """
        SELECT
            LTRIM(RTRIM(COLUMN_NAME)) AS column_name,
            LTRIM(RTRIM(DATA_TYPE)) AS data_type,
            NUMERIC_PRECISION,
            NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ?
          AND TABLE_NAME = ?
          AND COLUMN_NAME IN ({placeholders})
        ORDER BY COLUMN_NAME
        """.format(placeholders=", ".join("?" for _ in REQUIRED_COLUMNS)),
        (VIEW_SCHEMA, VIEW_NAME, *REQUIRED_COLUMNS),
    )
    column_validation = _check_required_columns(columns.get("rows") or [])
    columns["column_validation"] = column_validation
    columns["ok"] = columns["ok"] and column_validation["ok"]
    checks.append(columns)

    checks.append(
        _query(
            repo,
            "summary_by_branch_12m",
            f"""
            SELECT
                LTRIM(RTRIM(FILIAL)) AS filial,
                COUNT(*) AS total_apontamentos,
                CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas,
                CAST(SUM(CAST(VALOR_PARADA_RS AS DECIMAL(18, 2))) AS DECIMAL(18, 2)) AS total_custo,
                SUM(
                    CASE
                        WHEN LTRIM(RTRIM(FONTE_CUSTO)) = 'SEM CUSTO' THEN 1
                        ELSE 0
                    END
                ) AS registros_sem_custo,
                CAST(
                    SUM(
                        CASE
                            WHEN LTRIM(RTRIM(FONTE_CUSTO)) = 'SEM CUSTO'
                            THEN CAST(TEMPO_HORAS AS DECIMAL(18, 4))
                            ELSE CAST(0 AS DECIMAL(18, 4))
                        END
                    ) AS DECIMAL(18, 4)
                ) AS horas_sem_custo
            FROM {VIEW_FQN} WITH (NOLOCK)
            WHERE {DATE_FILTER_12M}
            GROUP BY LTRIM(RTRIM(FILIAL))
            ORDER BY filial
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "monthly_summary_by_branch_12m",
            f"""
            SELECT
                LTRIM(RTRIM(FILIAL)) AS filial,
                LTRIM(RTRIM(ANO_MES)) AS ano_mes,
                COUNT(*) AS total_apontamentos,
                CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas,
                CAST(SUM(CAST(VALOR_PARADA_RS AS DECIMAL(18, 2))) AS DECIMAL(18, 2)) AS total_custo
            FROM {VIEW_FQN} WITH (NOLOCK)
            WHERE {DATE_FILTER_12M}
            GROUP BY LTRIM(RTRIM(FILIAL)), LTRIM(RTRIM(ANO_MES))
            ORDER BY filial, ano_mes DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "top_10_recursos_by_hours",
            f"""
            SELECT TOP 10
                LTRIM(RTRIM(RECURSO)) AS recurso,
                CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas
            FROM {VIEW_FQN} WITH (NOLOCK)
            WHERE {DATE_FILTER_12M}
            GROUP BY LTRIM(RTRIM(RECURSO))
            ORDER BY total_horas DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "top_10_operadores_by_hours",
            f"""
            SELECT TOP 10
                LTRIM(RTRIM(CODIGO_OPERADOR)) AS codigo_operador,
                LTRIM(RTRIM(NOME_OPERADOR)) AS nome_operador,
                CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas
            FROM {VIEW_FQN} WITH (NOLOCK)
            WHERE {DATE_FILTER_12M}
            GROUP BY LTRIM(RTRIM(CODIGO_OPERADOR)), LTRIM(RTRIM(NOME_OPERADOR))
            ORDER BY total_horas DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "sample_recent_10",
            f"""
            SELECT TOP 10
                LTRIM(RTRIM(FILIAL)) AS filial,
                DATA_REFERENCIA,
                LTRIM(RTRIM(ANO_MES)) AS ano_mes,
                CAST(TEMPO_HORAS AS DECIMAL(18, 4)) AS tempo_horas,
                CAST(VALOR_PARADA_RS AS DECIMAL(18, 2)) AS valor_parada_rs,
                LTRIM(RTRIM(RECURSO)) AS recurso,
                LTRIM(RTRIM(CENTRO_CUSTO)) AS centro_custo,
                LTRIM(RTRIM(CODIGO_OPERADOR)) AS codigo_operador,
                LTRIM(RTRIM(NOME_OPERADOR)) AS nome_operador,
                LTRIM(RTRIM(FONTE_CUSTO)) AS fonte_custo,
                RECNO
            FROM {VIEW_FQN} WITH (NOLOCK)
            ORDER BY DATA_REFERENCIA DESC, RECNO DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "alert_invalid_branches",
            f"""
            SELECT
                LTRIM(RTRIM(FILIAL)) AS filial,
                COUNT(*) AS total
            FROM {VIEW_FQN} WITH (NOLOCK)
            WHERE {DATE_FILTER_12M}
              AND LTRIM(RTRIM(FILIAL)) NOT IN ('01', '02')
            GROUP BY LTRIM(RTRIM(FILIAL))
            ORDER BY total DESC
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "alert_sem_custo",
            f"""
            SELECT
                LTRIM(RTRIM(FILIAL)) AS filial,
                COUNT(*) AS total_sem_custo,
                CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS horas_sem_custo
            FROM {VIEW_FQN} WITH (NOLOCK)
            WHERE {DATE_FILTER_12M}
              AND LTRIM(RTRIM(FONTE_CUSTO)) = 'SEM CUSTO'
            GROUP BY LTRIM(RTRIM(FILIAL))
            ORDER BY filial
            """,
        )
    )

    checks.append(
        _query(
            repo,
            "alert_nome_operador_vazio",
            f"""
            SELECT
                LTRIM(RTRIM(FILIAL)) AS filial,
                COUNT(*) AS total_sem_nome_operador
            FROM {VIEW_FQN} WITH (NOLOCK)
            WHERE {DATE_FILTER_12M}
              AND (
                    NOME_OPERADOR IS NULL
                    OR LTRIM(RTRIM(NOME_OPERADOR)) = ''
                  )
            GROUP BY LTRIM(RTRIM(FILIAL))
            ORDER BY filial
            """,
        )
    )

    ok_count = sum(1 for c in checks if c["ok"])
    view_ok = bool(view_exists.get("ok") and view_exists.get("row_count", 0) > 0)
    columns_ok = bool(columns.get("ok"))
    sample = next((c for c in checks if c["name"] == "sample_recent_10"), None)
    has_data = bool(sample and sample.get("row_count", 0) > 0)

    alerts = {
        "invalid_branches": next(
            (c for c in checks if c["name"] == "alert_invalid_branches"), {}
        ).get("rows")
        or [],
        "sem_custo": next((c for c in checks if c["name"] == "alert_sem_custo"), {}).get(
            "rows"
        )
        or [],
        "nome_operador_vazio": next(
            (c for c in checks if c["name"] == "alert_nome_operador_vazio"), {}
        ).get("rows")
        or [],
    }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "view": VIEW_FQN,
        "phase": "0",
        "date_reference_field": "DATA_REFERENCIA",
        "default_window": "last_12_months",
        "checks_passed": ok_count,
        "checks_total": len(checks),
        "view_exists": view_ok,
        "required_columns_ok": columns_ok,
        "has_sample_data": has_data,
        "alerts": alerts,
        "ready_for_phase_1": view_ok and columns_ok and ok_count == len(checks),
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
        "# Fase 0 — Validação TOTVS (Retrabalho / Horas Improdutivas)",
        "",
        f"> Gerado em: `{report['generated_at']}`",
        f"> View: `{report['view']}`",
        f"> Janela padrão: `{report['default_window']}` via `{report['date_reference_field']}`",
        f"> Status: **{status}**",
        "",
        f"Checks: {report['checks_passed']}/{report['checks_total']} OK | "
        f"View existe: {'sim' if report['view_exists'] else 'não'} | "
        f"Colunas OK: {'sim' if report['required_columns_ok'] else 'não'} | "
        f"Amostra com dados: {'sim' if report['has_sample_data'] else 'não'}",
        "",
        "## Alertas",
        "",
        "### Filiais fora de 01/02",
        "",
        _format_table(report["alerts"]["invalid_branches"]),
        "### FONTE_CUSTO = SEM CUSTO",
        "",
        _format_table(report["alerts"]["sem_custo"]),
        "### NOME_OPERADOR nulo ou vazio",
        "",
        _format_table(report["alerts"]["nome_operador_vazio"]),
        "",
        "## Resultados por check",
        "",
    ]

    titles = {
        "view_exists": "View existe",
        "required_columns": "Colunas obrigatórias",
        "summary_by_branch_12m": "Resumo 12 meses por filial",
        "monthly_summary_by_branch_12m": "Resumo mensal 12 meses por filial",
        "top_10_recursos_by_hours": "Top 10 recursos por horas",
        "top_10_operadores_by_hours": "Top 10 operadores por horas",
        "sample_recent_10": "Amostra recente (TOP 10)",
        "alert_invalid_branches": "Alerta — filiais inválidas",
        "alert_sem_custo": "Alerta — SEM CUSTO",
        "alert_nome_operador_vazio": "Alerta — operador sem nome",
    }

    for check in report["checks"]:
        title = titles.get(check["name"], check["name"])
        lines.append(f"### {title}")
        lines.append("")
        if not check["ok"]:
            lines.append(f"**Erro:** `{check.get('error', 'desconhecido')}`")
            lines.append("")
            continue
        if check["name"] == "required_columns" and check.get("column_validation"):
            validation = check["column_validation"]
            lines.append(
                f"Colunas encontradas: **{len(validation['found'])}/{len(validation['required'])}**"
            )
            if validation["missing"]:
                lines.append(f"Faltando: `{', '.join(validation['missing'])}`")
            lines.append("")
        lines.append(f"Linhas: **{check.get('row_count', 0)}**")
        lines.append("")
        lines.append(_format_table(check.get("rows") or []))

    lines.extend(
        [
            "## Como regenerar",
            "",
            "```bash",
            "docker exec delpi-api-delpi python scripts/validate_retrabalho_horas_improdutivas_view.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validação Fase 0 — VW_BI_RT_HORAS_IMPRODUTIVAS"
    )
    parser.add_argument("--markdown", type=Path, help="Caminho para gravar relatório Markdown")
    parser.add_argument("--json", type=Path, help="Caminho para gravar relatório JSON")
    args = parser.parse_args()

    try:
        report = build_report()
    except Exception as exc:
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "view": VIEW_FQN,
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
