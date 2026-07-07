#!/usr/bin/env python3
"""Valida operationIds de tv_data_routes.json contra openapi_baseline da api-delpi."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TV_ROUTES_PATH = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_routes.json"
OPENAPI_BASELINE_PATH = ROOT / "api-delpi" / "app" / "content" / "openapi_baseline.json"


def load_operation_ids(baseline_path: Path) -> set[str]:
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    operations = payload.get("operations") or payload.get("paths") or []
    ids: set[str] = set()
    if isinstance(operations, list):
        for item in operations:
            if isinstance(item, dict):
                op = item.get("operationId")
                if isinstance(op, str) and op.strip():
                    ids.add(op.strip())
    return ids


def load_tv_routes(routes_path: Path) -> list[dict]:
    payload = json.loads(routes_path.read_text(encoding="utf-8"))
    raw = payload.get("routes") or []
    return [item for item in raw if isinstance(item, dict)]


def check(*, routes_path: Path, baseline_path: Path) -> list[str]:
    errors: list[str] = []
    if not routes_path.is_file():
        return [f"Catálogo TV ausente: {routes_path}"]
    if not baseline_path.is_file():
        return [f"OpenAPI baseline ausente: {baseline_path}"]

    openapi_ids = load_operation_ids(baseline_path)
    for route in load_tv_routes(routes_path):
        operation_id = str(route.get("operationId") or "").strip()
        if not operation_id:
            errors.append("Rota TV sem operationId.")
            continue
        if operation_id not in openapi_ids:
            errors.append(f"operationId fora do OpenAPI: {operation_id}")
        path = str(route.get("path") or "").strip()
        if not path.startswith("/"):
            errors.append(f"Path inválido para {operation_id}: {path!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate allowlist TV × OpenAPI api-delpi")
    parser.add_argument("--check", action="store_true", help="Falha se houver drift")
    parser.add_argument("--routes", type=Path, default=TV_ROUTES_PATH)
    parser.add_argument("--openapi", type=Path, default=OPENAPI_BASELINE_PATH)
    args = parser.parse_args()

    errors = check(routes_path=args.routes, baseline_path=args.openapi)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1 if args.check else 0
    print(f"OK — {len(load_tv_routes(args.routes))} rotas TV alinhadas ao OpenAPI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
