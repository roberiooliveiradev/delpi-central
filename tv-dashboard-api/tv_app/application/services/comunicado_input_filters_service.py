"""Contribuições de blocos `input` para o merge canônico de params (espelho TS)."""

from __future__ import annotations

from typing import Any


def _is_empty(value: Any) -> bool:
    return value is None or value == ""


def _z_index(block: dict[str, Any]) -> int:
    style = block.get("style")
    if isinstance(style, dict) and isinstance(style.get("zIndex"), (int, float)):
        return int(style["zIndex"])
    return 1


def resolve_input_target_scope(input_cfg: dict[str, Any] | None) -> str:
    if isinstance(input_cfg, dict) and input_cfg.get("targetScope") == "sources":
        return "sources"
    return "slide"


def intersect_param_schema_keys(schemas: list[dict[str, Any]]) -> list[str]:
    if not schemas:
        return []
    keys = set(schemas[0].keys())
    for schema in schemas[1:]:
        keys &= set(schema.keys())
    return sorted(keys)


def resolve_input_param_schema_field(
    param_key: str,
    schemas: list[dict[str, Any]],
) -> dict[str, Any] | None:
    key = str(param_key or "").strip()
    if not key or not schemas:
        return None
    if key not in intersect_param_schema_keys(schemas):
        return None
    for schema in schemas:
        field = schema.get(key)
        if isinstance(field, dict):
            return field
    return None


def is_value_allowed_by_param_schema(value: Any, field: dict[str, Any] | None) -> bool:
    if _is_empty(value) or not isinstance(field, dict):
        return False
    raw_enum = field.get("enum")
    if isinstance(raw_enum, list) and len(raw_enum) > 0:
        return any(str(item) == str(value) for item in raw_enum if item is not None)
    field_type = str(field.get("type") or "")
    if field_type == "boolean":
        return isinstance(value, bool) or value in ("true", "false", True, False)
    if field_type in {"integer", "number"}:
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False
    return True


def collect_input_filter_contributions(
    blocks: list[Any] | None,
    *,
    runtime_overrides: dict[str, Any] | None = None,
    schema_by_source_id: dict[str, dict[str, Any]] | None = None,
    slide_schemas: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Retorna { slide: dict, bySourceId: dict[str, dict] }.
    Com schemas fornecidos, valores fora do enum/tipo são descartados.
    """
    slide: dict[str, Any] = {}
    by_source_id: dict[str, dict[str, Any]] = {}

    input_blocks = [
        block
        for block in (blocks or [])
        if isinstance(block, dict) and str(block.get("type") or "") == "input"
    ]
    input_blocks.sort(key=lambda b: (_z_index(b), str(b.get("id") or "")))

    def apply_value(
        target: dict[str, Any],
        param_key: str,
        value: Any,
        field: dict[str, Any] | None,
        *,
        require_schema: bool,
    ) -> None:
        if _is_empty(value):
            return
        if not require_schema:
            target[param_key] = value
            return
        if field and is_value_allowed_by_param_schema(value, field):
            target[param_key] = value

    require_slide = slide_schemas is not None
    require_source = schema_by_source_id is not None

    for block in input_blocks:
        input_cfg = block.get("input") if isinstance(block.get("input"), dict) else {}
        param_key = str(input_cfg.get("paramKey") or "").strip()
        if not param_key:
            continue
        scope = resolve_input_target_scope(input_cfg)
        value = input_cfg.get("defaultValue")

        if scope == "slide":
            field = (
                resolve_input_param_schema_field(param_key, slide_schemas or [])
                if require_slide
                else None
            )
            apply_value(slide, param_key, value, field, require_schema=require_slide)
            continue

        ids = [
            str(item).strip()
            for item in (input_cfg.get("targetSourceIds") or [])
            if str(item).strip()
        ]
        for source_id in ids:
            bucket = by_source_id.setdefault(source_id, {})
            schema = (schema_by_source_id or {}).get(source_id) if require_source else None
            field = (
                resolve_input_param_schema_field(param_key, [schema]) if schema else None
            )
            apply_value(bucket, param_key, value, field, require_schema=require_source)

    overrides = runtime_overrides if isinstance(runtime_overrides, dict) else {}
    override_slide = overrides.get("slide")
    if isinstance(override_slide, dict):
        for key, value in override_slide.items():
            field = (
                resolve_input_param_schema_field(str(key), slide_schemas or [])
                if require_slide
                else None
            )
            apply_value(slide, str(key), value, field, require_schema=require_slide)

    override_by_source = overrides.get("bySourceId")
    if isinstance(override_by_source, dict):
        for source_id, params in override_by_source.items():
            if not isinstance(params, dict):
                continue
            sid = str(source_id)
            bucket = by_source_id.setdefault(sid, {})
            schema = (schema_by_source_id or {}).get(sid) if require_source else None
            for key, value in params.items():
                field = (
                    resolve_input_param_schema_field(str(key), [schema]) if schema else None
                )
                apply_value(bucket, str(key), value, field, require_schema=require_source)

    return {"slide": slide, "bySourceId": by_source_id}


def merge_filter_layers(*layers: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        for key, value in layer.items():
            if _is_empty(value):
                continue
            merged[str(key)] = value
    return merged
