#!/usr/bin/env python3
"""Gera catálogo TV (tv_data_routes.json) a partir do OpenAPI baseline api-delpi.

Fonte de verdade (como o registry operacional do chat):
  api-delpi openapi → openapi_baseline.json (v2: parameters + xDelpi)
  → generate --write → tv_data_routes.json
  → overlays em tv_data_route_overlays.json (TV-only)

Campos do OpenAPI (sempre regenerados / mergeados):
  operationId, path, httpMethod, paramSchema, paramStrategy (inferido),
  metaShape (x-delpi.shape quando houver)

Overlays TV (preservados / arquivo overlays):
  valueFields, seriesField, tableFields, tvConstraints, fixedQueryParams,
  defaultParams, label, description, category, allowedDisplayModes,
  paramStrategy (se explícito), ajustes pontuais de paramSchema
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
TV_OVERLAYS_PATH = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_data_route_overlays.json"

# Overlay / preservação manual (não vêm do OpenAPI puro).
OVERLAY_KEYS = frozenset(
    {
        "valueFields",
        "seriesField",
        "defaultParams",
        "tvConstraints",
        "allowedDisplayModes",
        "paramStrategy",
        "fixedQueryParams",
        "tableFields",
        "description",
        "label",
        "category",
        "paramSchema",  # merge profundo com schema OpenAPI
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

PARAM_LABELS_PT: dict[str, str] = {
    "branch": "Filial",
    "periodDays": "Período (dias)",
    "start_date": "Data início",
    "end_date": "Data fim",
    "customer_segment": "Segmento (weg | new_business)",
    "granularity": "Granularidade",
    "limit": "Limite",
    "offset": "Offset",
    "page": "Página",
    "page_size": "Tamanho da página",
    "code": "Código",
    "product_code": "Código do produto",
}

# Explicações curtas no inspetor (DeckField hint) — complementam o OpenAPI.
PARAM_HINTS_PT: dict[str, str] = {
    "branch": "Código da filial no Protheus (ex.: 01 ou 02). Vazio usa o consolidado da rota, quando permitido.",
    "periodDays": "Quantos dias para trás entram no cálculo (ex.: 30 = último mês até hoje).",
    "granularity": "Como agrupar os pontos da série: day (dia), week (semana), month (mês) ou year (ano).",
    "customer_segment": "Filtra clientes: weg ou new_business. Vazio = todos os segmentos.",
    "start_date": "Início do intervalo (AAAA-MM-DD). Em rotas com Período (dias), o sistema calcula automaticamente.",
    "end_date": "Fim do intervalo (AAAA-MM-DD). Em rotas com Período (dias), o sistema calcula automaticamente.",
    "page": "Número da página na listagem paginada.",
    "page_size": "Quantidade de linhas por página.",
    "limit": "Máximo de registros retornados pela API.",
}

KNOWN_PARAM_ENUMS: dict[str, list[Any]] = {
    "granularity": ["day", "week", "month", "year"],
    "customer_segment": ["weg", "new_business"],
    "loss_type": ["refugo", "scrap", "both"],
    "product_type": ["PA", "PI"],
    "sort_dir": ["asc", "desc"],
    "direction": ["asc", "desc"],
    "orderDir": ["asc", "desc"],
    "linked_sort_dir": ["asc", "desc"],
    "stock_method": ["auto", "hybrid", "estimated", "official_closure"],
    "periodDays": [7, 14, 30, 60, 90, 180, 365],
}

KNOWN_PARAM_DEFAULTS: dict[str, Any] = {
    "granularity": "day",
}


def enrich_param_schema_entry(name: str, entry: dict[str, Any]) -> dict[str, Any]:
    """Aplica label, hint, enum e default canônicos TV sobre o campo OpenAPI."""
    enriched = dict(entry)
    if name in PARAM_LABELS_PT:
        enriched["label"] = PARAM_LABELS_PT[name]
    hint = PARAM_HINTS_PT.get(name) or str(enriched.get("description") or "").strip()
    if hint:
        enriched["description"] = hint
    if name in KNOWN_PARAM_ENUMS and not enriched.get("enum"):
        enriched["enum"] = list(KNOWN_PARAM_ENUMS[name])
    if name in KNOWN_PARAM_DEFAULTS and enriched.get("default") is None:
        enriched["default"] = KNOWN_PARAM_DEFAULTS[name]
        # Com default TV, não bloquear preview se o campo vier vazio na UI.
        enriched["optional"] = True
    return enriched


def strip_fixed_params_from_schema(route: dict[str, Any]) -> dict[str, Any]:
    """Remove do inspetor parâmetros já fixados no catálogo (ex.: granularity=day)."""
    fixed = route.get("fixedQueryParams")
    schema = route.get("paramSchema")
    if not isinstance(fixed, dict) or not isinstance(schema, dict):
        return route
    next_schema = {key: value for key, value in schema.items() if key not in fixed}
    updated = dict(route)
    if next_schema:
        updated["paramSchema"] = next_schema
    else:
        updated.pop("paramSchema", None)
    return updated


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def format_operation_id_label(operation_id: str) -> str:
    text = re.sub(r"^(get|list|search)_", "", operation_id, flags=re.IGNORECASE)
    text = text.replace("_", " ").strip()
    return text[:1].upper() + text[1:] if text else operation_id


def humanize_param_label(name: str, description: str | None = None) -> str:
    if name in PARAM_LABELS_PT:
        return PARAM_LABELS_PT[name]
    desc = (description or "").strip()
    if desc and len(desc) <= 48:
        return desc
    return name.replace("_", " ").strip().capitalize() or name


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
    x_delpi = operation.get("xDelpi") if isinstance(operation.get("xDelpi"), dict) else {}
    shape = str(x_delpi.get("shape") or "").strip()
    if shape:
        return shape
    path = str(operation.get("path") or "").lower()
    operation_id = str(operation.get("operationId") or "").lower()
    haystack = f"{path} {operation_id}"
    if any(token in haystack for token in ("/search", "list_", "_list", "/items", "/proposals")):
        return "paged_list"
    if "hierarchy" in haystack or "structure" in haystack:
        return "hierarchy"
    return "scalar"


def map_openapi_type(param: dict[str, Any]) -> str:
    type_name = str(param.get("type") or "").strip().lower()
    if type_name in {"integer", "int", "number"}:
        return "integer" if type_name != "number" else "number"
    if type_name == "boolean":
        return "boolean"
    return "string"


def build_param_schema_from_openapi(
    parameters: list[dict[str, Any]] | None,
) -> tuple[dict[str, Any], str]:
    """Converte parameters do baseline → paramSchema TV + paramStrategy."""
    params = [p for p in (parameters or []) if isinstance(p, dict) and p.get("name")]
    names = {str(p["name"]) for p in params}
    has_date_range = "start_date" in names and "end_date" in names
    strategy = "date_range" if has_date_range else "direct"
    schema: dict[str, Any] = {}

    if has_date_range:
        schema["periodDays"] = enrich_param_schema_entry(
            "periodDays",
            {
                "type": "integer",
                "default": 30,
                "label": PARAM_LABELS_PT["periodDays"],
                "optional": True,
            },
        )

    for param in params:
        name = str(param["name"])
        if has_date_range and name in {"start_date", "end_date"}:
            continue
        entry: dict[str, Any] = {
            "type": map_openapi_type(param),
            "optional": not bool(param.get("required")),
            "label": humanize_param_label(name, param.get("description")),
        }
        if param.get("default") is not None:
            entry["default"] = param["default"]
        if isinstance(param.get("enum"), list) and param["enum"]:
            entry["enum"] = list(param["enum"])
        openapi_desc = str(param.get("description") or "").strip()
        if openapi_desc:
            entry["description"] = openapi_desc
        schema[name] = enrich_param_schema_entry(name, entry)

    return schema, strategy


def infer_value_fields(operation_id: str) -> list[str]:
    """Heurística leve: operationId com _pct → campo homônimo + value."""
    oid = operation_id.strip()
    if "_pct" not in oid.lower():
        return []
    field = re.sub(r"^(get|list|search)_", "", oid, flags=re.IGNORECASE)
    if not field:
        return []
    return [field, "value"]


def merge_param_schema(
    openapi_schema: dict[str, Any],
    *overlays: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = {key: dict(value) if isinstance(value, dict) else value for key, value in openapi_schema.items()}
    for overlay in overlays:
        if not overlay:
            continue
        for key, value in overlay.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
    return merged


def build_base_route(operation: dict[str, Any]) -> dict[str, Any]:
    operation_id = str(operation.get("operationId") or "").strip()
    summary = str(operation.get("summary") or "").strip()
    description = str(operation.get("description") or "").strip()
    param_schema, param_strategy = build_param_schema_from_openapi(operation.get("parameters"))
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
    if param_schema:
        route["paramSchema"] = param_schema
        route["paramStrategy"] = param_strategy
        if param_strategy == "date_range":
            route["defaultParams"] = {"periodDays": 30}
    value_fields = infer_value_fields(operation_id)
    if value_fields:
        route["valueFields"] = value_fields
    return route


def apply_overlay(base: dict[str, Any], overlay: dict[str, Any] | None) -> dict[str, Any]:
    if not overlay:
        return base
    merged = dict(base)
    for key, value in overlay.items():
        if key not in OVERLAY_KEYS or value in (None, "", [], {}):
            continue
        if key == "paramSchema" and isinstance(value, dict):
            merged["paramSchema"] = merge_param_schema(merged.get("paramSchema") or {}, value)
        elif key == "defaultParams" and isinstance(value, dict):
            merged["defaultParams"] = {**(merged.get("defaultParams") or {}), **value}
        else:
            merged[key] = value
    return merged


def merge_with_existing(base: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
    """Preserva curadoria do catálogo atual (labels PT, valueFields manuais, etc.)."""
    if not existing:
        return base
    merged = dict(base)
    for key in OVERLAY_KEYS:
        if key == "paramSchema":
            continue
        value = existing.get(key)
        if value not in (None, "", [], {}):
            if key == "defaultParams" and isinstance(value, dict):
                merged["defaultParams"] = {**(merged.get("defaultParams") or {}), **value}
            else:
                merged[key] = value
    existing_schema = existing.get("paramSchema")
    if isinstance(existing_schema, dict) and existing_schema:
        merged["paramSchema"] = merge_param_schema(merged.get("paramSchema") or {}, existing_schema)
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


def load_overlays(overlays_path: Path) -> dict[str, dict[str, Any]]:
    if not overlays_path.is_file():
        return {}
    payload = load_json(overlays_path)
    raw = payload.get("overlays") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): dict(value)
        for key, value in raw.items()
        if isinstance(value, dict) and str(key).strip()
    }


def extract_overlay_from_route(route: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    """Extrai só o que difere do base OpenAPI (para seed de overlays)."""
    overlay: dict[str, Any] = {}
    for key in OVERLAY_KEYS:
        if key == "paramSchema":
            continue
        value = route.get(key)
        if value in (None, "", [], {}):
            continue
        if value != base.get(key):
            overlay[key] = value
    route_schema = route.get("paramSchema") if isinstance(route.get("paramSchema"), dict) else {}
    base_schema = base.get("paramSchema") if isinstance(base.get("paramSchema"), dict) else {}
    schema_diff: dict[str, Any] = {}
    for key, value in route_schema.items():
        if key not in base_schema or base_schema.get(key) != value:
            schema_diff[key] = value
    if schema_diff:
        overlay["paramSchema"] = schema_diff
    return overlay


def seed_overlays_from_catalog(
    *,
    baseline_path: Path,
    routes_path: Path,
    overlays_path: Path,
) -> dict[str, dict[str, Any]]:
    existing = load_existing_routes(routes_path)
    overlays: dict[str, dict[str, Any]] = {}
    for operation in load_openapi_get_operations(baseline_path):
        operation_id = str(operation.get("operationId") or "").strip()
        base = build_base_route(operation)
        route = existing.get(operation_id)
        if not route:
            continue
        overlay = extract_overlay_from_route(route, base)
        # Só persiste overlays com conteúdo TV-relevante (não só label/description genéricos).
        tv_keys = {
            "valueFields",
            "seriesField",
            "tableFields",
            "tvConstraints",
            "fixedQueryParams",
            "paramStrategy",
            "defaultParams",
            "paramSchema",
        }
        if any(key in overlay for key in tv_keys):
            # Mantém label/description/category se já curados junto.
            overlays[operation_id] = overlay
    payload = {
        "version": 1,
        "description": (
            "Overlays TV por operationId — valueFields, tvConstraints, paramStrategy, "
            "labels curados. Mergeados sobre o schema gerado do OpenAPI."
        ),
        "overlays": dict(sorted(overlays.items())),
    }
    overlays_path.parent.mkdir(parents=True, exist_ok=True)
    overlays_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return overlays


def generate_routes(
    *,
    baseline_path: Path,
    routes_path: Path,
    overlays_path: Path | None = None,
) -> list[dict[str, Any]]:
    existing = load_existing_routes(routes_path)
    overlays = load_overlays(overlays_path or TV_OVERLAYS_PATH)
    generated: list[dict[str, Any]] = []
    for operation in load_openapi_get_operations(baseline_path):
        operation_id = str(operation.get("operationId") or "").strip()
        base = build_base_route(operation)
        with_existing = merge_with_existing(base, existing.get(operation_id))
        with_overlay = apply_overlay(with_existing, overlays.get(operation_id))
        generated.append(strip_fixed_params_from_schema(with_overlay))
    return generated


def write_routes(routes_path: Path, routes: list[dict[str, Any]]) -> None:
    payload = {"routes": routes}
    routes_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=OPENAPI_BASELINE_PATH)
    parser.add_argument("--routes", type=Path, default=TV_ROUTES_PATH)
    parser.add_argument("--overlays", type=Path, default=TV_OVERLAYS_PATH)
    parser.add_argument("--write", action="store_true", help="Grava tv_data_routes.json")
    parser.add_argument("--check", action="store_true", help="Falha se o catálogo divergir do gerador")
    parser.add_argument(
        "--seed-overlays",
        action="store_true",
        help="Extrai overlays TV do catálogo atual para tv_data_route_overlays.json",
    )
    args = parser.parse_args()

    if not args.baseline.is_file():
        print(f"OpenAPI baseline ausente: {args.baseline}", file=sys.stderr)
        return 1

    if args.seed_overlays:
        overlays = seed_overlays_from_catalog(
            baseline_path=args.baseline,
            routes_path=args.routes,
            overlays_path=args.overlays,
        )
        print(f"Gravados {len(overlays)} overlays em {args.overlays}")
        if not args.write and not args.check:
            return 0

    generated = generate_routes(
        baseline_path=args.baseline,
        routes_path=args.routes,
        overlays_path=args.overlays,
    )

    if args.write:
        write_routes(args.routes, generated)
        with_schema = sum(1 for item in generated if item.get("paramSchema"))
        with_values = sum(1 for item in generated if item.get("valueFields"))
        print(
            f"Gravado {len(generated)} rotas em {args.routes} "
            f"(paramSchema={with_schema}, valueFields={with_values})"
        )
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
