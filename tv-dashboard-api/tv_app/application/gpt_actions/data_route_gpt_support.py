"""Helpers for GPT data-route discovery/preview projection."""

from __future__ import annotations

from typing import Any, Mapping


_GPT_ROUTE_KEYS = (
    "operationId",
    "path",
    "httpMethod",
    "label",
    "category",
    "description",
    "whenToUse",
    "paramSchema",
    "paramStrategy",
    "allowedDisplayModes",
    "dateRangeKeys",
    "valueFields",
    "valueFieldLabels",
    "valueFieldTypes",
)


def project_route_for_gpt(route: Mapping[str, Any]) -> dict[str, Any]:
    """Compact route DTO for Custom GPT (no encyclopedia dump)."""
    out: dict[str, Any] = {}
    for key in _GPT_ROUTE_KEYS:
        value = route.get(key)
        if value is not None and value != "" and value != [] and value != {}:
            out[key] = value
    # AUTHORITATIVE ROUTE FIELD > DERIVED TV CALCULATION: o caller precisa ver
    # os campos que a rota já fornece antes de derivar métricas via transform.
    projectable = route.get("projectableFields")
    if isinstance(projectable, list) and projectable:
        out["projectableFields"] = [
            {
                key: item[key]
                for key in ("name", "label", "semanticType")
                if isinstance(item, dict) and item.get(key) not in (None, "")
            }
            for item in projectable
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        ]
    if route.get("reason") is not None:
        out["reason"] = route.get("reason")
    if route.get("score") is not None:
        out["score"] = route.get("score")
    return out


def validate_route_params(
    route: Mapping[str, Any],
    params: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate/normalize params against catalog paramSchema.

    Raises ValueError with a stable message; callers map to GptActionsError codes.
    """
    schema = route.get("paramSchema")
    raw = dict(params) if isinstance(params, Mapping) else {}
    if not isinstance(schema, Mapping) or not schema:
        return raw

    cleaned: dict[str, Any] = {}
    for key, spec in schema.items():
        if not isinstance(spec, Mapping):
            continue
        name = str(key).strip()
        if not name:
            continue
        optional = True
        if isinstance(spec.get("required"), bool):
            optional = not bool(spec.get("required"))
        elif "optional" in spec:
            optional = bool(spec.get("optional"))
        value = raw.get(name)
        if value is None or value == "":
            if "default" in spec and should_keep_default(spec):
                cleaned[name] = spec.get("default")
                continue
            if not optional:
                label = str(spec.get("label") or name).strip() or name
                raise ValueError(f"PARAM_REQUIRED:{name}:{label}")
            continue
        enum_values = spec.get("enum")
        if isinstance(enum_values, list) and enum_values:
            token = str(value).strip()
            allowed = {str(item).strip() for item in enum_values}
            if token not in allowed:
                raise ValueError(
                    f"PARAM_INVALID:{name}:{token}:allowed={','.join(sorted(allowed))}"
                )
            cleaned[name] = token
            continue
        cleaned[name] = value

    # Preserve unknown keys only if schema empty handling already returned; here drop extras.
    return cleaned


def should_keep_default(spec: Mapping[str, Any]) -> bool:
    return spec.get("default") is not None


def build_preview_block_from_route(
    route: Mapping[str, Any],
    *,
    params: Mapping[str, Any],
) -> dict[str, Any]:
    operation_id = str(route.get("operationId") or "").strip()
    modes = route.get("allowedDisplayModes")
    display = "auto"
    if isinstance(modes, list) and modes:
        first = str(modes[0] or "").strip()
        if first:
            display = first
    return {
        "id": "gpt-route-preview",
        "type": "data_source",
        "title": str(route.get("label") or operation_id),
        "dataBinding": {
            "operationId": operation_id,
            "params": dict(params),
            "displayMode": display,
            "label": str(route.get("label") or operation_id),
        },
    }
