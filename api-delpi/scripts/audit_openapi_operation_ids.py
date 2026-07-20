#!/usr/bin/env python3
"""Inventário de operationId OpenAPI — estáveis vs auto-FastAPI.

Uso:
  python scripts/audit_openapi_operation_ids.py --write
  python scripts/audit_openapi_operation_ids.py --check          # inventário sincronizado
  python scripts/audit_openapi_operation_ids.py --report         # resumo stdout

Heurística auto: operationId termina em _get|_post|_put|_patch|_delete (padrão FastAPI).
Sugestão canônica: nome da função + prefixo de domínio quando o nome for genérico demais.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = API_ROOT / "app" / "content" / "openapi_baseline.json"
INVENTORY_PATH = API_ROOT / "app" / "content" / "openapi_operation_id_inventory.json"
ALIASES_PATH = REPO_ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_operation_id_aliases.json"

_AUTO_SUFFIX = re.compile(r"_(get|post|put|patch|delete)$", re.IGNORECASE)

_VERBS = (
    "force_delete_",
    "complete_",
    "reopen_",
    "download_",
    "upload_",
    "publish_",
    "create_",
    "update_",
    "delete_",
    "close_",
    "join_",
    "list_",
    "get_",
    "post_",
    "put_",
    "patch_",
    "search_",
    "export_",
    "remove_",
    "add_",
    "set_",
    "save_",
)


def is_auto_operation_id(operation_id: str) -> bool:
    return bool(_AUTO_SUFFIX.search(str(operation_id or "").strip()))


def path_to_fastapi_id_fragment(path: str) -> str:
    segs: list[str] = []
    for seg in str(path or "").strip("/").split("/"):
        if not seg:
            continue
        if seg.startswith("{") and seg.endswith("}"):
            segs.append(f"_{seg[1:-1]}_")
        else:
            segs.append(seg.replace("-", "_").replace(".", "_"))
    return "_".join(segs)


def extract_function_name(operation_id: str, path: str, method: str) -> str:
    oid = str(operation_id or "").strip()
    method_l = str(method or "get").lower()
    if not oid.endswith("_" + method_l):
        return oid
    body = oid[: -(len(method_l) + 1)]
    path_id = path_to_fastapi_id_fragment(path)
    for suf in (path_id, path_id.replace("__", "_")):
        if not suf:
            continue
        if body.endswith("_" + suf):
            return body[: -(len(suf) + 1)]
        if body.endswith(suf):
            return body[: -len(suf)].rstrip("_")
    return body


def recommend_canonical(function_name: str, path: str, tag: str) -> str:
    fn = str(function_name or "").strip()
    p = str(path or "")
    if not fn:
        return fn
    if "/audit-5s" in p:
        if "audit_5s" in fn:
            return fn
        for verb in _VERBS:
            if fn.startswith(verb):
                return f"{verb}audit_5s_{fn[len(verb):]}"
        return f"audit_5s_{fn}"
    if "cultura" in p:
        if "get" in fn:
            return "get_cultura_delpi_content"
        return "update_cultura_delpi_content"
    if "/scheduling" in p:
        return fn
    if p.startswith("/system") or tag == "system":
        return fn
    if "/customers" in p:
        return "search_customers" if "search" in fn else fn
    if "propostas" in p or "proposta" in p:
        if "overrides" in fn:
            return "export_proposta_comercial_pdf_with_overrides"
        if "pdf" in fn:
            return "export_proposta_comercial_pdf"
        return fn
    if "/public/quality-labels" in p:
        return "get_public_quality_label_inspection"
    if p.rstrip("/").endswith("/health") or tag == "Health":
        return "get_health"
    if "/products/" in p and "structure_excel" in fn:
        return "get_product_structure_excel_public"
    return fn


def build_inventory(baseline: dict[str, Any]) -> dict[str, Any]:
    ops = baseline.get("operations") or []
    rows: list[dict[str, Any]] = []
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for op in ops:
        if not isinstance(op, dict):
            continue
        oid = str(op.get("operationId") or "").strip()
        if not oid:
            continue
        method = str(op.get("method") or "").upper()
        path = str(op.get("path") or "")
        tags = op.get("tags") if isinstance(op.get("tags"), list) else []
        tag = str(tags[0]) if tags else "(sem tag)"
        auto = is_auto_operation_id(oid)
        row: dict[str, Any] = {
            "operationId": oid,
            "method": method,
            "path": path,
            "tag": tag,
            "stable": not auto,
        }
        if auto:
            fn = extract_function_name(oid, path, method)
            recommended = recommend_canonical(fn, path, tag)
            row["functionName"] = fn
            row["recommendedCanonical"] = recommended
            by_tag[tag].append(row)
        rows.append(row)

    auto_rows = [r for r in rows if not r["stable"]]
    recommendations = [str(r.get("recommendedCanonical") or "") for r in auto_rows]
    collisions = sorted(k for k, v in Counter(recommendations).items() if k and v > 1)

    return {
        "version": 1,
        "baselineVersion": str(baseline.get("version") or ""),
        "operationCount": len(rows),
        "stableCount": sum(1 for r in rows if r["stable"]),
        "autoCount": len(auto_rows),
        "recommendationCollisions": collisions,
        "autoByTag": {tag: len(items) for tag, items in sorted(by_tag.items(), key=lambda x: -len(x[1]))},
        "operations": sorted(rows, key=lambda r: (r["path"], r["method"], r["operationId"])),
    }


def load_aliases() -> dict[str, str]:
    if not ALIASES_PATH.is_file():
        return {}
    payload = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    raw = payload.get("aliases") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {
        str(k).strip(): str(v).strip()
        for k, v in raw.items()
        if str(k).strip() and str(v).strip()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--write", action="store_true", help="Grava inventário JSON")
    parser.add_argument("--check", action="store_true", help="Falha se inventário divergir")
    parser.add_argument("--report", action="store_true", help="Imprime resumo")
    parser.add_argument(
        "--check-aliases-coverage",
        action="store_true",
        help="Falha se operationId auto do baseline não tiver alias TV (onda estrita)",
    )
    args = parser.parse_args()

    if not args.baseline.is_file():
        print(f"Baseline ausente: {args.baseline}", file=sys.stderr)
        return 1

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    inventory = build_inventory(baseline)

    if args.write:
        args.inventory.parent.mkdir(parents=True, exist_ok=True)
        args.inventory.write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            f"Gravado {args.inventory} "
            f"(auto={inventory['autoCount']} stable={inventory['stableCount']})"
        )

    if args.report or (not args.write and not args.check and not args.check_aliases_coverage):
        print(
            f"ops={inventory['operationCount']} stable={inventory['stableCount']} "
            f"auto={inventory['autoCount']} collisions={len(inventory['recommendationCollisions'])}"
        )
        for tag, count in list(inventory["autoByTag"].items())[:12]:
            print(f"  {count:3d}  {tag}")

    if args.check:
        if not args.inventory.is_file():
            print(f"Inventário ausente: {args.inventory}", file=sys.stderr)
            return 1
        stored = json.loads(args.inventory.read_text(encoding="utf-8"))
        # Compara contagens e lista de auto operationIds (ignora ordem de campos extras).
        def fingerprint(payload: dict[str, Any]) -> list[str]:
            return sorted(
                str(row.get("operationId"))
                for row in (payload.get("operations") or [])
                if isinstance(row, dict) and not row.get("stable")
            )

        if fingerprint(stored) != fingerprint(inventory):
            print(
                "Drift no inventário de operationId auto — rode com --write.",
                file=sys.stderr,
            )
            return 1
        if stored.get("autoCount") != inventory["autoCount"]:
            print("Drift autoCount — rode com --write.", file=sys.stderr)
            return 1
        print(f"OK — inventário sincronizado (auto={inventory['autoCount']}).")

    if args.check_aliases_coverage:
        aliases = load_aliases()
        missing = [
            str(row.get("operationId"))
            for row in inventory["operations"]
            if isinstance(row, dict)
            and not row.get("stable")
            and str(row.get("operationId")) not in aliases
        ]
        if missing:
            print(
                f"Falha — {len(missing)} operationId auto sem alias TV:",
                file=sys.stderr,
            )
            for oid in missing[:40]:
                print(f"  - {oid}", file=sys.stderr)
            if len(missing) > 40:
                print(f"  … +{len(missing) - 40}", file=sys.stderr)
            return 1
        print(f"OK — todos os {inventory['autoCount']} auto-ids têm alias.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
