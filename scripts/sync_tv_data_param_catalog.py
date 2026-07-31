#!/usr/bin/env python3
"""Gera labels/hints/enums do MFE TV a partir de openapi_param_locale.json (fonte única).

Uso:
  python3 scripts/sync_tv_data_param_catalog.py --write
  python3 scripts/sync_tv_data_param_catalog.py --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARAM_LOCALE = ROOT / "api-delpi" / "app" / "content" / "openapi_param_locale.json"
TV_ROUTES = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_routes.json"
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

# Filiais/códigos de escopo — labels opcionais; BranchField cobre a UX principal.
_IDENTITY_ENUM_PARAMS = frozenset({"branch", "filial", "branch_code", "filial_id"})


def _load_param_locale() -> tuple[dict[str, str], dict[str, str], dict[str, dict[str, str]]]:
    payload = json.loads(PARAM_LOCALE.read_text(encoding="utf-8"))
    labels: dict[str, str] = dict(TV_ONLY_LABELS)
    hints: dict[str, str] = dict(TV_ONLY_HINTS)
    enum_pt: dict[str, dict[str, str]] = {}
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
        raw_enums = entry.get("enumLabels")
        if not isinstance(raw_enums, dict):
            continue
        mapped: dict[str, str] = {}
        for code, langs in raw_enums.items():
            if not isinstance(langs, dict):
                continue
            pt_block = langs.get("pt-BR") if isinstance(langs.get("pt-BR"), dict) else {}
            en_block = langs.get("en") if isinstance(langs.get("en"), dict) else {}
            pt_label = str(pt_block.get("label") or "").strip()
            en_label = str(en_block.get("label") or "").strip()
            if not pt_label or not en_label:
                continue
            mapped[str(code)] = pt_label
        if mapped:
            enum_pt[str(name)] = dict(sorted(mapped.items()))
    return dict(sorted(labels.items())), dict(sorted(hints.items())), dict(sorted(enum_pt.items()))


def _ts_record(name: str, data: dict[str, str]) -> str:
    lines = [f"export const {name}: Record<string, string> = {{"]
    for key, value in data.items():
        lines.append(f"  {json.dumps(key)}: {json.dumps(value, ensure_ascii=False)},")
    lines.append("};")
    return "\n".join(lines)


def _ts_enum_option_labels(enum_pt: dict[str, dict[str, str]]) -> str:
    lines = [
        "/** Rótulos PT-BR das opções de enum — gerados de openapi_param_locale.json enumLabels. */",
        "export const ENUM_OPTION_LABELS: Record<string, Record<string, string>> = {",
    ]
    for param, values in enum_pt.items():
        inner = ", ".join(
            f"{json.dumps(code)}: {json.dumps(label, ensure_ascii=False)}"
            for code, label in values.items()
        )
        lines.append(f"  {param}: {{ {inner} }},")
    lines.append("};")
    return "\n".join(lines)


def _extract_helpers_tail(existing: str) -> str:
    """Preserva UI_FALLBACK_ENUMS + helpers (não ENUM_OPTION_LABELS — esse é gerado)."""
    start = existing.find("/** Enums de UI quando o OpenAPI não declara")
    if start < 0:
        start = existing.find("export const UI_FALLBACK_ENUMS")
    if start < 0:
        raise SystemExit("Não encontrou UI_FALLBACK_ENUMS em dataParamCatalog.ts")
    return existing[start:].rstrip() + "\n"


def build_mfe_catalog(
    labels: dict[str, str],
    hints: dict[str, str],
    enum_pt: dict[str, dict[str, str]],
) -> str:
    header = """/**
 * Fonte única de rótulos e enums de fallback para parâmetros de dados no MFE TV Dashboard.
 * Labels/hints/ENUM_OPTION_LABELS gerados de api-delpi/app/content/openapi_param_locale.json —
 * rode: python3 scripts/sync_tv_data_param_catalog.py --write
 * Preferir meta/OpenAPI da API quando disponível; estes mapas cobrem UI estável entre rotas.
 * enumLabels no JSON são bilíngues (en + pt-BR); o MFE consome pt-BR.
 */

"""
    existing = MFE_CATALOG.read_text(encoding="utf-8") if MFE_CATALOG.is_file() else ""
    tail = _extract_helpers_tail(existing)
    body = "\n\n".join(
        [
            _ts_record("PARAM_FIELD_LABELS", labels),
            _ts_record("PARAM_FIELD_HINTS", hints),
            _ts_enum_option_labels(enum_pt),
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


def _tv_route_enums() -> dict[str, set[str]]:
    payload = json.loads(TV_ROUTES.read_text(encoding="utf-8"))
    routes = payload.get("routes") if isinstance(payload, dict) else payload
    enums: dict[str, set[str]] = defaultdict(set)
    if not isinstance(routes, list):
        return {}
    for route in routes:
        if not isinstance(route, dict):
            continue
        schema = route.get("paramSchema") or {}
        if not isinstance(schema, dict):
            continue
        for key, field in schema.items():
            if not isinstance(field, dict):
                continue
            raw = field.get("enum")
            if not isinstance(raw, list):
                continue
            for item in raw:
                if item is None:
                    continue
                text = str(item).strip()
                if text:
                    enums[str(key)].add(text)
    return enums


def _check_enum_coverage(payload: dict) -> list[str]:
    """Falhas: valor de enum no catálogo TV sem enumLabels bilíngue (en + pt-BR)."""
    params = payload.get("params") if isinstance(payload, dict) else {}
    if not isinstance(params, dict):
        params = {}
    failures: list[str] = []
    for param, values in sorted(_tv_route_enums().items()):
        if param in _IDENTITY_ENUM_PARAMS:
            continue
        entry = params.get(param) if isinstance(params.get(param), dict) else {}
        enum_labels = entry.get("enumLabels") if isinstance(entry.get("enumLabels"), dict) else {}
        for code in sorted(values):
            langs = enum_labels.get(code) if isinstance(enum_labels.get(code), dict) else {}
            en = str(((langs.get("en") or {}) if isinstance(langs.get("en"), dict) else {}).get("label") or "").strip()
            pt = str(
                ((langs.get("pt-BR") or {}) if isinstance(langs.get("pt-BR"), dict) else {}).get("label") or ""
            ).strip()
            if not en or not pt:
                failures.append(f"{param}={code} (en={en!r} pt-BR={pt!r})")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = json.loads(PARAM_LOCALE.read_text(encoding="utf-8"))
    labels, hints, enum_pt = _load_param_locale()
    mfe = build_mfe_catalog(labels, hints, enum_pt)
    presentation = patch_presentation(labels)
    enum_gaps = _check_enum_coverage(payload)

    if args.check:
        ok = True
        if enum_gaps:
            print(
                f"Faltam enumLabels bilíngues ({len(enum_gaps)}) em openapi_param_locale.json:",
                file=sys.stderr,
            )
            for gap in enum_gaps[:40]:
                print(f"  - {gap}", file=sys.stderr)
            if len(enum_gaps) > 40:
                print(f"  … e mais {len(enum_gaps) - 40}", file=sys.stderr)
            ok = False
        if MFE_CATALOG.read_text(encoding="utf-8") != mfe:
            print("Drift em dataParamCatalog.ts — rode com --write.", file=sys.stderr)
            ok = False
        if PRESENTATION_LABELS.read_text(encoding="utf-8") != presentation:
            print("Drift em formatDataSourceBindingSummary.ts — rode com --write.", file=sys.stderr)
            ok = False
        if ok:
            print(
                f"OK — catálogos TV alinhados ({len(labels)} labels, {len(enum_pt)} enums)."
            )
            return 0
        return 1

    if enum_gaps:
        print(
            f"Aviso: {len(enum_gaps)} valores de enum sem enumLabels bilíngue "
            "(o --check falhará até completar).",
            file=sys.stderr,
        )

    if not args.write:
        print(
            f"Dry-run — {len(labels)} labels / {len(hints)} hints / {len(enum_pt)} enums. Use --write."
        )
        return 0

    MFE_CATALOG.write_text(mfe, encoding="utf-8")
    PRESENTATION_LABELS.write_text(presentation, encoding="utf-8")
    print(
        f"Gravado {MFE_CATALOG} e {PRESENTATION_LABELS} "
        f"({len(labels)} labels, {len(enum_pt)} enums)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
