#!/usr/bin/env python3
"""Gera/valida baseline OpenAPI das rotas HTTP (transformometro-api).

Uso:
  PYTHONPATH=. python scripts/sync_openapi_baseline.py --write
  PYTHONPATH=. python scripts/sync_openapi_baseline.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent
SHARED_ROOT = REPO_ROOT / "shared"
BASELINE_PATH = API_ROOT / "tm_app" / "content" / "openapi_baseline.json"

for _path in (API_ROOT, SHARED_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


def _module_for_path(path: str) -> str:
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return "root"
    if parts[0] != "transformometro":
        return parts[0]
    if len(parts) == 1:
        return "transformometro"
    second = parts[1]
    if second in {"dashboard", "data", "colaboracao", "realtime"}:
        return second
    if second == "integrations" or (len(parts) > 2 and parts[1] == "integrations"):
        return "integrations"
    return "crud"


def build_baseline() -> dict:
    from tests.support.test_app import create_test_app

    app = create_test_app()
    schema = app.openapi()
    operations: list[dict] = []
    for path, methods in (schema.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            if not isinstance(op, dict):
                continue
            oid = str(op.get("operationId") or "").strip()
            if not oid:
                continue
            operations.append(
                {
                    "operationId": oid,
                    "method": method.upper(),
                    "path": path,
                    "module": _module_for_path(path),
                }
            )
    operations.sort(key=lambda r: (r["module"], r["path"], r["method"], r["operationId"]))
    return {
        "version": 1,
        "generatedAt": date.today().isoformat(),
        "operation_count": len(operations),
        "operations": operations,
    }


def _fingerprint(payload: dict) -> list[str]:
    return sorted(
        f"{row.get('method')}:{row.get('path')}:{row.get('operationId')}"
        for row in (payload.get("operations") or [])
        if isinstance(row, dict)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    args = parser.parse_args(argv)

    baseline = build_baseline()

    if args.write:
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(
            json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Gravado {args.baseline} (ops={baseline['operation_count']})")
        return 0

    if args.check:
        if not args.baseline.is_file():
            print(f"Baseline ausente: {args.baseline}", file=sys.stderr)
            return 1
        stored = json.loads(args.baseline.read_text(encoding="utf-8"))
        if _fingerprint(stored) != _fingerprint(baseline):
            print("Drift no OpenAPI baseline — rode --write.", file=sys.stderr)
            return 1
        print(f"OK — baseline sincronizado (ops={baseline['operation_count']})")
        return 0

    print(f"ops={baseline['operation_count']}")
    for row in baseline["operations"][:20]:
        print(f"  {row['method']:6} {row['path']}  {row['operationId']}")
    if baseline["operation_count"] > 20:
        print(f"  … +{baseline['operation_count'] - 20}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
