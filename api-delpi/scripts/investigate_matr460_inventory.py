#!/usr/bin/env python3
"""
Investigação TOTVS — MATR460 / Registro de Inventário vs. SB9/SB2/SD3/SC2.

Uso:
  docker exec -w /app delpi-api-delpi env PYTHONPATH=/app \\
    python scripts/investigate_matr460_inventory.py

Saída:
  docs/roadmaps/evidencias/matr460-investigacao-totvs.json
  docs/roadmaps/evidencias/matr460-investigacao-totvs.md
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.infrastructure.persistence.totvs.base_repository import BaseRepository

_SCRIPT_DIR = Path(__file__).resolve().parent
_SQL_PATH = _SCRIPT_DIR / "sql" / "investigate_matr460_inventory.sql"
_EVIDENCE_DIR = _SCRIPT_DIR.parent / "docs" / "roadmaps" / "evidencias"

RESULTSET_NAMES = (
    "sb9_closure_dates_2026",
    "sb9_value_by_date",
    "sb9_vs_sb2_vs_ref",
    "sb9_by_local_feb28",
    "sb2_by_local_current",
    "sd3_bridge_period_summary",
    "sc2_open_orders_wip_proxy",
    "inventory_related_objects",
)

MATR460_REFERENCE = {
    "01": {"em_estoque": 3_598_312.40, "em_processo": 263_790.57, "total_geral": 3_862_102.97},
    "02": {"em_estoque": 9_737_043.62, "em_processo": 311_465.89, "total_geral": 10_048_509.51},
}


def _fmt_money(value: float | None) -> str:
    if value is None:
        return "—"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(part: float | None, whole: float | None) -> float | None:
    if part is None or whole is None or whole == 0:
        return None
    return round(100.0 * part / whole, 2)


def _run_sql() -> list[list[dict]]:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    with BaseRepository() as repo:
        return repo.execute_query_multiple(sql, ())


def _analyze(
    named_sets: dict[str, list[dict]],
) -> dict:
    findings: list[str] = []
    sb9_dates = named_sets.get("sb9_closure_dates_2026", [])
    compare = named_sets.get("sb9_vs_sb2_vs_ref", [])
    wip = {str(r["branch"]): r for r in named_sets.get("sc2_open_orders_wip_proxy", [])}

    dates_on_end = [
        r for r in sb9_dates
        if str(r.get("closure_date") or "").strip() == "20260531"
    ]
    if not dates_on_end:
        findings.append(
            "SB9010 **não possui** fechamento em `20260531` — MATR460 EM ESTOQUE de maio/2026 "
            "não está refletido como SB9 nessa data."
        )

    max_dates_2026 = {}
    for row in sb9_dates:
        branch = str(row.get("branch") or "")
        dt = str(row.get("closure_date") or "")
        if branch and (branch not in max_dates_2026 or dt > max_dates_2026[branch]):
            max_dates_2026[branch] = dt

    for branch, max_dt in sorted(max_dates_2026.items()):
        if max_dt < "20260531":
            findings.append(
                f"Filial {branch}: último fechamento SB9 em 2026 é **{max_dt}** "
                f"(anterior a maio/2026)."
            )

    alignment: list[dict] = []
    for row in compare:
        branch = str(row.get("branch") or "")
        ref = MATR460_REFERENCE.get(branch, {})
        sb2 = float(row.get("sb2_current_value") or 0)
        sb9_feb = float(row.get("sb9_feb28_value") or 0)
        sb9_end_raw = row.get("sb9_on_end_date_value")
        sb9_end = float(sb9_end_raw) if sb9_end_raw not in (None, "") else None
        em_estoque = ref.get("em_estoque")
        em_processo = ref.get("em_processo")
        total_geral = ref.get("total_geral")
        wip_row = wip.get(branch, {})
        wip_proxy = float(wip_row.get("open_value_proxy") or 0)

        alignment.append({
            "branch": branch,
            "matr460_em_estoque": em_estoque,
            "matr460_em_processo": em_processo,
            "matr460_total_geral": total_geral,
            "sb9_feb28": sb9_feb,
            "sb9_on_end_date": sb9_end,
            "sb2_current": sb2,
            "sc2_wip_proxy": wip_proxy,
            "sb2_vs_em_estoque_pct": _pct(sb2, em_estoque),
            "sb9_feb_vs_em_estoque_pct": _pct(sb9_feb, em_estoque),
            "sb2_plus_wip_vs_total_pct": _pct(sb2 + wip_proxy, total_geral),
            "wip_proxy_vs_em_processo_pct": _pct(wip_proxy, em_processo),
        })

        if em_estoque and abs(sb2 - em_estoque) / em_estoque < 0.05:
            findings.append(
                f"Filial {branch}: **SB2 atual** ({_fmt_money(sb2)}) ≈ MATR460 EM ESTOQUE "
                f"({_fmt_money(em_estoque)}) — saldo corrente é boa referência quando SB9 de maio ausente."
            )
        if em_processo and wip_proxy > 0:
            ratio = _pct(wip_proxy, em_processo)
            if ratio and 50 <= ratio <= 200:
                findings.append(
                    f"Filial {branch}: proxy SC2 WIP ({_fmt_money(wip_proxy)}) na ordem de "
                    f"EM PROCESSO MATR460 ({_fmt_money(em_processo)}) — candidato W3, validar regra de custo."
                )
            elif ratio and ratio < 50:
                findings.append(
                    f"Filial {branch}: proxy SC2 WIP ({_fmt_money(wip_proxy)}) **subestima** "
                    f"EM PROCESSO ({_fmt_money(em_processo)}) — MATR460 usa outra fonte além de SC2 simples."
                )

    objects = named_sets.get("inventory_related_objects", [])
    custom_views = [
        o for o in objects
        if str(o.get("object_type") or "").startswith("VIEW")
        and "SB9" not in str(o.get("object_name") or "").upper()
    ]
    if custom_views:
        findings.append(
            f"Encontradas {len(custom_views)} view(s) customizadas relacionadas a inventário — "
            "revisar com DBA/Protheus antes de W3."
        )
    else:
        findings.append(
            "Nenhuma view SQL customizada óbvia para MATR460 — relatório provavelmente lê SB9010 "
            "+ módulo produção (EM PROCESSO) via AdvPL, não view publicada."
        )

    return {"alignment": alignment, "findings": findings, "max_sb9_date_2026_by_branch": max_dates_2026}


def _write_md(payload: dict, path: Path) -> None:
    lines = [
        "# Investigação TOTVS — MATR460 vs. fontes SQL",
        "",
        f"**Gerado em:** {payload['generated_at']}",
        "",
        "Referência MATR460 (prints maio/2026): EM ESTOQUE + EM PROCESSO + TOTAL GERAL.",
        "",
        "## Alinhamento por filial",
        "",
        "| Filial | MATR EM ESTOQUE | SB9 28/02 | SB9 31/05 | SB2 atual | SC2 WIP proxy | SB2 vs EM EST. |",
        "|--------|-----------------|-----------|-----------|-----------|---------------|----------------|",
    ]
    for row in payload["analysis"]["alignment"]:
        lines.append(
            f"| {row['branch']} | {_fmt_money(row.get('matr460_em_estoque'))} | "
            f"{_fmt_money(row.get('sb9_feb28'))} | "
            f"{_fmt_money(row.get('sb9_on_end_date'))} | "
            f"{_fmt_money(row.get('sb2_current'))} | "
            f"{_fmt_money(row.get('sc2_wip_proxy'))} | "
            f"{row.get('sb2_vs_em_estoque_pct') or '—'}% |"
        )

    lines.extend(["", "## Achados", ""])
    for item in payload["analysis"]["findings"]:
        lines.append(f"- {item}")

    sb9_dates = payload["raw"]["sb9_closure_dates_2026"]
    if sb9_dates:
        lines.extend(["", "## Datas SB9 em 2026", "", "| Filial | Data | Valor | Registros |", "|--------|------|-------|-----------|"])
        for row in sb9_dates[:20]:
            lines.append(
                f"| {row.get('branch')} | {row.get('closure_date')} | "
                f"{_fmt_money(float(row.get('closure_value') or 0))} | {row.get('record_count')} |"
            )

    objs = payload["raw"].get("inventory_related_objects", [])
    if objs:
        lines.extend(["", "## Objetos SQL (amostra)", "", "| Tipo | Schema | Nome |", "|------|--------|------|"])
        for row in objs[:25]:
            lines.append(
                f"| {row.get('object_type')} | {row.get('schema_name')} | {row.get('object_name')} |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not _SQL_PATH.is_file():
        print(f"SQL não encontrado: {_SQL_PATH}", file=__import__("sys").stderr)
        return 1

    _EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    resultsets = _run_sql()
    named_sets = {
        name: (
            (resultsets[i].get("data") or [])
            if i < len(resultsets)
            else []
        )
        for i, name in enumerate(RESULTSET_NAMES)
    }
    analysis = _analyze(named_sets)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "reference": MATR460_REFERENCE,
        "analysis": analysis,
        "raw": named_sets,
    }

    json_path = _EVIDENCE_DIR / "matr460-investigacao-totvs.json"
    md_path = _EVIDENCE_DIR / "matr460-investigacao-totvs.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    _write_md(payload, md_path)

    print(f"Evidências: {json_path}")
    print(f"           {md_path}")
    for line in analysis["findings"]:
        print(f"  • {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
