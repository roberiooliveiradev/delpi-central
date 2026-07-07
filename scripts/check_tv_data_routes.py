#!/usr/bin/env python3
"""Valida allowlist TV × OpenAPI api-delpi (operationId, path, método GET)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TV_ROUTES_PATH = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_routes.json"
OPENAPI_BASELINE_PATH = ROOT / "api-delpi" / "app" / "content" / "openapi_baseline.json"


def load_openapi_operations(baseline_path: Path) -> dict[str, dict]:
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    operations = payload.get("operations") or payload.get("paths") or []
    indexed: dict[str, dict] = {}
    if not isinstance(operations, list):
        return indexed
    for item in operations:
        if not isinstance(item, dict):
            continue
        operation_id = str(item.get("operationId") or "").strip()
        if operation_id:
            indexed[operation_id] = item
    return indexed


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

    openapi_ops = load_openapi_operations(baseline_path)
    for route in load_tv_routes(routes_path):
        operation_id = str(route.get("operationId") or "").strip()
        if not operation_id:
            errors.append("Rota TV sem operationId.")
            continue

        openapi_op = openapi_ops.get(operation_id)
        if openapi_op is None:
            errors.append(f"operationId fora do OpenAPI: {operation_id}")
            continue

        openapi_method = str(openapi_op.get("method") or "").upper()
        if openapi_method != "GET":
            errors.append(
                f"{operation_id}: OpenAPI expõe {openapi_method or '?'} — catálogo TV aceita só GET."
            )

        catalog_method = str(route.get("httpMethod") or "GET").upper()
        if catalog_method != "GET":
            errors.append(f"{operation_id}: httpMethod do catálogo deve ser GET, recebido {catalog_method!r}.")

        path = str(route.get("path") or "").strip()
        openapi_path = str(openapi_op.get("path") or "").strip()
        if not path.startswith("/"):
            errors.append(f"Path inválido para {operation_id}: {path!r}")
        elif openapi_path and path != openapi_path:
            errors.append(
                f"{operation_id}: path do catálogo ({path}) difere do OpenAPI ({openapi_path})."
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate allowlist TV × OpenAPI api-delpi (GET only)")
    parser.add_argument("--check", action="store_true", help="Falha se houver drift")
    parser.add_argument("--routes", type=Path, default=TV_ROUTES_PATH)
    parser.add_argument("--openapi", type=Path, default=OPENAPI_BASELINE_PATH)
    args = parser.parse_args()

    errors = check(routes_path=args.routes, baseline_path=args.openapi)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1 if args.check else 0
    print(f"OK — {len(load_tv_routes(args.routes))} rotas GET alinhadas ao OpenAPI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
