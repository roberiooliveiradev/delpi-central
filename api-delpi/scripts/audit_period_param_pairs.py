#!/usr/bin/env python3
"""Inventário e gate de pares de período HTTP (start_date/end_date canônico).

Uso:
  python scripts/audit_period_param_pairs.py --report
  python scripts/audit_period_param_pairs.py --check
      # falha se houver param legado NÃO deprecated (pós-migração / rotas novas)

Exclusões semânticas: issue_date_*, modified_*, from/to (scheduling).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = API_ROOT / "app" / "content" / "openapi_baseline.json"

CANONICAL = ("start_date", "end_date")
LEGACY_PAIRS: tuple[tuple[str, str], ...] = (
    ("date_start", "date_end"),
    ("dataInicio", "dataFim"),
    ("data_inicio", "data_fim"),
    ("date_from", "date_to"),
    ("data_inicial", "data_final"),
)
SEMANTIC_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("issue_date_start", "issue_date_end"),
        ("modified_from", "modified_to"),
        ("from", "to"),
    }
)
ALL_START = {CANONICAL[0], *(p[0] for p in LEGACY_PAIRS), *(p[0] for p in SEMANTIC_PAIRS)}
ALL_END = {CANONICAL[1], *(p[1] for p in LEGACY_PAIRS), *(p[1] for p in SEMANTIC_PAIRS)}


def _param_names(operation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for param in operation.get("parameters") or []:
        if not isinstance(param, dict):
            continue
        name = str(param.get("name") or "").strip()
        if name:
            out[name] = param
    return out


def _detect_pair(names: set[str]) -> tuple[str, str] | None:
    if CANONICAL[0] in names and CANONICAL[1] in names:
        return CANONICAL
    for start, end in LEGACY_PAIRS:
        if start in names and end in names:
            return start, end
    for start, end in SEMANTIC_PAIRS:
        if start in names and end in names:
            return start, end
    return None


def load_operations(baseline_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    ops = payload.get("operations") if isinstance(payload, dict) else None
    if isinstance(ops, list):
        return [op for op in ops if isinstance(op, dict)]
    # Fallback: OpenAPI paths shape
    paths = payload.get("paths") if isinstance(payload, dict) else {}
    collected: list[dict[str, Any]] = []
    if isinstance(paths, dict):
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method, operation in methods.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                if not isinstance(operation, dict):
                    continue
                item = dict(operation)
                item["path"] = path
                item["httpMethod"] = method.upper()
                collected.append(item)
    return collected


def inventariar(baseline_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for operation in load_operations(baseline_path):
        params = _param_names(operation)
        names = set(params)
        pair = _detect_pair(names)
        if not pair:
            # start/end soltos sem par completo
            starts = sorted(names & ALL_START)
            ends = sorted(names & ALL_END)
            if not starts and not ends:
                continue
            pair_label = f"incomplete:{','.join(starts)}/{','.join(ends)}"
            family = "incomplete"
        else:
            pair_label = f"{pair[0]}/{pair[1]}"
            if pair == CANONICAL:
                family = "canonical"
            elif pair in SEMANTIC_PAIRS:
                family = "semantic"
            else:
                family = "legacy"
        deprecated_flags = {
            name: bool(params[name].get("deprecated"))
            for name in (pair if isinstance(pair, tuple) else [])
            if isinstance(pair, tuple) and name in params
        }
        legacy_aliases_present = [
            name
            for start, end in LEGACY_PAIRS
            for name in (start, end)
            if name in params
        ]
        rows.append(
            {
                "operationId": str(operation.get("operationId") or "").strip(),
                "path": str(operation.get("path") or "").strip(),
                "pair": pair_label,
                "family": family,
                "deprecated": deprecated_flags,
                "legacyAliases": {
                    name: bool(params[name].get("deprecated"))
                    for name in legacy_aliases_present
                },
            }
        )
    return sorted(rows, key=lambda row: (row["family"], row["pair"], row["operationId"]))


def report(rows: list[dict[str, Any]]) -> None:
    counts = Counter(row["family"] for row in rows)
    pair_counts = Counter(row["pair"] for row in rows)
    print(f"Total operações com período: {len(rows)}")
    print("Por família:")
    for family, count in sorted(counts.items()):
        print(f"  {family}: {count}")
    print("Por par:")
    for pair, count in pair_counts.most_common():
        print(f"  {pair}: {count}")
    print("\nLegado (não semântico):")
    for row in rows:
        if row["family"] != "legacy":
            continue
        print(f"  {row['operationId']}\t{row['path']}\t{row['pair']}")


def check_no_active_legacy(rows: list[dict[str, Any]]) -> list[str]:
    """Após migração completa: legado só é permitido se deprecated=True no OpenAPI.

    - Família `legacy` (sem canônico): todos os params do par devem estar deprecated
      (ou a rota ainda não migrou — falha).
    - Família `canonical` com aliases no schema: cada alias deve estar deprecated.
    """
    errors: list[str] = []
    for row in rows:
        if row["family"] == "legacy":
            flags = row.get("deprecated") or {}
            if not flags or not all(flags.values()):
                errors.append(
                    f"{row['operationId']}: par legado ativo {row['pair']} "
                    "(migrar para start_date/end_date + alias deprecated)"
                )
            continue
        if row["family"] != "canonical":
            continue
        aliases = row.get("legacyAliases") or {}
        for name, deprecated in aliases.items():
            if not deprecated:
                errors.append(
                    f"{row['operationId']}: alias legado ativo `{name}` "
                    "(marcar deprecated=True ou remover)"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--report", action="store_true", help="Imprime inventário")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Gate: falha se houver legado ativo (use --strict-active)",
    )
    parser.add_argument(
        "--strict-active",
        action="store_true",
        help="Com --check: exige zero legado não-deprecated",
    )
    parser.add_argument(
        "--forbid-new-legacy",
        action="store_true",
        help="Com --check: mesmo que --strict-active (alias para CI pós-migração)",
    )
    args = parser.parse_args()
    if not args.baseline.is_file():
        print(f"Baseline não encontrado: {args.baseline}", file=sys.stderr)
        return 2
    rows = inventariar(args.baseline)
    if args.report or not (args.check or args.strict_active or args.forbid_new_legacy):
        report(rows)
    if args.check or args.strict_active or args.forbid_new_legacy:
        if args.strict_active or args.forbid_new_legacy:
            errors = check_no_active_legacy(rows)
            if errors:
                print(f"FAIL: {len(errors)} par(es) legado ativo(s):", file=sys.stderr)
                for err in errors[:40]:
                    print(f"  {err}", file=sys.stderr)
                if len(errors) > 40:
                    print(f"  … +{len(errors) - 40}", file=sys.stderr)
                return 1
            print("OK: nenhum par legado ativo (todos canônicos ou deprecated/semânticos)")
        else:
            legacy = sum(1 for row in rows if row["family"] == "legacy")
            print(
                f"OK (modo inventário): {legacy} ops legado — "
                "use --strict-active após migração completa"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
