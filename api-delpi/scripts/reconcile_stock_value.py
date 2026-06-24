#!/usr/bin/env python3
"""
W0 — Reconciliação estoque Suprimentos vs. Registro de Inventário.

Executa SQL de diagnóstico (SB9+SD3 estimado, fechamento oficial, SB2) e compara
com GET /supplies/stock-value no mesmo período.

Uso (container delpi-api-delpi com TOTVS):
  docker exec -w /app delpi-api-delpi env PYTHONPATH=/app python scripts/reconcile_stock_value.py
  docker exec -w /app delpi-api-delpi env PYTHONPATH=/app \\
    python scripts/reconcile_stock_value.py --start-date 2026-05-01 --end-date 2026-05-31

Saída:
  docs/roadmaps/evidencias/estoque-reconciliacao-<end_date>.json
  docs/roadmaps/evidencias/estoque-reconciliacao-<end_date>.md

Ver playbook: docs/roadmaps/playbook-correcao-estoque-supplies-inventario.md §7
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.composition.supplies_composer import build_get_stock_value_use_case
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

_SCRIPT_DIR = Path(__file__).resolve().parent
_SQL_PATH = _SCRIPT_DIR / "sql" / "reconcile_stock_value_period.sql"
_EVIDENCE_DIR = _SCRIPT_DIR.parent / "docs" / "roadmaps" / "evidencias"

_DEFAULT_BRANCHES = ("01", "02")

# Referência manual — Registro de Inventário TOTVS (prints maio/2026).
# Atualizar quando houver novo fechamento oficial para conferência.
OFFICIAL_INVENTORY_REFERENCE: dict[str, dict[str, float]] = {
    "01": {
        "em_estoque": 3_598_312.40,
        "em_processo": 263_790.57,
        "total_geral": 3_862_102.97,
        "label": "Matriz",
    },
    "02": {
        "em_estoque": 9_737_043.62,
        "em_processo": 311_465.89,
        "total_geral": 10_048_509.51,
        "label": "UES",
    },
}


def _parse_cli_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Data inválida: {value!r}")


def _to_protheus(d: date) -> str:
    return d.strftime("%Y%m%d")


def _inject_sql_dates(sql: str, start: str, end: str, end_exclusive: str) -> str:
    sql = re.sub(
        r"DECLARE @start_date CHAR\(8\) = '[^']*';",
        f"DECLARE @start_date CHAR(8) = '{start}';",
        sql,
        count=1,
    )
    sql = re.sub(
        r"DECLARE @end_date CHAR\(8\) = '[^']*';",
        f"DECLARE @end_date CHAR(8) = '{end}';",
        sql,
        count=1,
    )
    sql = re.sub(
        r"DECLARE @end_exclusive CHAR\(8\) = '[^']*';",
        f"DECLARE @end_exclusive CHAR(8) = '{end_exclusive}';",
        sql,
        count=1,
    )
    return sql


def _pct(part: float | None, whole: float | None) -> float | None:
    if part is None or whole is None or whole == 0:
        return None
    return round(100.0 * part / whole, 2)


def _fmt_money(value: float | None) -> str:
    if value is None:
        return "—"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _run_sql(start: str, end: str, end_exclusive: str) -> list[dict]:
    raw = _SQL_PATH.read_text(encoding="utf-8")
    sql = _inject_sql_dates(raw, start, end, end_exclusive)
    with BaseRepository() as repo:
        return repo.execute_query_multiple(sql, ())


def _run_api_per_branch(
    start_iso: str,
    end_iso: str,
    branches: tuple[str, ...],
) -> dict[str, float]:
    use_case = build_get_stock_value_use_case()
    out: dict[str, float] = {}
    for branch in branches:
        payload = use_case.execute(
            GetStockValueRequest(
                branch=branch,
                start_date=start_iso,
                end_date=end_iso,
                summary_only=True,
            )
        )
        summary = payload.get("summary") or {}
        out[branch] = float(summary.get("total_stock_value") or 0)
    return out


def _index_by_branch(rows: list[dict], key: str = "branch") -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for row in rows:
        branch = str(row.get(key) or "").strip()
        if branch:
            indexed[branch] = row
    return indexed


def _build_report(
    *,
    start_iso: str,
    end_iso: str,
    start_protheus: str,
    end_protheus: str,
    resultsets: list[dict],
    api_by_branch: dict[str, float],
    branches: tuple[str, ...],
) -> dict:
    rs_names = [
        "estimated_by_branch",
        "official_closure_le_end",
        "official_closure_on_end",
        "sb2_current",
        "recent_sb9_dates",
    ]
    named_sets: dict[str, list[dict]] = {}
    for idx, name in enumerate(rs_names):
        if idx < len(resultsets):
            named_sets[name] = resultsets[idx].get("data") or []

    estimated = _index_by_branch(named_sets.get("estimated_by_branch", []))
    closure_le = _index_by_branch(named_sets.get("official_closure_le_end", []))
    closure_on_end = _index_by_branch(named_sets.get("official_closure_on_end", []))
    sb2 = _index_by_branch(named_sets.get("sb2_current", []))

    branch_reports: list[dict] = []
    for branch in branches:
        ref = OFFICIAL_INVENTORY_REFERENCE.get(branch, {})
        est = estimated.get(branch, {})
        estimated_sql = float(est.get("estimated_total_value") or 0)
        api_val = api_by_branch.get(branch, 0.0)
        closure_le_row = closure_le.get(branch, {})
        closure_on_row = closure_on_end.get(branch, {})
        sb2_row = sb2.get(branch, {})

        official_le = float(closure_le_row.get("official_closure_value") or 0) or None
        official_on = float(closure_on_row.get("official_closure_value") or 0) or None
        sb2_val = float(sb2_row.get("sb2_total_value") or 0) or None

        em_estoque_ref = ref.get("em_estoque")
        total_geral_ref = ref.get("total_geral")

        branch_reports.append(
            {
                "branch": branch,
                "label": ref.get("label", branch),
                "period": {"start": start_iso, "end": end_iso},
                "sql_estimated": {
                    "closing_base_date": est.get("closing_base_date"),
                    "closing_base_value": est.get("closing_base_value"),
                    "bridge_value": est.get("bridge_value"),
                    "period_net_value": est.get("period_net_value"),
                    "total": estimated_sql,
                },
                "api_estimated_total": api_val,
                "api_matches_sql": abs(api_val - estimated_sql) < 0.02,
                "official_sb9_le_end_date": {
                    "closure_date": closure_le_row.get("closure_date"),
                    "value": official_le,
                },
                "official_sb9_on_end_date": {
                    "closure_date": closure_on_row.get("closure_date") or end_protheus,
                    "value": official_on,
                },
                "sb2_current": sb2_val,
                "inventory_reference_print": ref,
                "gaps": {
                    "api_vs_em_estoque_ref_pct": _pct(api_val, em_estoque_ref),
                    "api_vs_total_geral_ref_pct": _pct(api_val, total_geral_ref),
                    "sb9_on_end_vs_em_estoque_ref_pct": _pct(official_on, em_estoque_ref),
                    "sb9_le_end_vs_em_estoque_ref_pct": _pct(official_le, em_estoque_ref),
                },
                "diagnosis": _diagnose_branch(
                    api_val=api_val,
                    estimated_sql=estimated_sql,
                    official_on=official_on,
                    official_le=official_le,
                    em_estoque_ref=em_estoque_ref,
                ),
            }
        )

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": {
            "start": start_iso,
            "end": end_iso,
            "start_protheus": start_protheus,
            "end_protheus": end_protheus,
        },
        "branches": branch_reports,
        "raw_resultsets": {
            name: named_sets.get(name, []) for name in rs_names
        },
        "playbook_next_step": _playbook_recommendation(branch_reports, named_sets),
    }


def _diagnose_branch(
    *,
    api_val: float,
    estimated_sql: float,
    official_on: float | None,
    official_le: float | None,
    em_estoque_ref: float | None,
) -> list[str]:
    notes: list[str] = []
    if abs(api_val - estimated_sql) > 0.02:
        notes.append("API diverge do SQL de reconciliação — investigar cache ou parâmetros.")

    if official_on and em_estoque_ref:
        ratio = official_on / em_estoque_ref
        if 0.98 <= ratio <= 1.02:
            notes.append(
                "Fechamento SB9 na end_date ≈ EM ESTOQUE do Registro — W2 (modo official_closure) é a correção principal."
            )
        elif official_le and abs(official_le - em_estoque_ref) / em_estoque_ref < 0.02:
            notes.append(
                "Fechamento MAX(B9_DATA)<=end_date ≈ EM ESTOQUE — usar closure_le_end na API."
            )
        else:
            notes.append(
                "SB9 na end_date não bate com EM ESTOQUE do print — validar fechamento TOTVS/MATR460 com Controladoria."
            )
    elif not official_on:
        notes.append(
            "Sem fechamento SB9 na data exata end_date — estimativa SB9+SD3 é esperada; validar closing_base_date e ponte SD3."
        )

    if em_estoque_ref and api_val < em_estoque_ref * 0.5:
        notes.append(
            "Estimativa API < 50% do EM ESTOQUE oficial — gap estrutural (ponte/período SD3 ou base SB9 antiga)."
        )

    return notes


def _playbook_recommendation(branch_reports: list[dict], raw: dict) -> str:
    on_end = raw.get("official_closure_on_end") or []
    if not on_end:
        recent = raw.get("recent_sb9_dates") or []
        max_dates = {r.get("branch"): r.get("closure_date") for r in recent if r.get("branch")}
        stale = all(
            (max_dates.get(b.get("branch")) or "") < "20260301"
            for b in branch_reports
        )
        if stale:
            return (
                "SB9010 sem fechamento após fev/2026 — estimativa SD3 não confiável para maio. "
                "Escalar Controladoria (fechamentos SB9 mar–mai) antes de W2; avaliar fallback "
                "SB2 ou MAX(B9_DATA)<=end_date quando inventário oficial existir sem SB9 na data."
            )
    for item in branch_reports:
        for note in item.get("diagnosis") or []:
            if "W2" in note:
                return "Prosseguir W1 (breakdown) + W2 (stock_method=auto com sb9_closure_on_end_date)."
    return "Revisar gaps por filial; considerar W1 transparência enquanto define D1–D4."


def _w0_conclusions(report: dict) -> list[str]:
    lines: list[str] = []
    raw = report.get("raw_resultsets") or {}
    on_end = raw.get("official_closure_on_end") or []
    if not on_end:
        lines.append(
            "**Não há registros SB9010 com `B9_DATA = end_date`** — o Registro de Inventário "
            "não está refletido como fechamento SB9 nessa data no banco consultado."
        )

    for item in report.get("branches") or []:
        est = item.get("sql_estimated") or {}
        ref = item.get("inventory_reference_print") or {}
        sb2 = item.get("sb2_current")
        base_date = est.get("closing_base_date")
        if base_date and str(base_date) < "20260301":
            lines.append(
                f"Filial **{item.get('branch')}**: último fechamento SB9 usado pela API é **{base_date}**; "
                f"ponte SD3 {_fmt_money(float(est.get('bridge_value') or 0))} + período "
                f"{_fmt_money(float(est.get('period_net_value') or 0))} → estimativa "
                f"{_fmt_money(float(est.get('total') or 0))} vs EM ESTOQUE ref. "
                f"{_fmt_money(ref.get('em_estoque'))}."
            )
        if sb2 and ref.get("em_estoque"):
            ratio = sb2 / ref["em_estoque"] if ref["em_estoque"] else 0
            if 0.9 <= ratio <= 1.1:
                lines.append(
                    f"Filial **{item.get('branch')}**: **SB2 atual** ({_fmt_money(sb2)}) está próximo do "
                    "EM ESTOQUE do print — saldo corrente é melhor referência que SB9+SD3 neste cenário."
                )

    all_match = all(b.get("api_matches_sql") for b in report.get("branches") or [])
    if all_match:
        lines.append("**API e SQL de reconciliação coincidem** — o gap é de regra/dados TOTVS, não bug de implementação.")

    return lines


def _render_markdown(report: dict) -> str:
    lines = [
        "# Evidências — reconciliação estoque Suprimentos",
        "",
        f"**Gerado em:** {report.get('generated_at', '')}  ",
        f"**Período:** {report['period']['start']} a {report['period']['end']}",
        "",
        "Referência: [playbook-correcao-estoque-supplies-inventario.md](../playbook-correcao-estoque-supplies-inventario.md)",
        "",
        "## Resumo por filial",
        "",
        "| Filial | API estimada | SQL estimada | SB9 em end_date | SB9 ≤ end_date | SB2 atual | Ref. EM ESTOQUE | Ref. TOTAL GERAL |",
        "|--------|-------------|-------------|-----------------|----------------|-----------|-----------------|------------------|",
    ]

    for item in report.get("branches") or []:
        sql_est = item.get("sql_estimated") or {}
        on_end = item.get("official_sb9_on_end_date") or {}
        le_end = item.get("official_sb9_le_end_date") or {}
        ref = item.get("inventory_reference_print") or {}
        lines.append(
            "| {branch} {label} | {api} | {sql} | {on} | {le} | {sb2} | {em} | {tot} |".format(
                branch=item.get("branch"),
                label=item.get("label", ""),
                api=_fmt_money(item.get("api_estimated_total")),
                sql=_fmt_money(sql_est.get("total")),
                on=_fmt_money(on_end.get("value")),
                le=_fmt_money(le_end.get("value")),
                sb2=_fmt_money(item.get("sb2_current")),
                em=_fmt_money(ref.get("em_estoque")),
                tot=_fmt_money(ref.get("total_geral")),
            )
        )

    lines.extend(["", "## Breakdown SQL (estimativa API)", ""])
    for item in report.get("branches") or []:
        est = item.get("sql_estimated") or {}
        lines.extend(
            [
                f"### Filial {item.get('branch')} — {item.get('label', '')}",
                "",
                f"- Base SB9 (`closing_base_date`): **{est.get('closing_base_date') or '—'}** → {_fmt_money(float(est.get('closing_base_value') or 0))}",
                f"- Ponte SD3: {_fmt_money(float(est.get('bridge_value') or 0))}",
                f"- Período SD3: {_fmt_money(float(est.get('period_net_value') or 0))}",
                f"- **Total estimado:** {_fmt_money(float(est.get('total') or 0))}",
                "",
            ]
        )
        for note in item.get("diagnosis") or []:
            lines.append(f"- {note}")
        lines.append("")

    lines.extend(
        [
            "## Conclusões W0",
            "",
        ]
    )
    for line in _w0_conclusions(report):
        lines.append(f"- {line}")
    lines.append("")

    lines.extend(
        [
            "## Próximo passo (playbook)",
            "",
            report.get("playbook_next_step", ""),
            "",
            "## Checklist W0",
            "",
            "- [ ] Confirmar fechamento SB9 na `end_date` por filial",
            "- [ ] Comparar SB9 end_date com EM ESTOQUE do Registro",
            "- [ ] Comparar API com SQL (deve coincidir)",
            "- [ ] Registrar decisão D1–D4 com Suprimentos",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="W0 reconciliação estoque Suprimentos")
    parser.add_argument("--start-date", default="2026-05-01")
    parser.add_argument("--end-date", default="2026-05-31")
    parser.add_argument("--branches", default=",".join(_DEFAULT_BRANCHES))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_EVIDENCE_DIR,
        help="Diretório para JSON/MD de evidências",
    )
    parser.add_argument("--no-write", action="store_true", help="Só imprimir JSON no stdout")
    args = parser.parse_args()

    start_d = _parse_cli_date(args.start_date)
    end_d = _parse_cli_date(args.end_date)
    if start_d > end_d:
        print("start_date não pode ser maior que end_date.", file=sys.stderr)
        return 1

    start_protheus = _to_protheus(start_d)
    end_protheus = _to_protheus(end_d)
    end_exclusive = _to_protheus(end_d + timedelta(days=1))
    start_iso = start_d.isoformat()
    end_iso = end_d.isoformat()
    branches = tuple(b.strip() for b in args.branches.split(",") if b.strip())

    print(f"Reconciliando estoque {start_iso} .. {end_iso} filiais {branches}...", file=sys.stderr)

    resultsets = _run_sql(start_protheus, end_protheus, end_exclusive)
    api_by_branch = _run_api_per_branch(start_iso, end_iso, branches)

    report = _build_report(
        start_iso=start_iso,
        end_iso=end_iso,
        start_protheus=start_protheus,
        end_protheus=end_protheus,
        resultsets=resultsets,
        api_by_branch=api_by_branch,
        branches=branches,
    )

    if args.no_write:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"estoque-reconciliacao-{end_protheus}"
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nEvidências: {json_path}", file=sys.stderr)
    print(f"            {md_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
