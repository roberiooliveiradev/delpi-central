#!/usr/bin/env python3
"""Gera catálogo TV (tv_data_routes.json) a partir do OpenAPI baseline api-delpi."""

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

# Enriquecimentos manuais preservados quando operationId coincide.
PRESERVE_KEYS = frozenset(
    {
        "valueFields",
        "seriesField",
        "defaultParams",
        "paramSchema",
        "tvConstraints",
        "metaShape",
        "allowedDisplayModes",
        "paramStrategy",
        "fixedQueryParams",
        "tableFields",
        "description",
        "label",
        "category",
    }
)

TAG_TO_CATEGORY: dict[str, str] = {
    "Agendamento": "scheduling",
    "Auditoria 5S": "quality",
    "Clientes": "commercial",
    "Comercial": "commercial",
    "Compras operacionais": "supplies",
    "Cultura DELPI": "strategic",
    "Dashboard": "system",
    "Engenharia": "engineering",
    "Financeiro": "financial",
    "Health": "system",
    "Inspeções de Entrada": "quality",
    "Kaizen — cadastro": "quality",
    "PAC Qualidade — inteligência": "quality",
    "PAC Qualidade — padrões de solução": "quality",
    "PAC Qualidade — planos de ação": "quality",
    "Pedidos de Venda em Aberto": "commercial",
    "Produção": "production",
    "Produção operacional": "production",
    "Propostas Comerciais": "commercial",
    "Qualidade": "quality",
    "Qualidade — PPM": "quality",
    "Quality Labels": "quality",
    "Quality Labels (público)": "quality",
    "Recursos Humanos": "hr",
    "Suprimentos": "supplies",
    "products": "products",
    "sales": "commercial",
    "system": "system",
}

PATH_SEGMENT_TO_CATEGORY: dict[str, str] = {
    "commercial": "commercial",
    "production": "production",
    "quality": "quality",
    "supplies": "supplies",
    "products": "products",
    "financial": "financial",
    "financeiro": "financial",
    "hr": "hr",
    "scheduling": "scheduling",
    "engineering": "engineering",
    "engenharia": "engineering",
    "strategic": "strategic",
    "system": "system",
    "dashboard": "system",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def format_operation_id_label(operation_id: str) -> str:
    text = re.sub(r"^(get|list|search)_", "", operation_id, flags=re.IGNORECASE)
    text = text.replace("_", " ").strip()
    return text[:1].upper() + text[1:] if text else operation_id


def resolve_category(operation: dict[str, Any]) -> str:
    tags = operation.get("tags") or []
    if isinstance(tags, list) and tags:
        tag = str(tags[0]).strip()
        if tag in TAG_TO_CATEGORY:
            return TAG_TO_CATEGORY[tag]
    path = str(operation.get("path") or "").strip()
    segment = path.strip("/").split("/")[0].lower() if path else ""
    return PATH_SEGMENT_TO_CATEGORY.get(segment, "other")


def infer_allowed_display_modes(operation: dict[str, Any]) -> list[str]:
    path = str(operation.get("path") or "").lower()
    operation_id = str(operation.get("operationId") or "").lower()
    haystack = f"{path} {operation_id}"
    if "series" in haystack or haystack.endswith("/series"):
        return ["line_chart", "auto"]
    if any(token in haystack for token in ("/search", "list_", "_list", "/items", "/proposals")):
        return ["table", "auto"]
    if "hierarchy" in haystack or "structure" in haystack:
        return ["table", "auto"]
    return ["kpi", "auto"]


def infer_meta_shape(operation: dict[str, Any]) -> str:
    path = str(operation.get("path") or "").lower()
    operation_id = str(operation.get("operationId") or "").lower()
    haystack = f"{path} {operation_id}"
    if any(token in haystack for token in ("/search", "list_", "_list", "/items", "/proposals")):
        return "paged_list"
    if "hierarchy" in haystack or "structure" in haystack:
        return "hierarchy"
    if "series" in haystack:
        return "scalar"
    return "scalar"


def build_base_route(operation: dict[str, Any]) -> dict[str, Any]:
    operation_id = str(operation.get("operationId") or "").strip()
    summary = str(operation.get("summary") or "").strip()
    description = str(operation.get("description") or "").strip()
    route: dict[str, Any] = {
        "operationId": operation_id,
        "httpMethod": "GET",
        "label": summary or format_operation_id_label(operation_id),
        "category": resolve_category(operation),
        "path": str(operation.get("path") or "").strip(),
        "allowedDisplayModes": infer_allowed_display_modes(operation),
        "metaShape": infer_meta_shape(operation),
    }
    if description:
        route["description"] = description
    return route


def merge_with_existing(base: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
    if not existing:
        return base
    merged = dict(base)
    for key, value in existing.items():
        if key in PRESERVE_KEYS and value not in (None, "", [], {}):
            merged[key] = value
    return merged


def load_openapi_get_operations(baseline_path: Path) -> list[dict[str, Any]]:
    payload = load_json(baseline_path)
    operations = payload.get("operations") or []
    if not isinstance(operations, list):
        return []
    result: list[dict[str, Any]] = []
    for item in operations:
        if not isinstance(item, dict):
            continue
        if str(item.get("method") or "").upper() != "GET":
            continue
        if item.get("deprecated"):
            continue
        operation_id = str(item.get("operationId") or "").strip()
        if operation_id:
            result.append(item)
    result.sort(key=lambda op: (str(op.get("path") or ""), str(op.get("operationId") or "")))
    return result


def load_existing_routes(routes_path: Path) -> dict[str, dict[str, Any]]:
    if not routes_path.is_file():
        return {}
    payload = load_json(routes_path)
    raw = payload.get("routes") or []
    indexed: dict[str, dict[str, Any]] = {}
    if not isinstance(raw, list):
        return indexed
    for item in raw:
        if isinstance(item, dict):
            op = str(item.get("operationId") or "").strip()
            if op:
                indexed[op] = dict(item)
    return indexed


def generate_routes(*, baseline_path: Path, routes_path: Path) -> list[dict[str, Any]]:
    existing = load_existing_routes(routes_path)
    generated: list[dict[str, Any]] = []
    for operation in load_openapi_get_operations(baseline_path):
        operation_id = str(operation.get("operationId") or "").strip()
        base = build_base_route(operation)
        generated.append(merge_with_existing(base, existing.get(operation_id)))
    return generated


def write_routes(routes_path: Path, routes: list[dict[str, Any]]) -> None:
    payload = {"routes": routes}
    routes_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=OPENAPI_BASELINE_PATH)
    parser.add_argument("--routes", type=Path, default=TV_ROUTES_PATH)
    parser.add_argument("--write", action="store_true", help="Grava tv_data_routes.json")
    parser.add_argument("--check", action="store_true", help="Falha se o catálogo divergir do gerador")
    args = parser.parse_args()

    if not args.baseline.is_file():
        print(f"OpenAPI baseline ausente: {args.baseline}", file=sys.stderr)
        return 1

    generated = generate_routes(baseline_path=args.baseline, routes_path=args.routes)

    if args.write:
        write_routes(args.routes, generated)
        print(f"Gravado {len(generated)} rotas em {args.routes}")
        return 0

    if args.check:
        if not args.routes.is_file():
            print(f"Catálogo TV ausente: {args.routes}", file=sys.stderr)
            return 1
        stored = load_json(args.routes).get("routes") or []
        if stored != generated:
            print(
                f"Drift detectado — stored={len(stored)} generated={len(generated)}. "
                "Rode com --write para sincronizar.",
                file=sys.stderr,
            )
            return 1
        print(f"OK — catálogo sincronizado ({len(generated)} rotas GET).")
        return 0

    print(json.dumps({"count": len(generated), "routes": generated[:3]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
