#!/usr/bin/env python3
"""
Validação Fase 0 — views dbo.vw_minha_delpi_inspecoes_entrada_* (TOTVS).

Executa contagem e amostra (TOP 10) por filial nas views de inspeções de entrada.

Uso (container api-delpi com rede TOTVS):
  docker exec delpi-api-delpi python scripts/validate_inspecoes_entrada_views.py

Uso (host, com venv e TOTVS_DB_* ou DB_* no ambiente):
  cd api-delpi && python scripts/validate_inspecoes_entrada_views.py

Opções:
  --json PATH   grava relatório JSON
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

VIEWS: tuple[str, ...] = (
    "dbo.vw_minha_delpi_inspecoes_entrada_resumo_filial",
    "dbo.vw_minha_delpi_inspecoes_entrada_pendentes",
    "dbo.vw_minha_delpi_inspecoes_entrada_pendentes_fornecedor",
    "dbo.vw_minha_delpi_inspecoes_entrada_rejeitadas_ensaiador",
    "dbo.vw_minha_delpi_inspecoes_entrada_historico_tela",
)

BRANCHES: tuple[str, ...] = ("01", "02")
BRANCH_COLUMN = "Filial"


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

    def run_one(self, query: str, params: tuple = ()) -> dict | None:
        with self:
            return self.execute_one(query, params)


def _short_view_name(view: str) -> str:
    prefix = "dbo.vw_minha_delpi_inspecoes_entrada_"
    if view.startswith(prefix):
        return view[len(prefix) :]
    return view


def _validate_view_branch(
    repo: _ValidationRepository,
    view: str,
    branch: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "view": view,
        "view_short": _short_view_name(view),
        "branch": branch,
        "ok": False,
        "total": None,
        "columns": [],
        "sample_count": 0,
        "sample": [],
        "error": None,
    }

    try:
        count_row = repo.run_one(
            f"SELECT COUNT(*) AS total FROM {view} WHERE {BRANCH_COLUMN} = ?",
            (branch,),
        )
        total = int((count_row or {}).get("total") or 0)
        result["total"] = total

        sample = repo.run(
            f"SELECT TOP 10 * FROM {view} WHERE {BRANCH_COLUMN} = ?",
            (branch,),
        )
        result["sample"] = sample
        result["sample_count"] = len(sample)
        if sample:
            result["columns"] = list(sample[0].keys())
        result["ok"] = True
    except Exception as exc:
        result["error"] = str(exc)

    return result


def build_report() -> dict[str, Any]:
    repo = _ValidationRepository()
    results: list[dict[str, Any]] = []

    for view in VIEWS:
        for branch in BRANCHES:
            results.append(_validate_view_branch(repo, view, branch))

    ok_count = sum(1 for item in results if item["ok"])
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "0",
        "views": list(VIEWS),
        "branches": list(BRANCHES),
        "branch_column": BRANCH_COLUMN,
        "checks_passed": ok_count,
        "checks_total": len(results),
        "all_ok": ok_count == len(results),
        "results": results,
    }


def _format_sample_table(rows: list[dict], max_rows: int = 10) -> str:
    if not rows:
        return "  (sem registros na amostra)\n"
    keys = list(rows[0].keys())
    lines = [
        "  | " + " | ".join(keys) + " |",
        "  | " + " | ".join("---" for _ in keys) + " |",
    ]
    for row in rows[:max_rows]:
        lines.append("  | " + " | ".join(str(row.get(k, "")) for k in keys) + " |")
    return "\n".join(lines) + "\n"


def _print_detail_results(results: list[dict[str, Any]]) -> None:
    current_view: str | None = None
    for item in results:
        if item["view"] != current_view:
            current_view = item["view"]
            print(f"\n=== {current_view} ===")

        branch = item["branch"]
        if not item["ok"]:
            print(f"\n--- Filial {branch} — ERRO ---")
            print(f"  {item['error']}")
            continue

        print(f"\n--- Filial {branch} — OK (total: {item['total']}) ---")
        columns = item.get("columns") or []
        print(f"Colunas ({len(columns)}): {', '.join(columns) if columns else '(nenhuma)'}")
        print("Amostra (TOP 10):")
        print(_format_sample_table(item.get("sample") or []))


def _print_summary_table(results: list[dict[str, Any]]) -> None:
    headers = ("View", "Filial", "Status", "Total", "Colunas", "Erro")
    rows: list[tuple[str, ...]] = []

    for item in results:
        status = "OK" if item["ok"] else "FAIL"
        total = str(item["total"]) if item["total"] is not None else "-"
        columns = str(len(item.get("columns") or [])) if item["ok"] else "-"
        error = (item.get("error") or "-").replace("\n", " ")
        if len(error) > 80:
            error = error[:77] + "..."
        rows.append(
            (
                item["view_short"],
                item["branch"],
                status,
                total,
                columns,
                error if not item["ok"] else "-",
            )
        )

    widths = [len(h) for h in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def _fmt_row(cells: tuple[str, ...]) -> str:
        return " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells))

    separator = "-+-".join("-" * width for width in widths)
    print("\n=== Resumo geral ===")
    print(_fmt_row(headers))
    print(separator)
    for row in rows:
        print(_fmt_row(row))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validação Fase 0 — views inspeções de entrada (TOTVS)",
    )
    parser.add_argument("--json", type=Path, help="Caminho para gravar relatório JSON")
    args = parser.parse_args()

    try:
        report = build_report()
    except Exception as exc:
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "phase": "0",
            "all_ok": False,
            "error": str(exc),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
        return 1

    _print_detail_results(report["results"])
    _print_summary_table(report["results"])

    print(
        f"\nChecks: {report['checks_passed']}/{report['checks_total']} OK | "
        f"Gerado em: {report['generated_at']}"
    )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )
        print(f"Relatório JSON gravado em: {args.json}")

    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
