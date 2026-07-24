#!/usr/bin/env python3
"""Gera catálogo TV (tv_data_routes.json) a partir do OpenAPI baseline api-delpi.

Fonte de verdade (como o registry operacional do chat):
  api-delpi openapi → openapi_baseline.json (v3: parameters + xDelpi.locale/params/category)
  → generate --write → tv_data_routes.json
  → overlays em tv_data_route_overlays.json (TV-only)

Campos do OpenAPI (sempre regenerados / mergeados):
  operationId, path, httpMethod, paramSchema, paramStrategy (inferido),
  metaShape (x-delpi.shape quando houver),
  whenToUse/label/description de audiência (x-delpi.locale.pt-BR ou x-delpi.tv),
  category (x-delpi.category quando houver),
  labels de params (x-delpi.params.*.locale.pt-BR)

Overlays TV (preservados / arquivo overlays):
  valueFields, seriesField, tableFields, tvConstraints, fixedQueryParams,
  defaultParams, label, description, whenToUse, category, allowedDisplayModes,
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
        "valueFieldLabels",
        "valueFieldTypes",
        "seriesField",
        "defaultParams",
        "tvConstraints",
        "allowedDisplayModes",
        "paramStrategy",
        "fixedQueryParams",
        "tableFields",
        "description",
        "whenToUse",
        "label",
        "category",
        "paramSchema",  # merge profundo com schema OpenAPI
        "suggestedTransformSteps",
    }
)

TAG_TO_CATEGORY: dict[str, str] = {
    "Agendamento": "scheduling",
    "Auditoria 5S": "quality",
    "Clientes": "commercial",
    "Comercial": "commercial",
    "Commercial": "commercial",
    "Compras operacionais": "supplies",
    "Cultura DELPI": "strategic",
    "Dashboard": "system",
    "Engenharia": "engineering",
    "Engineering": "engineering",
    "Financeiro": "financial",
    "Financial": "financial",
    "Health": "system",
    "Inspeções de Entrada": "quality",
    "Kaizen — cadastro": "quality",
    "PAC Qualidade — inteligência": "quality",
    "PAC Qualidade — padrões de solução": "quality",
    "PAC Qualidade — planos de ação": "quality",
    "Pedidos de Venda em Aberto": "commercial",
    "Produção": "production",
    "Production": "production",
    "Produção operacional": "production",
    "Propostas Comerciais": "commercial",
    "Qualidade": "quality",
    "Quality": "quality",
    "Qualidade — PPM": "quality",
    "Quality Labels": "quality",
    "Quality Labels (público)": "quality",
    "Recursos Humanos": "hr",
    "Human Resources": "hr",
    "Suprimentos": "supplies",
    "Supplies": "supplies",
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


# Labels/hints: api-delpi/app/content/openapi_param_locale.json (única fonte).


def _load_param_locale_catalog() -> dict[str, dict[str, str]]:
    """name → {label, description} em pt-BR a partir do catálogo canônico."""
    catalog_path = ROOT / "api-delpi" / "app" / "content" / "openapi_param_locale.json"
    if not catalog_path.is_file():
        return {}
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    raw = payload.get("params") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, str]] = {}
    for name, value in raw.items():
        key = str(name or "").strip()
        if not key or not isinstance(value, dict):
            continue
        locale = value.get("locale") if isinstance(value.get("locale"), dict) else {}
        pt = locale.get("pt-BR") if isinstance(locale.get("pt-BR"), dict) else {}
        entry: dict[str, str] = {}
        label = str(pt.get("label") or "").strip()
        description = str(pt.get("description") or "").strip()
        if label:
            entry["label"] = label
        if description:
            entry["description"] = description
        if entry:
            out[key] = entry
    return out


_PARAM_LOCALE_PT = _load_param_locale_catalog()

# Fallback temporário (Onda 2/3): preferir enum/default do OpenAPI.
# Mantido vazio de propósito — inventário paralelo é falha de contrato.
KNOWN_PARAM_ENUMS: dict[str, list[Any]] = {}

# Defaults HTTP inventados no gerador — proibido. UX TV: tv_param_ux_defaults.json.
KNOWN_PARAM_DEFAULTS: dict[str, Any] = {}


def _load_tv_param_ux_defaults() -> dict[str, Any]:
    path = ROOT / "tv-dashboard-api" / "tv_app" / "content" / "tv_param_ux_defaults.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get("defaults") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {str(k): v for k, v in raw.items() if str(k).strip()}


_TV_PARAM_UX_DEFAULTS = _load_tv_param_ux_defaults()

_FALLBACK_PARAM_USAGE: set[str] = set()


def _note_param_fallback(kind: str, name: str) -> None:
    _FALLBACK_PARAM_USAGE.add(f"{kind}:{name}")


def enrich_param_schema_entry(
    name: str,
    entry: dict[str, Any],
    *,
    locale_label: str | None = None,
    locale_description: str | None = None,
    skip_ux_default: bool = False,
) -> dict[str, Any]:
    """Aplica label/hint/enum/default — OpenAPI + x-delpi + catálogo JSON; UX defaults TV-only."""
    enriched = dict(entry)
    catalog = _PARAM_LOCALE_PT.get(name) or {}
    if locale_label:
        enriched["label"] = locale_label
    elif catalog.get("label") and not enriched.get("label"):
        enriched["label"] = catalog["label"]
    elif catalog.get("label"):
        enriched["label"] = catalog["label"]

    if locale_description:
        enriched["description"] = locale_description
    else:
        hint = catalog.get("description") or str(enriched.get("description") or "").strip()
        if hint:
            enriched["description"] = hint

    if name in KNOWN_PARAM_ENUMS and not enriched.get("enum"):
        enriched["enum"] = list(KNOWN_PARAM_ENUMS[name])
        _note_param_fallback("enum", name)
    # Período em dias: input numérico livre — nunca enum/select.
    if name == "periodDays":
        enriched.pop("enum", None)
    if name in KNOWN_PARAM_DEFAULTS and enriched.get("default") is None:
        enriched["default"] = KNOWN_PARAM_DEFAULTS[name]
        enriched["optional"] = True
        _note_param_fallback("default", name)
    elif (
        not skip_ux_default
        and name in _TV_PARAM_UX_DEFAULTS
        and enriched.get("default") is None
    ):
        # Default só de UX TV — não inventa contrato HTTP.
        enriched["default"] = _TV_PARAM_UX_DEFAULTS[name]
        enriched["optional"] = True
    return enriched


def normalize_route_param_schema(route: dict[str, Any]) -> dict[str, Any]:
    """Reaplica enrich após merge (remove enums obsoletos herdados do catálogo)."""
    schema = route.get("paramSchema")
    if not isinstance(schema, dict) or not schema:
        return route
    competence_first = "competence" in schema
    updated = dict(route)
    updated["paramSchema"] = {
        key: enrich_param_schema_entry(
            key,
            value if isinstance(value, dict) else {},
            skip_ux_default=competence_first and key == "branch",
        )
        for key, value in schema.items()
    }
    return updated


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
    catalog_label = (_PARAM_LOCALE_PT.get(name) or {}).get("label")
    if catalog_label:
        return catalog_label
    desc = (description or "").strip()
    if desc and len(desc) <= 48:
        return desc
    return name.replace("_", " ").strip().capitalize() or name


def resolve_category(operation: dict[str, Any]) -> str:
    x_delpi = operation.get("xDelpi") if isinstance(operation.get("xDelpi"), dict) else {}
    category = str(x_delpi.get("category") or "").strip()
    if category:
        return category
    tags = operation.get("tags") or []
    if isinstance(tags, list) and tags:
        tag = str(tags[0]).strip()
        if tag in TAG_TO_CATEGORY:
            return TAG_TO_CATEGORY[tag]
    path = str(operation.get("path") or "").strip()
    segment = path.strip("/").split("/")[0].lower() if path else ""
    return PATH_SEGMENT_TO_CATEGORY.get(segment, "other")


def extract_param_locale_pt(operation: dict[str, Any], param_name: str) -> tuple[str | None, str | None]:
    """Retorna (label, description) de xDelpi.params.<name>.locale.pt-BR quando curados.

    Aceita legado flat `params.<name>.{en,pt-BR}` (sync SI antigo) além do canônico
    `params.<name>.locale.{en,pt-BR}`.
    """
    x_delpi = operation.get("xDelpi") if isinstance(operation.get("xDelpi"), dict) else {}
    params = x_delpi.get("params") if isinstance(x_delpi.get("params"), dict) else {}
    entry = params.get(param_name) if isinstance(params.get(param_name), dict) else {}
    locale = entry.get("locale") if isinstance(entry.get("locale"), dict) else {}
    pt = locale.get("pt-BR") if isinstance(locale.get("pt-BR"), dict) else {}
    if not pt:
        # Legado SI: params.<name>.pt-BR sem wrapper locale.
        pt = entry.get("pt-BR") if isinstance(entry.get("pt-BR"), dict) else {}
    label = str(pt.get("label") or "").strip() or None
    description = str(pt.get("description") or "").strip() or None
    return label, description


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


# Pares de período OpenAPI — ordem = preferência (date_start antes de start_date).
_DATE_RANGE_KEY_PAIRS: tuple[tuple[str, str], ...] = (
    ("date_start", "date_end"),
    ("start_date", "end_date"),
    ("date_from", "date_to"),
    ("dataInicio", "dataFim"),
    ("data_inicial", "data_final"),
    ("issue_date_start", "issue_date_end"),
    ("modified_from", "modified_to"),
)


def detect_openapi_date_range_keys(names: set[str]) -> tuple[str, str] | None:
    for start, end in _DATE_RANGE_KEY_PAIRS:
        if start in names and end in names:
            return start, end
    return None


def build_param_schema_from_openapi(
    parameters: list[dict[str, Any]] | None,
    operation: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str, tuple[str, str] | None]:
    """Converte parameters do baseline → paramSchema TV + paramStrategy + dateRangeKeys.

    Mantém as chaves de data canônicas no schema (UI de período relativo) e registra
    `dateRangeKeys` para o gateway emitir exatamente os nomes HTTP da api-delpi.
    Preferência: enum/default do OpenAPI; label/description de x-delpi.params.locale.pt-BR.

    Rotas com `competence` (SI / IGD): strategy `direct` — não inventa periodDays nem
    trata o par de datas como date_range TV (competência é o eixo principal).
    """
    params = [p for p in (parameters or []) if isinstance(p, dict) and p.get("name")]
    names = {str(p["name"]) for p in params}
    competence_first = "competence" in names
    date_range_keys = None if competence_first else detect_openapi_date_range_keys(names)
    strategy = "date_range" if date_range_keys else "direct"
    schema: dict[str, Any] = {}
    op = operation if isinstance(operation, dict) else {}

    for param in params:
        name = str(param["name"])
        locale_label, locale_description = extract_param_locale_pt(op, name)
        entry: dict[str, Any] = {
            "type": map_openapi_type(param),
            "optional": not bool(param.get("required")),
            "label": locale_label or humanize_param_label(name, param.get("description")),
        }
        if param.get("default") is not None:
            entry["default"] = param["default"]
        if isinstance(param.get("enum"), list) and param["enum"]:
            entry["enum"] = list(param["enum"])
        fmt = str(param.get("format") or "").strip()
        if fmt:
            entry["format"] = fmt
        openapi_desc = str(param.get("description") or "").strip()
        if locale_description:
            entry["description"] = locale_description
        elif openapi_desc:
            entry["description"] = openapi_desc
        # SI: filial opcional sem default UX «01» (omitir = consolidado).
        skip_ux_default = competence_first and name == "branch"
        schema[name] = enrich_param_schema_entry(
            name,
            entry,
            locale_label=locale_label,
            locale_description=locale_description,
            skip_ux_default=skip_ux_default,
        )

    return schema, strategy, date_range_keys


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


def extract_tv_audience(operation: dict[str, Any]) -> dict[str, Any]:
    """Campos de audiência TV a partir de x-delpi.locale.pt-BR (preferido) ou x-delpi.tv."""
    x_delpi = operation.get("xDelpi") if isinstance(operation.get("xDelpi"), dict) else {}
    locale = x_delpi.get("locale") if isinstance(x_delpi.get("locale"), dict) else {}
    pt = locale.get("pt-BR") if isinstance(locale.get("pt-BR"), dict) else {}
    tv = x_delpi.get("tv") if isinstance(x_delpi.get("tv"), dict) else {}
    audience: dict[str, Any] = {}
    when_to_use = str(pt.get("whenToUse") or tv.get("whenToUse") or "").strip()
    if when_to_use:
        audience["whenToUse"] = when_to_use
    label = str(pt.get("label") or pt.get("summary") or tv.get("label") or "").strip()
    if label:
        audience["label"] = label
    description = str(pt.get("description") or tv.get("description") or "").strip()
    if description:
        audience["description"] = description
    return audience


def build_base_route(operation: dict[str, Any]) -> dict[str, Any]:
    operation_id = str(operation.get("operationId") or "").strip()
    summary = str(operation.get("summary") or "").strip()
    description = str(operation.get("description") or "").strip()
    param_schema, param_strategy, date_range_keys = build_param_schema_from_openapi(
        operation.get("parameters"),
        operation,
    )
    tv_audience = extract_tv_audience(operation)
    route: dict[str, Any] = {
        "operationId": operation_id,
        "httpMethod": "GET",
        "label": tv_audience.get("label") or summary or format_operation_id_label(operation_id),
        "category": resolve_category(operation),
        "path": str(operation.get("path") or "").strip(),
        "allowedDisplayModes": infer_allowed_display_modes(operation),
        "metaShape": infer_meta_shape(operation),
    }
    route_description = tv_audience.get("description") or description
    if route_description:
        route["description"] = route_description
    if tv_audience.get("whenToUse"):
        route["whenToUse"] = tv_audience["whenToUse"]
    if param_schema:
        route["paramSchema"] = param_schema
        route["paramStrategy"] = param_strategy
        if date_range_keys:
            route["dateRangeKeys"] = list(date_range_keys)
            route["defaultParams"] = {"periodDays": 30}
        elif param_strategy == "date_range":
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
    """Preserva curadoria TV-only do catálogo; OpenAPI/locale vence em label/description/whenToUse/category."""
    if not existing:
        return base
    merged = dict(base)
    openapi_wins = frozenset({"label", "description", "whenToUse", "category"})
    for key in OVERLAY_KEYS:
        if key == "paramSchema":
            continue
        if key in openapi_wins and merged.get(key):
            continue
        value = existing.get(key)
        if value not in (None, "", [], {}):
            if key == "defaultParams" and isinstance(value, dict):
                merged["defaultParams"] = {**(merged.get("defaultParams") or {}), **value}
            else:
                merged[key] = value
    # OpenAPI direct (ex.: SI competence-first): não herdar date_range / periodDays do catálogo antigo.
    if merged.get("paramStrategy") == "direct":
        merged.pop("dateRangeKeys", None)
        defaults = merged.get("defaultParams")
        if isinstance(defaults, dict) and "periodDays" in defaults:
            cleaned = {k: v for k, v in defaults.items() if k != "periodDays"}
            if cleaned:
                merged["defaultParams"] = cleaned
            else:
                merged.pop("defaultParams", None)
    existing_schema = existing.get("paramSchema")
    if isinstance(existing_schema, dict) and existing_schema:
        # OpenAPI vence em contrato (optional/type/enum/default); existing só preenche
        # buracos e labels extras. Sem isso, sync live congela optional:false antigo
        # enquanto description/whenToUse já vêm do OpenAPI (ex.: filial consolidada).
        openapi_schema = merged.get("paramSchema") if isinstance(merged.get("paramSchema"), dict) else {}
        patched_existing: dict[str, Any] = {}
        for key, value in existing_schema.items():
            if not isinstance(value, dict):
                patched_existing[key] = value
                continue
            entry = dict(value)
            openapi_entry = openapi_schema.get(key) if isinstance(openapi_schema.get(key), dict) else {}
            # paramSchema TV usa só `optional`; `required` residual do baseline não deve
            # vencer no MFE (isParamFieldOptional prioriza required).
            entry.pop("required", None)
            if "optional" in openapi_entry:
                entry["optional"] = bool(openapi_entry["optional"])
            if openapi_entry.get("type"):
                entry["type"] = openapi_entry["type"]
            if openapi_entry.get("enum"):
                entry["enum"] = list(openapi_entry["enum"])
            if "default" in openapi_entry:
                entry["default"] = openapi_entry["default"]
            elif openapi_entry.get("optional") is True:
                # OpenAPI opcional sem default — não reintroduzir UX antigo do catálogo
                # (ex.: filial SI consolidada vs default «01» herdado).
                entry.pop("default", None)
            patched_existing[key] = entry
        merged["paramSchema"] = merge_param_schema(openapi_schema, patched_existing)
    return merged


_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})


def _schema_type_and_meta(schema: dict[str, Any]) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    candidates: list[dict[str, Any]] = [schema]
    any_of = schema.get("anyOf") or schema.get("oneOf")
    if isinstance(any_of, list):
        for item in any_of:
            if isinstance(item, dict) and item.get("type") != "null":
                candidates.append(item)
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        type_name = str(candidate.get("type") or "").strip()
        if type_name and type_name != "null" and "type" not in meta:
            meta["type"] = type_name
        if "default" in candidate and candidate.get("default") is not None and "default" not in meta:
            meta["default"] = candidate["default"]
        enum = candidate.get("enum")
        if isinstance(enum, list) and enum and "enum" not in meta:
            meta["enum"] = [str(item) for item in enum]
        format_name = str(candidate.get("format") or "").strip()
        if format_name and "format" not in meta:
            meta["format"] = format_name
    if "default" in schema and schema.get("default") is not None and "default" not in meta:
        meta["default"] = schema["default"]
    return meta


def _simplify_openapi_parameter(param: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(param, dict):
        return None
    if str(param.get("in") or "").lower() != "query":
        return None
    name = str(param.get("name") or "").strip()
    if not name:
        return None
    schema = param.get("schema") if isinstance(param.get("schema"), dict) else {}
    entry: dict[str, Any] = {
        "name": name,
        "required": bool(param.get("required")),
    }
    description = str(param.get("description") or schema.get("description") or "").strip()
    if description:
        entry["description"] = description
    entry.update(_schema_type_and_meta(schema))
    return entry


def _clean_locale_map(raw: Any) -> dict[str, dict[str, str]] | None:
    if not isinstance(raw, dict):
        return None
    out: dict[str, dict[str, str]] = {}
    for lang, block in raw.items():
        lang_key = str(lang or "").strip()
        if not lang_key or not isinstance(block, dict):
            continue
        cleaned: dict[str, str] = {}
        for field in ("summary", "description", "whenToUse", "label"):
            value = str(block.get(field) or "").strip()
            if value:
                cleaned[field] = value
        if cleaned:
            out[lang_key] = cleaned
    return out or None


def _extract_x_delpi(operation: dict[str, Any]) -> dict[str, Any] | None:
    raw = operation.get("x-delpi")
    if not isinstance(raw, dict):
        return None
    out: dict[str, Any] = {}
    entity = raw.get("entity")
    shape = raw.get("shape")
    if entity is not None:
        out["entity"] = str(entity)
    if shape is not None:
        out["shape"] = str(shape)
    presentation = raw.get("presentation")
    if isinstance(presentation, dict) and presentation.get("strategy") is not None:
        out["presentationStrategy"] = str(presentation.get("strategy"))
    category = str(raw.get("category") or "").strip()
    if category:
        out["category"] = category
    locale = _clean_locale_map(raw.get("locale"))
    if locale:
        out["locale"] = locale
    params_raw = raw.get("params")
    if isinstance(params_raw, dict) and params_raw:
        params_out: dict[str, Any] = {}
        for name, value in params_raw.items():
            key = str(name or "").strip()
            if not key or not isinstance(value, dict):
                continue
            param_locale = _clean_locale_map(value.get("locale"))
            if param_locale:
                params_out[key] = {"locale": param_locale}
        if params_out:
            out["params"] = params_out
    tv = raw.get("tv")
    if isinstance(tv, dict) and tv:
        tv_clean: dict[str, str] = {}
        for field in ("whenToUse", "description", "label"):
            value = str(tv.get(field) or "").strip()
            if value:
                tv_clean[field] = value
        if tv_clean:
            out["tv"] = tv_clean
    return out or None


def build_baseline_payload_from_openapi(spec: dict[str, Any]) -> dict[str, Any]:
    """Converte OpenAPI completo → baseline v3 (sem depender de app.domain api-delpi).

    O OpenAPI live da api-delpi já traz `x-delpi` (locale/params) via injector.
    """
    operations: list[dict[str, Any]] = []
    for path, methods in (spec.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            row: dict[str, Any] = {
                "method": method.upper(),
                "path": path,
                "operationId": operation.get("operationId"),
                "summary": operation.get("summary"),
                "tags": operation.get("tags") or [],
                "deprecated": bool(operation.get("deprecated")),
            }
            parameters: list[dict[str, Any]] = []
            for raw_param in operation.get("parameters") or []:
                simplified = _simplify_openapi_parameter(raw_param)
                if simplified:
                    parameters.append(simplified)
            if parameters:
                row["parameters"] = parameters
            x_delpi = _extract_x_delpi(operation)
            if x_delpi:
                row["xDelpi"] = x_delpi
            description = str(operation.get("description") or "").strip()
            if description:
                row["description"] = description
            operations.append(row)
    operations.sort(key=lambda row: (str(row.get("path") or ""), str(row.get("method") or "")))
    info = spec.get("info") or {}
    return {
        "version": "3",
        "api_title": info.get("title"),
        "api_version": info.get("version"),
        "openapi_version": spec.get("openapi"),
        "operation_count": len(operations),
        "operations": operations,
    }


def load_openapi_get_operations(baseline_path: Path) -> list[dict[str, Any]]:
    payload = load_json(baseline_path)
    # Aceita baseline {operations:[…]} ou OpenAPI completo {paths:{…}}.
    if isinstance(payload.get("paths"), dict) and "operations" not in payload:
        payload = build_baseline_payload_from_openapi(payload)
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


def load_overlay_prefixes(overlays_path: Path) -> dict[str, dict[str, Any]]:
    if not overlays_path.is_file():
        return {}
    payload = load_json(overlays_path)
    raw = payload.get("overlayPrefixes") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): dict(value)
        for key, value in raw.items()
        if isinstance(value, dict) and str(key).strip()
    }


def resolve_overlay(
    operation_id: str,
    *,
    overlays: dict[str, dict[str, Any]],
    prefixes: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    exact = overlays.get(operation_id)
    prefix_match: dict[str, Any] | None = None
    # Prefixo mais longo vence (ex.: get_si_indicator_quality_ vs get_si_indicator_).
    for prefix, overlay in sorted(prefixes.items(), key=lambda item: len(item[0]), reverse=True):
        if operation_id.startswith(prefix):
            prefix_match = overlay
            break
    if exact and prefix_match:
        merged = dict(prefix_match)
        merged.update(exact)
        return merged
    return exact or prefix_match


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
            "whenToUse",
            "valueFieldLabels",
            "valueFieldTypes",
            "suggestedTransformSteps",
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
    overlays_file = overlays_path or TV_OVERLAYS_PATH
    overlays = load_overlays(overlays_file)
    prefixes = load_overlay_prefixes(overlays_file)
    generated: list[dict[str, Any]] = []
    for operation in load_openapi_get_operations(baseline_path):
        operation_id = str(operation.get("operationId") or "").strip()
        base = build_base_route(operation)
        with_existing = merge_with_existing(base, existing.get(operation_id))
        with_overlay = apply_overlay(
            with_existing,
            resolve_overlay(operation_id, overlays=overlays, prefixes=prefixes),
        )
        normalized = normalize_route_param_schema(with_overlay)
        generated.append(strip_fixed_params_from_schema(normalized))
    return generated


def write_routes(routes_path: Path, routes: list[dict[str, Any]]) -> None:
    payload = {"routes": routes}
    routes_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=OPENAPI_BASELINE_PATH)
    parser.add_argument(
        "--from-openapi",
        type=Path,
        default=None,
        help="OpenAPI completo (openapi.json) — converte para baseline em memória / --baseline-out",
    )
    parser.add_argument(
        "--baseline-out",
        type=Path,
        default=None,
        help="Com --from-openapi: grava o baseline derivado neste path",
    )
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

    baseline_path = args.baseline
    if args.from_openapi is not None:
        if not args.from_openapi.is_file():
            print(f"OpenAPI ausente: {args.from_openapi}", file=sys.stderr)
            return 1
        spec = load_json(args.from_openapi)
        payload = build_baseline_payload_from_openapi(spec)
        if args.baseline_out is not None:
            args.baseline_out.parent.mkdir(parents=True, exist_ok=True)
            args.baseline_out.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            baseline_path = args.baseline_out
            print(f"Baseline derivado: {baseline_path} ({payload.get('operation_count')} ops)")
        else:
            import tempfile

            tmp = Path(tempfile.mkstemp(prefix="tv_openapi_baseline_", suffix=".json")[1])
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            baseline_path = tmp
            print(f"Baseline temporário: {baseline_path} ({payload.get('operation_count')} ops)")

    if not baseline_path.is_file():
        print(f"OpenAPI baseline ausente: {baseline_path}", file=sys.stderr)
        return 1

    if args.seed_overlays:
        overlays = seed_overlays_from_catalog(
            baseline_path=baseline_path,
            routes_path=args.routes,
            overlays_path=args.overlays,
        )
        print(f"Gravados {len(overlays)} overlays em {args.overlays}")
        if not args.write and not args.check:
            return 0

    generated = generate_routes(
        baseline_path=baseline_path,
        routes_path=args.routes,
        overlays_path=args.overlays,
    )

    if args.write:
        write_routes(args.routes, generated)
        with_schema = sum(1 for item in generated if item.get("paramSchema"))
        with_values = sum(1 for item in generated if item.get("valueFields"))
        if _FALLBACK_PARAM_USAGE:
            print(
                f"WARN — {len(_FALLBACK_PARAM_USAGE)} fallbacks de enum/default TV "
                f"(declarar no OpenAPI Query quando possível): "
                f"{', '.join(sorted(_FALLBACK_PARAM_USAGE))}"
            )
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
