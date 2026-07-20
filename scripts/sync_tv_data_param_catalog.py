#!/usr/bin/env python3
"""Gera labels/hints do MFE TV a partir de openapi_param_locale.json (fonte única).

Uso:
  python3 scripts/sync_tv_data_param_catalog.py --write
  python3 scripts/sync_tv_data_param_catalog.py --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARAM_LOCALE = ROOT / "api-delpi" / "app" / "content" / "openapi_param_locale.json"
MFE_CATALOG = ROOT / "plugins" / "tv-dashboard" / "src" / "content" / "dataParamCatalog.ts"
PRESENTATION_LABELS = (
    ROOT / "plugins" / "tv-dashboard-presentation" / "src" / "formatDataSourceBindingSummary.ts"
)

# Chaves TV-only (não estão no OpenAPI).
TV_ONLY_LABELS = {
    "dateRangePreset": "Período",
}
TV_ONLY_HINTS = {
    "dateRangePreset": "Atalho de período (este mês, últimos 30 dias etc.).",
}

# Subconjunto usado no cartão do palco (presentation).
PRESENTATION_KEYS = (
    "branch",
    "filial",
    "branches",
    "dateRangePreset",
    "periodDays",
    "date_start",
    "date_end",
    "start_date",
    "end_date",
    "date_from",
    "date_to",
    "dataInicio",
    "dataFim",
    "work_center",
    "cost_center",
    "granularity",
    "customer_segment",
    "product_type",
    "loss_type",
    "stock_method",
)


def _load_param_locale() -> tuple[dict[str, str], dict[str, str]]:
    payload = json.loads(PARAM_LOCALE.read_text(encoding="utf-8"))
    labels: dict[str, str] = dict(TV_ONLY_LABELS)
    hints: dict[str, str] = dict(TV_ONLY_HINTS)
    for name, entry in (payload.get("params") or {}).items():
        if not isinstance(entry, dict):
            continue
        locale = entry.get("locale") if isinstance(entry.get("locale"), dict) else {}
        pt = locale.get("pt-BR") if isinstance(locale.get("pt-BR"), dict) else {}
        label = str(pt.get("label") or "").strip()
        description = str(pt.get("description") or "").strip()
        if label:
            labels[str(name)] = label
        if description:
            hints[str(name)] = description
    return dict(sorted(labels.items())), dict(sorted(hints.items()))


def _ts_record(name: str, data: dict[str, str]) -> str:
    lines = [f"export const {name}: Record<string, string> = {{"]
    for key, value in data.items():
        lines.append(f"  {json.dumps(key)}: {json.dumps(value, ensure_ascii=False)},")
    lines.append("};")
    return "\n".join(lines)


def _extract_tail_from_existing(existing: str) -> str:
    """Preserva ENUM_OPTION_LABELS + UI_FALLBACK_ENUMS + helpers."""
    start = existing.find("export const ENUM_OPTION_LABELS")
    if start < 0:
        raise SystemExit("Não encontrou ENUM_OPTION_LABELS em dataParamCatalog.ts")
    return existing[start:].rstrip() + "\n"


def build_mfe_catalog(labels: dict[str, str], hints: dict[str, str]) -> str:
    header = """/**
 * Fonte única de rótulos e enums de fallback para parâmetros de dados no MFE TV Dashboard.
 * Labels/hints gerados de api-delpi/app/content/openapi_param_locale.json —
 * rode: python3 scripts/sync_tv_data_param_catalog.py --write
 * Preferir meta/OpenAPI da API quando disponível; estes mapas cobrem UI estável entre rotas.
 */

"""
    existing = MFE_CATALOG.read_text(encoding="utf-8") if MFE_CATALOG.is_file() else ""
    tail = _extract_tail_from_existing(existing)
    body = "\n\n".join(
        [
            _ts_record("PARAM_FIELD_LABELS", labels),
            _ts_record("PARAM_FIELD_HINTS", hints),
            tail,
        ]
    )
    return header + body


def build_presentation_snippet(labels: dict[str, str]) -> str:
    subset = {k: labels[k] for k in PRESENTATION_KEYS if k in labels}
    lines = [
        "/** Rótulos mínimos para o cartão no palco (gerado de openapi_param_locale / TV-only). */",
        "export const DATA_SOURCE_PARAM_LABELS: Record<string, string> = {",
    ]
    for key, value in subset.items():
        lines.append(f"  {key}: {json.dumps(value, ensure_ascii=False)},")
    lines.append("};")
    return "\n".join(lines)


def patch_presentation(labels: dict[str, str]) -> str:
    text = PRESENTATION_LABELS.read_text(encoding="utf-8")
    snippet = build_presentation_snippet(labels)
    new_text, n = re.subn(
        r"/\*\* Rótulos mínimos para o cartão no palco[\s\S]*?export const DATA_SOURCE_PARAM_LABELS: Record<string, string> = \{[\s\S]*?\n\};",
        snippet,
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit("Não encontrou DATA_SOURCE_PARAM_LABELS em formatDataSourceBindingSummary.ts")
    return new_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    labels, hints = _load_param_locale()
    mfe = build_mfe_catalog(labels, hints)
    presentation = patch_presentation(labels)

    if args.check:
        ok = True
        if MFE_CATALOG.read_text(encoding="utf-8") != mfe:
            print("Drift em dataParamCatalog.ts — rode com --write.", file=sys.stderr)
            ok = False
        if PRESENTATION_LABELS.read_text(encoding="utf-8") != presentation:
            print("Drift em formatDataSourceBindingSummary.ts — rode com --write.", file=sys.stderr)
            ok = False
        if ok:
            print(f"OK — catálogos TV alinhados ({len(labels)} labels).")
            return 0
        return 1

    if not args.write:
        print(f"Dry-run — {len(labels)} labels / {len(hints)} hints. Use --write.")
        return 0

    MFE_CATALOG.write_text(mfe, encoding="utf-8")
    PRESENTATION_LABELS.write_text(presentation, encoding="utf-8")
    print(f"Gravado {MFE_CATALOG} e {PRESENTATION_LABELS} ({len(labels)} labels).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
