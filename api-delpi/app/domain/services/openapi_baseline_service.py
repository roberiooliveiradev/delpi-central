"""Baseline OpenAPI versionado para diff de contrato e catálogo TV (Fase 4 + Playbook 22)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_BASELINE_PATH = Path(__file__).resolve().parents[2] / "content" / "openapi_baseline.json"

_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})

# Versão 3: parameters + x-delpi com locale EN/pt-BR, params.locale e category.
BASELINE_VERSION = "3"


def _operation_key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def _schema_type_and_meta(schema: dict[str, Any]) -> dict[str, Any]:
    """Extrai type/default/enum/format de schema OpenAPI (inclui anyOf com null)."""
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


def simplify_openapi_parameter(param: dict[str, Any]) -> dict[str, Any] | None:
    """Normaliza parameter OpenAPI → entrada enxuta do baseline (só query)."""
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


def extract_x_delpi(operation: dict[str, Any]) -> dict[str, Any] | None:
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


def merge_audience_into_x_delpi(
    x_delpi: dict[str, Any] | None,
    operation_id: str | None,
) -> dict[str, Any] | None:
    """Garante locale/params/category do JSON curado também no baseline (sem depender só do runtime)."""
    from app.domain.services.route_locale_catalog_service import apply_route_locale_to_x_delpi

    base = dict(x_delpi or {})
    if not operation_id:
        return base or None
    # apply espera o formato x-delpi (presentation aninhada); baseline usa presentationStrategy.
    runtime_shape = dict(base)
    if "presentationStrategy" in runtime_shape and "presentation" not in runtime_shape:
        runtime_shape["presentation"] = {"strategy": runtime_shape.pop("presentationStrategy")}
    merged = apply_route_locale_to_x_delpi(runtime_shape, str(operation_id))
    # Re-flatten para formato baseline.
    strategy = None
    presentation = merged.get("presentation")
    if isinstance(presentation, dict):
        strategy = presentation.get("strategy")
        merged = {k: v for k, v in merged.items() if k != "presentation"}
    if strategy is not None:
        merged["presentationStrategy"] = str(strategy)
    return merged or None


def extract_operations_from_openapi(spec: dict[str, Any]) -> list[dict[str, Any]]:
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
                simplified = simplify_openapi_parameter(raw_param)
                if simplified:
                    parameters.append(simplified)
            if parameters:
                row["parameters"] = parameters
            x_delpi = merge_audience_into_x_delpi(
                extract_x_delpi(operation),
                operation.get("operationId"),
            )
            if x_delpi:
                row["xDelpi"] = x_delpi
            description = str(operation.get("description") or "").strip()
            if description:
                row["description"] = description
            operations.append(row)

    operations.sort(key=lambda row: (row["path"], row["method"]))
    return operations


def enrich_baseline_payload_locale(payload: dict[str, Any]) -> dict[str, Any]:
    """Atualiza xDelpi.locale/params/category de um baseline já existente (sem reabrir FastAPI)."""
    ops = payload.get("operations")
    if not isinstance(ops, list):
        return payload
    enriched_ops: list[dict[str, Any]] = []
    for row in ops:
        if not isinstance(row, dict):
            continue
        next_row = dict(row)
        x_delpi = next_row.get("xDelpi") if isinstance(next_row.get("xDelpi"), dict) else {}
        merged = merge_audience_into_x_delpi(x_delpi, next_row.get("operationId"))
        if merged:
            next_row["xDelpi"] = merged
        enriched_ops.append(next_row)
    return {
        **payload,
        "version": BASELINE_VERSION,
        "operation_count": len(enriched_ops),
        "operations": enriched_ops,
    }


def enrich_saved_openapi_baseline() -> Path:
    payload = enrich_baseline_payload_locale(load_openapi_baseline())
    _BASELINE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return _BASELINE_PATH


def build_baseline_payload(spec: dict[str, Any]) -> dict[str, Any]:
    info = spec.get("info") or {}
    ops = extract_operations_from_openapi(spec)
    return {
        "version": BASELINE_VERSION,
        "api_title": info.get("title"),
        "api_version": info.get("version"),
        "openapi_version": spec.get("openapi"),
        "operation_count": len(ops),
        "operations": ops,
    }


def load_openapi_baseline() -> dict[str, Any]:
    raw = _BASELINE_PATH.read_text(encoding="utf-8")
    return json.loads(raw)


def save_openapi_baseline(spec: dict[str, Any]) -> Path:
    payload = build_baseline_payload(spec)
    _BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _BASELINE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return _BASELINE_PATH
