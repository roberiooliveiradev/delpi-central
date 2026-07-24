#!/usr/bin/env python3
"""Inventário de cobertura de testes por rota OpenAPI (transformometro-api).

Uso:
  PYTHONPATH=. python scripts/audit_route_test_coverage.py --report
  PYTHONPATH=. python scripts/audit_route_test_coverage.py --write
  PYTHONPATH=. python scripts/audit_route_test_coverage.py --check
  PYTHONPATH=. python scripts/audit_route_test_coverage.py --check-complete

Regra covered: operationId aparece como substring em tests/**/*.py
(exceto o próprio inventário). Status exempt é preservado no --write.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = API_ROOT / "tm_app" / "content" / "openapi_baseline.json"
COVERAGE_PATH = API_ROOT / "tm_app" / "content" / "route_test_coverage.json"
TESTS_ROOT = API_ROOT / "tests"

_DEFAULT_EXEMPTS: dict[str, str] = {
    # WebSocket — não entra no OpenAPI HTTP baseline; reservado se aparecer.
    "realtime_ws": "websocket_not_http_smoke",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _baseline_operations(baseline: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for op in baseline.get("operations") or []:
        if not isinstance(op, dict):
            continue
        oid = str(op.get("operationId") or "").strip()
        if not oid:
            continue
        rows.append(
            {
                "operationId": oid,
                "method": str(op.get("method") or "").upper(),
                "path": str(op.get("path") or ""),
                "module": str(op.get("module") or "root"),
            }
        )
    return rows


def _scan_test_blob() -> str:
    chunks: list[str] = []
    if not TESTS_ROOT.is_dir():
        return ""
    for path in TESTS_ROOT.rglob("*.py"):
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return "\n".join(chunks)


def _previous_exempts(path: Path) -> dict[str, str]:
    out = dict(_DEFAULT_EXEMPTS)
    if not path.is_file():
        return out
    try:
        stored = _load_json(path)
    except (OSError, json.JSONDecodeError):
        return out
    for row in stored.get("operations") or []:
        if not isinstance(row, dict) or row.get("status") != "exempt":
            continue
        oid = str(row.get("operationId") or "").strip()
        reason = str(row.get("exemptReason") or "documented_exempt").strip()
        if oid:
            out[oid] = reason or "documented_exempt"
    return out


def build_coverage(
    baseline: dict[str, Any],
    *,
    test_blob: str | None = None,
    previous_coverage: Path | None = None,
) -> dict[str, Any]:
    blob = test_blob if test_blob is not None else _scan_test_blob()
    exempts = _previous_exempts(previous_coverage or COVERAGE_PATH)
    operations: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()

    for row in _baseline_operations(baseline):
        oid = row["operationId"]
        if oid in exempts:
            status = "exempt"
            entry = {**row, "status": status, "exemptReason": exempts[oid]}
        elif oid in blob:
            status = "covered"
            entry = {**row, "status": status}
        else:
            status = "gap"
            entry = {**row, "status": status}
        counts[status] += 1
        operations.append(entry)

    by_module: dict[str, dict[str, int]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for op in operations:
        grouped[str(op["module"])].append(op)
    for module, rows in sorted(grouped.items()):
        by_module[module] = {
            "total": len(rows),
            "covered": sum(1 for r in rows if r["status"] == "covered"),
            "gap": sum(1 for r in rows if r["status"] == "gap"),
            "exempt": sum(1 for r in rows if r["status"] == "exempt"),
        }

    return {
        "version": 1,
        "generatedAt": date.today().isoformat(),
        "baselineOperationCount": int(baseline.get("operation_count") or len(operations)),
        "operationCount": len(operations),
        "coveredCount": counts["covered"],
        "gapCount": counts["gap"],
        "exemptCount": counts["exempt"],
        "byModule": by_module,
        "operations": operations,
    }


def _fingerprint(payload: dict[str, Any]) -> list[str]:
    return sorted(
        str(row.get("operationId"))
        for row in (payload.get("operations") or [])
        if isinstance(row, dict) and row.get("operationId")
    )


def print_report(coverage: dict[str, Any]) -> None:
    total = coverage["operationCount"]
    covered = coverage["coveredCount"]
    gap = coverage["gapCount"]
    exempt = coverage["exemptCount"]
    pct = (100.0 * covered / total) if total else 0.0
    print(f"ops={total} covered={covered} ({pct:.0f}%) gap={gap} exempt={exempt}")
    print(f"{'módulo':28} {'ops':>4} {'cov':>4} {'gap':>4} {'ex':>3}")
    for module, stats in sorted(
        (coverage.get("byModule") or {}).items(),
        key=lambda item: (-item[1].get("gap", 0), item[0]),
    ):
        print(
            f"{module:28} {stats['total']:4} {stats['covered']:4} "
            f"{stats['gap']:4} {stats['exempt']:3}"
        )
    gaps = [op for op in coverage.get("operations") or [] if op.get("status") == "gap"]
    if gaps:
        print("\nGaps (amostra, até 40):")
        for op in gaps[:40]:
            print(f"  {op['method']:6} {op['path']}  oid={op['operationId']}")
        if len(gaps) > 40:
            print(f"  … +{len(gaps) - 40} more")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--coverage", type=Path, default=COVERAGE_PATH)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-complete", action="store_true")
    args = parser.parse_args(argv)

    if not args.baseline.is_file():
        print(f"Baseline ausente: {args.baseline}", file=sys.stderr)
        return 1

    baseline = _load_json(args.baseline)
    coverage = build_coverage(baseline, previous_coverage=args.coverage)

    if args.write:
        args.coverage.parent.mkdir(parents=True, exist_ok=True)
        args.coverage.write_text(
            json.dumps(coverage, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            f"Gravado {args.coverage} "
            f"(covered={coverage['coveredCount']} gap={coverage['gapCount']} "
            f"exempt={coverage['exemptCount']})"
        )

    if args.report or (not args.write and not args.check and not args.check_complete):
        print_report(coverage)

    if args.check:
        if not args.coverage.is_file():
            print(f"Inventário ausente: {args.coverage} — rode --write.", file=sys.stderr)
            return 1
        stored = _load_json(args.coverage)
        if _fingerprint(stored) != _fingerprint(coverage):
            print("Drift no inventário de rotas — rode com --write.", file=sys.stderr)
            return 1
        live_by_oid = {op["operationId"]: op for op in coverage["operations"]}
        drift_status = 0
        for row in stored.get("operations") or []:
            if not isinstance(row, dict):
                continue
            oid = str(row.get("operationId") or "")
            live = live_by_oid.get(oid)
            if not live or row.get("status") == "exempt":
                continue
            if row.get("status") != live.get("status"):
                drift_status += 1
        if drift_status:
            print(
                f"Drift de status em {drift_status} operação(ões) — rode --write.",
                file=sys.stderr,
            )
            return 1
        print(
            f"OK — inventário sincronizado "
            f"(covered={coverage['coveredCount']} gap={coverage['gapCount']})."
        )

    if args.check_complete:
        gaps = [
            op["operationId"]
            for op in coverage.get("operations") or []
            if op.get("status") == "gap"
        ]
        if gaps:
            print(f"Falha — {len(gaps)} rota(s) sem teste (status=gap).", file=sys.stderr)
            for oid in gaps[:40]:
                print(f"  - {oid}", file=sys.stderr)
            if len(gaps) > 40:
                print(f"  … +{len(gaps) - 40}", file=sys.stderr)
            return 1
        print("OK — cobertura completa (sem gaps).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
