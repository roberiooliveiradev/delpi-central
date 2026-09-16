"""Validate execution arguments against TechnicalAction OpenAPI parameters.

Minimal OpenAPI-parameter validator (no external schema engine dependency).
Discovery and execution share ``build_argument_json_schema`` as the single contract.
"""

from __future__ import annotations

import re
from typing import Any

from app.application.external_capabilities.constants import (
    PRODUCT_SEARCH_DENIED_QUERY_PARAMS,
    PRODUCT_SEARCH_MAX_PAGE_SIZE,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
)

_TRANSPORT_FORBIDDEN = frozenset(
    {
        "url",
        "host",
        "path",
        "method",
        "operationId",
        "sql",
        "authorization",
        "Authorization",
    }
)


class ArgumentValidationError(ValueError):
    """Caller-facing argument validation failure."""


def _param_schema(param: dict[str, Any]) -> dict[str, Any]:
    nested = param.get("schema") if isinstance(param.get("schema"), dict) else {}
    schema: dict[str, Any] = {}
    ptype = param.get("type") or nested.get("type") or "string"
    schema["type"] = ptype
    for key in (
        "enum",
        "pattern",
        "format",
        "minimum",
        "maximum",
        "minLength",
        "maxLength",
        "default",
    ):
        if key in param:
            schema[key] = param[key]
        elif key in nested:
            schema[key] = nested[key]
    return schema


def build_argument_json_schema(action: TechnicalAction) -> dict[str, Any]:
    """JSON Schema-shaped object used by discovery AND execution (single contract)."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for segment in action.path.split("/"):
        if segment.startswith("{") and segment.endswith("}"):
            name = segment[1:-1]
            properties[name] = {"type": "string"}
            required.append(name)

    for param in action.parameters:
        if not isinstance(param, dict):
            continue
        name = param.get("name")
        if not name or not isinstance(name, str):
            continue
        if (
            action.operation_id == "search_products"
            and name in PRODUCT_SEARCH_DENIED_QUERY_PARAMS
        ):
            continue
        location = (param.get("in") or "query").lower()
        if location not in {"path", "query"}:
            continue
        prop = _param_schema(param)
        if action.operation_id == "search_products" and name == "page_size":
            prop["type"] = "integer"
            prop["minimum"] = 1
            prop["maximum"] = PRODUCT_SEARCH_MAX_PAGE_SIZE
            if "default" not in prop:
                prop["default"] = PRODUCT_SEARCH_MAX_PAGE_SIZE
        if action.operation_id == "search_products" and name == "page":
            prop["type"] = "integer"
            prop["minimum"] = 1
        properties[name] = prop
        if param.get("required") and name not in required:
            required.append(name)

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


def _coerce_value(name: str, value: Any, prop: dict[str, Any]) -> Any:
    expected = prop.get("type") or "string"
    if expected == "integer":
        if isinstance(value, bool):
            raise ArgumentValidationError(f"{name}: must be integer, not boolean")
        if isinstance(value, int):
            out = value
        elif isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
            out = int(value.strip())
        else:
            raise ArgumentValidationError(f"{name}: must be integer")
        if "minimum" in prop and out < prop["minimum"]:
            raise ArgumentValidationError(f"{name}: below minimum {prop['minimum']}")
        if "maximum" in prop and out > prop["maximum"]:
            raise ArgumentValidationError(f"{name}: above maximum {prop['maximum']}")
        return out
    if expected == "number":
        if isinstance(value, bool):
            raise ArgumentValidationError(f"{name}: must be number, not boolean")
        if isinstance(value, (int, float)):
            out = float(value)
        elif isinstance(value, str):
            try:
                out = float(value.strip())
            except ValueError as exc:
                raise ArgumentValidationError(f"{name}: must be number") from exc
        else:
            raise ArgumentValidationError(f"{name}: must be number")
        if "minimum" in prop and out < prop["minimum"]:
            raise ArgumentValidationError(f"{name}: below minimum {prop['minimum']}")
        if "maximum" in prop and out > prop["maximum"]:
            raise ArgumentValidationError(f"{name}: above maximum {prop['maximum']}")
        return out
    if expected == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
            return value.strip().lower() == "true"
        raise ArgumentValidationError(f"{name}: must be boolean")
    # string (default)
    if not isinstance(value, str):
        raise ArgumentValidationError(f"{name}: must be string")
    if "enum" in prop and value not in prop["enum"]:
        raise ArgumentValidationError(f"{name}: value not in enum")
    if "pattern" in prop and not re.fullmatch(str(prop["pattern"]), value):
        raise ArgumentValidationError(f"{name}: does not match pattern")
    if "minLength" in prop and len(value) < int(prop["minLength"]):
        raise ArgumentValidationError(f"{name}: shorter than minLength")
    if "maxLength" in prop and len(value) > int(prop["maxLength"]):
        raise ArgumentValidationError(f"{name}: longer than maxLength")
    return value


def validate_arguments(
    action: TechnicalAction,
    arguments: dict[str, Any] | None,
) -> dict[str, Any]:
    """Validate and normalize arguments; reject unknowns and transport smuggling."""
    raw = dict(arguments or {})
    for forbidden in _TRANSPORT_FORBIDDEN:
        if forbidden in raw:
            raise ArgumentValidationError(f"Argument '{forbidden}' is not allowed")

    schema = build_argument_json_schema(action)
    properties: dict[str, Any] = schema["properties"]
    required: list[str] = list(schema.get("required") or [])

    unknown = [k for k in raw if k not in properties]
    if unknown:
        raise ArgumentValidationError(f"Unknown argument(s): {', '.join(sorted(unknown))}")

    for name in required:
        if name not in raw or raw[name] is None:
            raise ArgumentValidationError(f"Missing required argument: {name}")

    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        if value is None:
            continue
        cleaned[key] = _coerce_value(key, value, properties[key])
    return cleaned


def split_path_and_query(
    action: TechnicalAction,
    arguments: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Fill path template and return remaining query arguments."""
    from urllib.parse import quote

    remaining = dict(arguments)
    parts: list[str] = []
    for segment in action.path.split("/"):
        if segment.startswith("{") and segment.endswith("}"):
            name = segment[1:-1]
            if name not in remaining:
                raise ArgumentValidationError(f"Missing path parameter: {name}")
            value = remaining.pop(name)
            parts.append(quote(str(value), safe=""))
        else:
            parts.append(segment)
    return "/".join(parts), remaining
