#!/usr/bin/env python3
"""Gate CI: catálogo TV não inventa enums/labels à parte do OpenAPI baseline.

Falha quando:
  - paramSchema.enum no TV diverge do enum do baseline OpenAPI (quando o baseline tem enum);
  - params canônicos (department_id, granularity, …) têm enum só no TV e não no OpenAPI;
  - operationId legado conhecido ainda aparece como id canônico no catálogo;
  - com --strict-auto-ids: qualquer operationId auto-FastAPI ainda listado no catálogo TV.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_BASELINE_PATH = ROOT / "api-delpi" / "app" / "content" / "openapi_baseline.json"
TV_ROUTES_PATH = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_routes.json"
ALIASES_PATH = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_operation_id_aliases.json"

CANONICAL_ENUM_PARAMS = frozenset(
    {
        "department_id",
        "granularity",
        "customer_segment",
        "loss_type",
        "product_type",
        "sort_dir",
        "linked_sort_dir",
        "stock_method",
        "direction",
        "orderDir",
    }
)

FORBIDDEN_OPERATION_IDS = frozenset(
    {
        "get_dashboard_department_idd_dashboard_department_idd_get",
    }
)

_AUTO_SUFFIX = re.compile(r"_(get|post|put|patch|delete)$", re.IGNORECASE)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _baseline_param_index(baseline: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    indexed: dict[str, dict[str, dict[str, Any]]] = {}
    for op in baseline.get("operations") or []:
        if not isinstance(op, dict):
            continue
        if str(op.get("method") or "").upper() != "GET":
            continue
        oid = str(op.get("operationId") or "").strip()
        if not oid:
            continue
        params: dict[str, dict[str, Any]] = {}
        for raw in op.get("parameters") or []:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("name") or "").strip()
            if name:
                params[name] = raw
        indexed[oid] = params
    return indexed


def check_parity(*, baseline_path: Path, routes_path: Path) -> list[str]:
    baseline = _load(baseline_path)
    routes_payload = _load(routes_path)
    routes = routes_payload.get("routes") if isinstance(routes_payload, dict) else None
    if not isinstance(routes, list):
        return ["tv_data_routes.json sem lista routes"]

    openapi_params = _baseline_param_index(baseline)
    issues: list[str] = []

    for route in routes:
        if not isinstance(route, dict):
            continue
        oid = str(route.get("operationId") or "").strip()
        if oid in FORBIDDEN_OPERATION_IDS:
            issues.append(f"{oid}: operationId legado auto-FastAPI — use get_dashboard_department_idd")
        schema = route.get("paramSchema") if isinstance(route.get("paramSchema"), dict) else {}
        baseline_params = openapi_params.get(oid) or {}
        for name, entry in schema.items():
            if not isinstance(entry, dict):
                continue
            tv_enum = entry.get("enum")
            if not isinstance(tv_enum, list) or not tv_enum:
                continue
            openapi_entry = baseline_params.get(name) or {}
            openapi_enum = openapi_entry.get("enum")
            if isinstance(openapi_enum, list) and openapi_enum:
                if [str(x) for x in tv_enum] != [str(x) for x in openapi_enum]:
                    issues.append(
                        f"{oid}.{name}: enum TV {tv_enum} ≠ OpenAPI {openapi_enum}"
                    )
            elif name in CANONICAL_ENUM_PARAMS:
                issues.append(
                    f"{oid}.{name}: enum só no catálogo TV {tv_enum} — declare no OpenAPI (Query enum=)"
                )
    return issues


def check_no_auto_ids_as_canonical(*, routes_path: Path) -> list[str]:
    """Após ondas R1+: catálogo TV não deve listar operationId com sufixo auto."""
    routes_payload = _load(routes_path)
    routes = routes_payload.get("routes") if isinstance(routes_payload, dict) else None
    if not isinstance(routes, list):
        return ["tv_data_routes.json sem lista routes"]
    issues: list[str] = []
    for route in routes:
        if not isinstance(route, dict):
            continue
        oid = str(route.get("operationId") or "").strip()
        if oid and _AUTO_SUFFIX.search(oid):
            issues.append(f"{oid}: ainda auto no catálogo — renomeie e use alias")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=OPENAPI_BASELINE_PATH)
    parser.add_argument("--routes", type=Path, default=TV_ROUTES_PATH)
    parser.add_argument("--check", action="store_true", help="Exit 1 se houver drift")
    parser.add_argument(
        "--strict-auto-ids",
        action="store_true",
        help="Falha se o catálogo TV ainda listar operationId auto-FastAPI",
    )
    args = parser.parse_args()

    if not args.baseline.is_file():
        print(f"Baseline ausente: {args.baseline}", file=sys.stderr)
        return 1
    if not args.routes.is_file():
        print(f"Catálogo TV ausente: {args.routes}", file=sys.stderr)
        return 1

    issues = check_parity(baseline_path=args.baseline, routes_path=args.routes)
    if args.strict_auto_ids:
        issues.extend(check_no_auto_ids_as_canonical(routes_path=args.routes))

    if issues:
        print(f"Falha — {len(issues)} problema(s) de paridade OpenAPI×TV:", file=sys.stderr)
        for item in issues[:40]:
            print(f"  - {item}", file=sys.stderr)
        if len(issues) > 40:
            print(f"  … +{len(issues) - 40} outros", file=sys.stderr)
        return 1 if args.check else 0

    print("OK — catálogo TV alinhado ao OpenAPI (enums canônicos).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
