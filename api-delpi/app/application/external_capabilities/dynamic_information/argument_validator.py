"""Validate execution arguments against TechnicalAction OpenAPI ∩ DAVI approved inputs.

Discovery and execution share ``build_argument_json_schema`` as the single contract.
Governed numeric/date constraints come from allowlist argumentConstraints metadata,
never from operationId-specific executor branches.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, Mapping

from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
)


def _pagination_limits() -> tuple[int, int]:
    """Return (default_page_size, max_page_size) from DAVI budgets — not Product Search."""
    budgets = load_dynamic_read_budgets()
    default_size = int(budgets.get("default_page_size") or 50)
    max_size = int(budgets.get("max_page_size") or budgets.get("execute_max_items") or 50)
    default_size = max(1, default_size)
    max_size = max(default_size, max_size)
    return default_size, max_size

# Transport names are forbidden globally. ``sql`` is intentionally NOT here:
# it is a legitimate owner-declared requestBody field of the canonical
# read-only SQL route — safety comes from trusted OpenAPI ∩
# approvedInputFields ∩ additionalProperties=false ∩ route validation.
_TRANSPORT_FORBIDDEN = frozenset(
    {
        "url",
        "host",
        "path",
        "method",
        "operationId",
        "authorization",
        "Authorization",
    }
)


class ArgumentValidationError(ValueError):
    """Caller-facing argument validation failure."""


def _param_schema(param: dict[str, Any]) -> dict[str, Any]:
    nested = param.get("schema") if isinstance(param.get("schema"), dict) else {}
    nested = _unwrap_nullable_schema(dict(nested))
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


def _approved_input_allowset(action: TechnicalAction) -> set[str] | None:
    """When governance declares approvedInputFields, discovery/execution honor only those."""
    if action.approved_input_fields:
        return set(action.approved_input_fields)
    return None


_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _argument_bindings(action: TechnicalAction) -> dict[str, str]:
    """Trusted external→owner argument-name bindings (allowlist metadata only)."""
    raw = getattr(action, "argument_bindings", None) or {}
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, str] = {}
    for external, owner in raw.items():
        if not isinstance(external, str) or not isinstance(owner, str):
            continue
        external = external.strip()
        owner = owner.strip()
        if not (_IDENT.fullmatch(external) and _IDENT.fullmatch(owner)):
            continue
        if external in _TRANSPORT_FORBIDDEN or owner in _TRANSPORT_FORBIDDEN:
            continue
        out[external] = owner
    return out


def _owner_param_names(action: TechnicalAction) -> set[str]:
    """Owner-declared names: path placeholders, declared parameters, body fields."""
    names: set[str] = set()
    for segment in action.path.split("/"):
        if segment.startswith("{") and segment.endswith("}"):
            names.add(segment[1:-1])
    for param in action.parameters or ():
        if isinstance(param, dict) and isinstance(param.get("name"), str):
            names.add(param["name"])
    for name in getattr(action, "body_fields", frozenset()) or ():
        names.add(str(name))
    return names


def _owner_to_external(action: TechnicalAction) -> dict[str, str]:
    """Reverse trusted bindings, dropping collisions and nonexistent targets."""
    bindings = _argument_bindings(action)
    owners = _owner_param_names(action)
    seen: dict[str, str] = {}
    duplicates: set[str] = set()
    for external, owner in bindings.items():
        if owner in seen:
            duplicates.add(owner)
            continue
        seen[owner] = external
    return {
        owner: external
        for owner, external in seen.items()
        if owner not in duplicates and owner in owners
    }


def bind_owner_arguments(
    action: TechnicalAction,
    validated_arguments: dict[str, Any],
) -> dict[str, Any]:
    """Rename validated EXTERNAL arguments to trusted owner names (fail closed).

    Runs after external validation, before fixed catalog HTTP binding. The
    mapping source is allowlist metadata only; a binding to an owner name that
    is not declared in trusted OpenAPI/path/query metadata fails closed.
    """
    raw = getattr(action, "argument_bindings", None) or {}
    if isinstance(raw, Mapping):
        for external, owner in raw.items():
            pair = {external, owner} if isinstance(external, str) and isinstance(owner, str) else set()
            if pair & _TRANSPORT_FORBIDDEN:
                raise ArgumentValidationError("Argument binding targets forbidden name")
    bindings = _argument_bindings(action)
    if not bindings:
        return dict(validated_arguments or {})
    owners = _owner_param_names(action)
    owners_seen: set[str] = set()
    for owner in bindings.values():
        if owner in owners_seen:
            raise ArgumentValidationError("Ambiguous argument binding target")
        owners_seen.add(owner)
        if owner not in owners:
            raise ArgumentValidationError("Argument binding target is not declared")
    out = dict(validated_arguments or {})
    for external, owner in bindings.items():
        if external not in out:
            continue
        if owner in out and out[owner] != out[external]:
            raise ArgumentValidationError("Ambiguous argument binding target")
        out[owner] = out.pop(external)
    return out


def _argument_constraints(action: TechnicalAction) -> Mapping[str, Any]:
    raw = getattr(action, "argument_constraints", None) or {}
    return raw if isinstance(raw, Mapping) else {}


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return int(value.strip())
    return None


def _argument_limits(constraints: Mapping[str, Any]) -> dict[str, Any]:
    raw = constraints.get("argumentLimits") or {}
    return raw if isinstance(raw, dict) else {}


def _require_arguments(constraints: Mapping[str, Any]) -> list[str]:
    """Allowlist-governed extra required args (beyond OpenAPI required flags).

    Generic governance only — never operationId-specific branching. Authors must
    also list each name in approvedInputFields so the property exists.
    """
    raw = constraints.get("requireArguments") or []
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            name = item.strip()
            if name not in out:
                out.append(name)
    return out


def _apply_argument_limits_to_schema(
    properties: dict[str, Any],
    constraints: Mapping[str, Any],
) -> None:
    """Tighten OpenAPI numeric bounds with governed DAVI limits (fail-closed, no clamp)."""
    for name, spec in _argument_limits(constraints).items():
        if name not in properties or not isinstance(spec, dict):
            continue
        prop = properties[name]
        for bound_key in ("minimum", "maximum"):
            governed = _as_int(spec.get(bound_key))
            if governed is None:
                continue
            existing = prop.get(bound_key)
            existing_i = _as_int(existing)
            if bound_key == "maximum":
                prop[bound_key] = min(existing_i, governed) if existing_i is not None else governed
            else:
                prop[bound_key] = max(existing_i, governed) if existing_i is not None else governed
        for bound_key in ("minItems", "maxItems"):
            governed = _as_int(spec.get(bound_key))
            if governed is None:
                continue
            existing = prop.get(bound_key)
            existing_i = _as_int(existing)
            if bound_key == "maxItems":
                prop[bound_key] = min(existing_i, governed) if existing_i is not None else governed
            else:
                prop[bound_key] = max(existing_i, governed) if existing_i is not None else governed
        for bound_key in ("minLength", "maxLength"):
            governed = _as_int(spec.get(bound_key))
            if governed is None:
                continue
            existing = prop.get(bound_key)
            existing_i = _as_int(existing)
            if bound_key == "maxLength":
                prop[bound_key] = min(existing_i, governed) if existing_i is not None else governed
            else:
                prop[bound_key] = max(existing_i, governed) if existing_i is not None else governed
        if "default" in spec:
            prop["default"] = spec["default"]
        governed_enum = spec.get("enum")
        if isinstance(governed_enum, list) and governed_enum:
            existing_enum = prop.get("enum")
            if isinstance(existing_enum, list) and existing_enum:
                # Fail-closed intersection: DAVI may only narrow the owner enum.
                prop["enum"] = [v for v in existing_enum if v in governed_enum]
            else:
                prop["enum"] = list(governed_enum)


def _apply_require_arguments_to_schema(
    properties: dict[str, Any],
    required: list[str],
    constraints: Mapping[str, Any],
) -> None:
    for name in _require_arguments(constraints):
        if name not in properties:
            continue
        if name not in required:
            required.append(name)


def _constraint_today() -> date:
    """Clock seam for governed date-range tests. Production uses the local date."""
    return date.today()


_ABSENT_END_TODAY = "today"
_ABSENT_START_EFFECTIVE_END_MINUS_WINDOW = "effectiveEndMinusDefaultWindow"


def _parse_constraint_date(name: str, value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not isinstance(value, str):
        raise ArgumentValidationError(f"{name}: must be a date (YYYY-MM-DD)")
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ArgumentValidationError(f"{name}: must be a date (YYYY-MM-DD)")


def _iter_date_range_specs(constraints: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Collect governed date-range specs.

    Supports legacy singular ``dateRange`` and metadata-driven ``dateRanges``
    (independent windows, e.g. scheduled + delivery). No operationId branching.
    """
    specs: list[dict[str, Any]] = []
    singular = constraints.get("dateRange")
    if isinstance(singular, dict):
        specs.append(singular)
    plural = constraints.get("dateRanges")
    if isinstance(plural, list):
        for item in plural:
            if isinstance(item, dict):
                specs.append(item)
    return specs


def _validate_one_date_range_spec(
    cleaned: dict[str, Any],
    spec: Mapping[str, Any],
) -> None:
    start_field = str(spec.get("startField") or "").strip()
    end_field = str(spec.get("endField") or "").strip()
    max_days = _as_int(spec.get("maxDays"))
    fallback_field = str(spec.get("fallbackStartField") or "").strip() or None
    default_window = _as_int(spec.get("defaultWindowDays"))
    absent_end = str(spec.get("absentEnd") or "").strip()
    absent_start = str(spec.get("absentStart") or "").strip()
    uses_effective_window = (
        absent_end == _ABSENT_END_TODAY
        and absent_start == _ABSENT_START_EFFECTIVE_END_MINUS_WINDOW
        and default_window is not None
        and default_window >= 0
    )
    if not start_field or not end_field or max_days is None:
        return
    if max_days < 0:
        raise ArgumentValidationError("dateRange.maxDays must be >= 0")

    start_raw = cleaned.get(start_field)
    end_raw = cleaned.get(end_field)
    # Fail-closed pair contract: when enabled, XOR is rejected without synthesizing
    # the missing bound (no today / same-day / window injection into arguments).
    if bool(spec.get("requireBothOrNeither")):
        if (start_raw is None) != (end_raw is None):
            raise ArgumentValidationError(
                f"{start_field} and {end_field} must both be provided or both omitted"
            )
    if start_raw is None and end_raw is None and not uses_effective_window:
        return
    # One-sided contract: a single supplied bound is validated as a date but the
    # missing bound is never synthesized (no today / same-day / window injection
    # into arguments); ordering and maxDays apply only when both are present.
    if bool(spec.get("allowSingleBound")) and (start_raw is None) != (
        end_raw is None
    ):
        if start_raw is not None:
            _parse_constraint_date(start_field, start_raw)
        else:
            _parse_constraint_date(end_field, end_raw)
        return

    today = _constraint_today()
    if uses_effective_window:
        end = (
            _parse_constraint_date(end_field, end_raw)
            if end_raw is not None
            else today
        )
        start = (
            _parse_constraint_date(start_field, start_raw)
            if start_raw is not None
            else end - timedelta(days=default_window)
        )
    else:
        fallback_raw = cleaned.get(fallback_field) if fallback_field else None
        if start_raw is not None:
            start = _parse_constraint_date(start_field, start_raw)
        elif fallback_raw is not None:
            start = _parse_constraint_date(fallback_field, fallback_raw)
        else:
            start = today

        if end_raw is not None:
            end = _parse_constraint_date(end_field, end_raw)
        elif start_raw is not None:
            end = start
        else:
            end = today

    if end < start:
        raise ArgumentValidationError(f"{end_field}: must not be before {start_field}")
    span_days = (end - start).days
    day_count_mode = str(spec.get("dayCountMode") or "").strip().lower()
    if day_count_mode == "inclusive":
        # Inclusive calendar-day count: start..end with N days means (end-start).days + 1.
        # Aligns with backends that enforce (end - start).days + 1 <= maxDays.
        inclusive_days = span_days + 1
        if inclusive_days > max_days:
            raise ArgumentValidationError(
                f"Date interval between {start_field} and {end_field} exceeds "
                f"{max_days} inclusive days"
            )
    elif span_days > max_days:
        raise ArgumentValidationError(
            f"Date interval between {start_field} and {end_field} exceeds {max_days} days"
        )


def _validate_date_range(
    cleaned: dict[str, Any],
    constraints: Mapping[str, Any],
) -> None:
    for spec in _iter_date_range_specs(constraints):
        _validate_one_date_range_spec(cleaned, spec)


def _apply_governed_defaults(
    raw: dict[str, Any],
    properties: dict[str, Any],
    constraints: Mapping[str, Any],
) -> None:
    """Inject only governed argumentLimits defaults — never OpenAPI-wide defaults."""
    for name, spec in _argument_limits(constraints).items():
        if name not in properties or not isinstance(spec, dict):
            continue
        if name in raw and raw[name] is not None:
            continue
        if "default" in spec:
            raw[name] = spec["default"]


def build_argument_json_schema(action: TechnicalAction) -> dict[str, Any]:
    """JSON Schema used by discovery AND execution (single external contract)."""
    properties: dict[str, Any] = {}
    required: list[str] = []
    approved = _approved_input_allowset(action)
    owner_to_external = _owner_to_external(action)

    for segment in action.path.split("/"):
        if segment.startswith("{") and segment.endswith("}"):
            name = segment[1:-1]
            external = owner_to_external.get(name, name)
            if approved is not None and external not in approved:
                continue
            properties[external] = {"type": "string"}
            required.append(external)

    for param in action.parameters:
        if not isinstance(param, dict):
            continue
        name = param.get("name")
        if not name or not isinstance(name, str):
            continue
        external = owner_to_external.get(name, name)
        if approved is not None and external not in approved:
            continue
        location = (param.get("in") or "query").lower()
        if location not in {"path", "query"}:
            continue
        prop = _param_schema(param)
        if external == "page_size":
            default_size, max_size = _pagination_limits()
            prop["type"] = "integer"
            prop["minimum"] = 1
            openapi_max = prop.get("maximum")
            if openapi_max is not None:
                try:
                    max_size = min(max_size, int(openapi_max))
                except (TypeError, ValueError):
                    pass
            prop["maximum"] = max_size
            if "default" not in prop:
                prop["default"] = min(default_size, max_size)
        if external == "page":
            prop["type"] = "integer"
            prop["minimum"] = 1
            if "default" not in prop:
                prop["default"] = 1
        properties[external] = prop
        if param.get("required") and external not in required:
            required.append(external)

    # Trusted JSON body fields (catalog-normalized requestBody ∩ approved inputs).
    body = action.request_body or {}
    body_properties = body.get("properties")
    if isinstance(body_properties, Mapping):
        for name, spec in body_properties.items():
            if not isinstance(spec, Mapping):
                continue
            external = owner_to_external.get(name, name)
            if approved is not None and external not in approved:
                continue
            if external not in properties:
                properties[external] = dict(spec)
        for name in body.get("required") or ():
            external = owner_to_external.get(name, name)
            if external in properties and external not in required:
                required.append(external)

    constraints = _argument_constraints(action)
    _apply_argument_limits_to_schema(properties, constraints)
    _apply_require_arguments_to_schema(properties, required, constraints)

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


def _unwrap_nullable_schema(prop: dict[str, Any]) -> dict[str, Any]:
    """Collapse Optional-style wrappers (anyOf/oneOf/type lists) into the
    concrete subtype schema so type, bounds, and enum checks still apply."""
    type_ = prop.get("type")
    if isinstance(type_, list):
        non_null = [t for t in type_ if t != "null"]
        prop = dict(prop, type=non_null[0]) if len(non_null) == 1 else prop
    for comb in ("anyOf", "oneOf"):
        subs = prop.get(comb)
        if not isinstance(subs, list):
            continue
        non_null = [
            s
            for s in subs
            if isinstance(s, Mapping) and (s.get("type") or "") != "null"
        ]
        if len(non_null) != 1:
            continue
        merged = dict(non_null[0])
        for key, val in prop.items():
            if key != comb:
                merged[key] = val
        prop = merged
    return prop


def _coerce_value(name: str, value: Any, prop: dict[str, Any]) -> Any:
    prop = _unwrap_nullable_schema(prop)
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
    if expected == "array":
        if isinstance(value, str) or not isinstance(value, (list, tuple)):
            raise ArgumentValidationError(f"{name}: must be an array")
        item_type = (prop.get("items") or {}).get("type") or "string"
        if item_type != "string":
            raise ArgumentValidationError(f"{name}: unsupported array item type")
        out = []
        for item in value:
            if not isinstance(item, str):
                raise ArgumentValidationError(f"{name}: array items must be strings")
            out.append(item)
        if "minItems" in prop and len(out) < int(prop["minItems"]):
            raise ArgumentValidationError(f"{name}: fewer than minItems {prop['minItems']}")
        if "maxItems" in prop and len(out) > int(prop["maxItems"]):
            raise ArgumentValidationError(f"{name}: more than maxItems {prop['maxItems']}")
        return out
    if expected == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
            return value.strip().lower() == "true"
        raise ArgumentValidationError(f"{name}: must be boolean")
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
    constraints = _argument_constraints(action)

    unknown = [k for k in raw if k not in properties]
    if unknown:
        raise ArgumentValidationError(f"Unknown argument(s): {', '.join(sorted(unknown))}")

    _apply_governed_defaults(raw, properties, constraints)

    for name in required:
        if name not in raw or raw[name] is None:
            raise ArgumentValidationError(f"Missing required argument: {name}")

    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        if value is None:
            continue
        cleaned[key] = _coerce_value(key, value, properties[key])
    _validate_date_range(cleaned, constraints)
    return cleaned
