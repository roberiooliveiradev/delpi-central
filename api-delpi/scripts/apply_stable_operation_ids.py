#!/usr/bin/env python3
"""Aplica operation_id estável nos decorators FastAPI a partir de api_delpi_success.

Varre routers, encontra o operation_id do envelope na mesma função e replica no
@router.get/post/... quando ainda ausente. Atualiza baseline, aliases TV,
audience e registry do chat.

Uso (na raiz do monorepo):
  python3 api-delpi/scripts/apply_stable_operation_ids.py --tag Qualidade --write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTES_ROOT = API_ROOT / "app" / "interface" / "http" / "routes"
BASELINE_PATH = API_ROOT / "app" / "content" / "openapi_baseline.json"
INVENTORY_PATH = API_ROOT / "app" / "content" / "openapi_operation_id_inventory.json"
AUDIENCE_PATH = API_ROOT / "app" / "content" / "tv_route_audience.json"
ALIASES_PATH = REPO_ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_operation_id_aliases.json"
CHAT_REGISTRY_PATH = (
    REPO_ROOT
    / "minha-delpi-ai-api"
    / "app"
    / "content"
    / "pt-BR"
    / "assistant"
    / "operational_route_registry.json"
)

_DECORATOR_RE = re.compile(
    r"@(router|public_router)\.(get|post|put|patch|delete)\(\s*(?P<args>.*?)\s*\)\s*\n"
    r"(?:@[^\n]+\n)*"
    r"def (?P<fn>[a-zA-Z_][a-zA-Z0-9_]*)\(",
    re.DOTALL,
)
_SUCCESS_OP_RE = re.compile(r'operation_id\s*=\s*["\']([a-zA-Z0-9_]+)["\']')


def _decorator_has_operation_id(args: str) -> bool:
    return "operation_id" in args or "operationId" in args


def _inject_operation_id(args: str, operation_id: str) -> str:
    args = args.strip()
    if not args:
        return f'operation_id="{operation_id}"'
    # Path positional first: "/areas" or '/areas'
    return f'{args}, operation_id="{operation_id}"'


def patch_router_file(path: Path) -> list[tuple[str, str]]:
    """Retorna lista (function_name, operation_id) aplicados."""
    text = path.read_text(encoding="utf-8")
    applied: list[tuple[str, str]] = []

    # Process from end to start to keep offsets valid.
    matches = list(_DECORATOR_RE.finditer(text))
    for match in reversed(matches):
        fn = match.group("fn")
        args = match.group("args")
        if _decorator_has_operation_id(args):
            continue
        # Já recebe operation_id via **helper OpenAPI — não injetar.
        if "**" in args:
            continue
        # Body: from def to next top-level def or end — approximate with next match start
        start = match.end()
        # Find end of function roughly: next \ndef at column 0 or @router
        next_def = re.search(r"\n(?:def |@router\.|@public_router\.)", text[start:])
        end = start + next_def.start() if next_def else len(text)
        body = text[start:end]
        ops = _SUCCESS_OP_RE.findall(body)
        if not ops:
            continue
        # Prefer last unique / most common — usually one
        operation_id = ops[-1]
        new_args = _inject_operation_id(args, operation_id)
        old = match.group(0)
        # Rebuild decorator line(s): only replace the parentheses args of the router call
        router_name = match.group(1)
        method = match.group(2)
        # Reconstruct carefully
        prefix = f"@{router_name}.{method}("
        # Find original call span within match
        call_match = re.search(
            rf"@{router_name}\.{method}\(\s*(.*?)\s*\)",
            old,
            re.DOTALL,
        )
        if not call_match:
            continue
        new_call = f"@{router_name}.{method}({new_args})"
        new_block = old.replace(call_match.group(0), new_call, 1)
        text = text[: match.start()] + new_block + text[match.end() :]
        applied.append((fn, operation_id))

    if applied:
        path.write_text(text, encoding="utf-8")
    return list(reversed(applied))


def build_legacy_to_canonical_from_baseline_and_inventory(
    tag_filter: str | None,
) -> dict[str, str]:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for row in inventory.get("operations") or []:
        if not isinstance(row, dict) or row.get("stable"):
            continue
        if tag_filter and row.get("tag") != tag_filter:
            continue
        legacy = str(row.get("operationId") or "")
        # Prefer recommended; may be overridden after router patch via envelope ids
        recommended = str(row.get("recommendedCanonical") or "").strip()
        if legacy and recommended:
            mapping[legacy] = recommended
    return mapping


def remap_json_operation_ids(payload: Any, mapping: dict[str, str]) -> int:
    changed = 0
    if isinstance(payload, dict):
        for key, value in list(payload.items()):
            if key in {"operationId", "operation_id"} and isinstance(value, str):
                new = mapping.get(value)
                if new and new != value:
                    payload[key] = new
                    changed += 1
            else:
                changed += remap_json_operation_ids(value, mapping)
    elif isinstance(payload, list):
        for item in payload:
            changed += remap_json_operation_ids(item, mapping)
    return changed


def update_baseline(mapping: dict[str, str]) -> int:
    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    changed = 0
    for op in payload.get("operations") or []:
        if not isinstance(op, dict):
            continue
        oid = str(op.get("operationId") or "")
        if oid in mapping:
            op["operationId"] = mapping[oid]
            changed += 1
    if changed:
        BASELINE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return changed


def update_aliases(mapping: dict[str, str]) -> int:
    payload: dict[str, Any]
    if ALIASES_PATH.is_file():
        payload = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    else:
        payload = {"version": 1, "description": "Aliases operationId legado → canônico", "aliases": {}}
    aliases = payload.setdefault("aliases", {})
    added = 0
    for legacy, canonical in sorted(mapping.items()):
        if legacy == canonical:
            continue
        if aliases.get(legacy) != canonical:
            aliases[legacy] = canonical
            added += 1
    payload["aliases"] = dict(sorted(aliases.items()))
    ALIASES_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return added


def update_audience(mapping: dict[str, str]) -> int:
    if not AUDIENCE_PATH.is_file():
        return 0
    payload = json.loads(AUDIENCE_PATH.read_text(encoding="utf-8"))
    routes = payload.get("routes")
    if not isinstance(routes, dict):
        return 0
    changed = 0
    for legacy, canonical in mapping.items():
        if legacy in routes and canonical not in routes:
            routes[canonical] = routes.pop(legacy)
            changed += 1
        elif legacy in routes and canonical in routes:
            routes.pop(legacy, None)
            changed += 1
    AUDIENCE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def update_chat_registry(mapping: dict[str, str]) -> int:
    if not CHAT_REGISTRY_PATH.is_file():
        return 0
    payload = json.loads(CHAT_REGISTRY_PATH.read_text(encoding="utf-8"))
    changed = remap_json_operation_ids(payload, mapping)
    if changed:
        CHAT_REGISTRY_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return changed


def refine_mapping_from_patched_routers(
    tag_filter: str | None,
    applied_by_fn: dict[str, str],
) -> dict[str, str]:
    """Combina inventário + operation_ids aplicados nos decorators."""
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    for row in inventory.get("operations") or []:
        if not isinstance(row, dict) or row.get("stable"):
            continue
        if tag_filter and row.get("tag") != tag_filter:
            continue
        legacy = str(row.get("operationId") or "")
        fn = str(row.get("functionName") or "")
        canonical = applied_by_fn.get(fn) or str(row.get("recommendedCanonical") or "")
        # Fix known registry names that differ from naive recommend
        if legacy and canonical:
            mapping[legacy] = canonical
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tag",
        default="",
        help="Tag OpenAPI a processar (vazio = todas as auto do inventário)",
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--routes-glob",
        default="quality/**/*.py",
        help="Glob relativo a routes/",
    )
    args = parser.parse_args()

    if not args.write:
        print("Dry-run: use --write para aplicar.", file=sys.stderr)

    files = sorted(ROUTES_ROOT.glob(args.routes_glob))
    applied_by_fn: dict[str, str] = {}
    for path in files:
        if path.name.startswith("test"):
            continue
        applied = patch_router_file(path) if args.write else []
        if not args.write:
            # dry: still scan
            text = path.read_text(encoding="utf-8")
            for match in _DECORATOR_RE.finditer(text):
                if _decorator_has_operation_id(match.group("args")):
                    continue
                start = match.end()
                next_def = re.search(r"\n(?:def |@router\.|@public_router\.)", text[start:])
                end = start + next_def.start() if next_def else len(text)
                ops = _SUCCESS_OP_RE.findall(text[start:end])
                if ops:
                    applied.append((match.group("fn"), ops[-1]))
        for fn, oid in applied:
            applied_by_fn[fn] = oid
        if applied:
            print(f"{path.relative_to(API_ROOT)}: {len(applied)} operation_id")

    mapping = refine_mapping_from_patched_routers(args.tag, applied_by_fn)
    # Override with inventory recommend when function not patched but recommend exists
    base_map = build_legacy_to_canonical_from_baseline_and_inventory(args.tag)
    for legacy, canonical in base_map.items():
        mapping.setdefault(legacy, canonical)
    # Prefer applied fn mapping when functionName matches
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    for row in inventory.get("operations") or []:
        if not isinstance(row, dict) or row.get("stable"):
            continue
        if args.tag and row.get("tag") != args.tag:
            continue
        legacy = str(row.get("operationId") or "")
        fn = str(row.get("functionName") or "")
        if fn in applied_by_fn:
            mapping[legacy] = applied_by_fn[fn]

    print(f"mapping size={len(mapping)} applied_fns={len(applied_by_fn)}")

    if not args.write:
        for legacy, canonical in list(mapping.items())[:15]:
            print(f"  {legacy} -> {canonical}")
        return 0

    print("baseline", update_baseline(mapping))
    print("aliases", update_aliases(mapping))
    print("audience", update_audience(mapping))
    print("chat_registry", update_chat_registry(mapping))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
