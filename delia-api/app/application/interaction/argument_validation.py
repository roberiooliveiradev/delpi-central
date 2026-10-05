"""Bounded deterministic argument-instance validation.

ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03R1 (ledger §6.128):
model-proposed invocation arguments are validated against the live
owner ``inputSchema`` — a provider-neutral bounded subset of JSON
Schema sufficient for the approved owner contracts (object, array,
string, integer, number, boolean, null; properties, required, items,
enum, const, additionalProperties, anyOf, min/max length/items).

This module validates *argument instances* — ``shared/delpi_mcp/
tool_validation.py`` validates the tool-definition wire shape, never
an invocation payload; the two concerns are not conflated.

Security posture: fail closed on every ambiguity; orchestration-owned
fields (candidate_token, proposal_handle, confirmation,
idempotency_key, commit_now) are denied at the top-level parameter
boundary — nested owner business payloads remain owner-validated. All
bounds are DÉLIA resource/security limits, not capability catalogs.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

# DÉLIA-side resource/security bounds for argument instances.
MAX_ARGUMENT_DEPTH = 6
MAX_ARGUMENT_NODES = 96
MAX_ARGUMENT_OBJECT_KEYS = 24
MAX_ARGUMENT_ARRAY_ITEMS = 32
MAX_ARGUMENT_STRING_CHARS = 4000
MAX_ARGUMENT_SERIALIZED_BYTES = 8192
MAX_TOP_LEVEL_KEYS = 32
MAX_ANYOF_BRANCHES = 8

# Orchestration-resolved tool parameters: never accepted from a model
# proposal — DÉLIA fills them from owner-issued state or the governed-
# write decision. ``commit_now`` is generic orchestration-control
# semantics (it would collapse PREPARE+ACT inside one owner call,
# bypassing the DÉLIA confirmation gate), not an owner business field.
ORCHESTRATED_FIELDS = frozenset(
    {
        "candidate_token",
        "proposal_handle",
        "confirmation",
        "idempotency_key",
        "commit_now",
    }
)


def normalize_arguments(raw: object) -> Mapping[str, Any] | None:
    """Normalize the model's ``arguments`` field into a Mapping.

    Accepts a typed Mapping verbatim (bounded). Accepts a JSON-encoded
    string only when the ENTIRE trimmed payload is a valid JSON object
    — the observed production model shape. Rejects arrays, scalars,
    leading/trailing prose, invalid JSON and oversized payloads.
    """
    if raw is None:
        return {}
    if isinstance(raw, str):
        text = raw.strip()
        if not text or len(text.encode("utf-8")) > MAX_ARGUMENT_SERIALIZED_BYTES:
            return None
        if not (text.startswith("{") and text.endswith("}")):
            return None
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            return None
        if not isinstance(parsed, dict):
            return None
        raw = parsed
    if not isinstance(raw, Mapping):
        return None
    if len(raw) > MAX_TOP_LEVEL_KEYS:
        return None
    try:
        serialized = json.dumps(raw, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return None
    if len(serialized.encode("utf-8")) > MAX_ARGUMENT_SERIALIZED_BYTES:
        return None
    return raw


def validate_arguments(
    arguments: Mapping[str, Any],
    schema: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Validate arguments against the live owner inputSchema.

    Returns a plain dict on success, None on any violation. Unknown
    top-level fields are always rejected; nested unknown fields are
    rejected when the schema forbids them (``additionalProperties:
    false`` or a declared properties set with a schema-valued
    additionalProperties). Orchestrated fields are denied at the
    top-level parameter boundary only.
    """
    if not isinstance(schema, Mapping):
        # Owner declared no schema: only an empty object is
        # acceptable — nothing else can be assumed.
        if dict(arguments):
            return None
        return {}
    if not _check_value(
        arguments, schema, _Budget(), depth=0, top_level=True
    ):
        return None
    return dict(arguments)


def validate_untyped_arguments(
    arguments: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Bounded validation when no owner schema is available.

    The owner contract has not declared a schema — only bounded
    values are accepted, orchestrated fields are still denied at the
    parameter boundary, and the owner remains the final validator.
    """
    if not _check_value(arguments, {}, _Budget(), depth=0, top_level=True):
        return None
    return dict(arguments)


class _Budget:
    """Global node/serialization bounds for one validation run."""

    def __init__(self) -> None:
        self.nodes = 0

    def spend(self, amount: int = 1) -> bool:
        self.nodes += amount
        return self.nodes <= MAX_ARGUMENT_NODES


def _json_types(schema_type: object) -> frozenset[str] | None:
    if isinstance(schema_type, str):
        return frozenset({schema_type})
    if isinstance(schema_type, (list, tuple)):
        return frozenset(t for t in schema_type if isinstance(t, str))
    return None


def _type_ok(value: Any, allowed: frozenset[str]) -> bool:
    for t in allowed:
        if t == "string" and isinstance(value, str):
            return True
        if t == "boolean" and isinstance(value, bool):
            return True
        if t == "integer" and isinstance(value, int) and not isinstance(
            value, bool
        ):
            return True
        if t == "number" and isinstance(value, (int, float)) and not isinstance(
            value, bool
        ):
            return True
        if t == "object" and isinstance(value, Mapping):
            return True
        if t == "array" and isinstance(value, (list, tuple)):
            return True
        if t == "null" and value is None:
            return True
    return False


def _check_value(
    value: Any,
    schema: Mapping[str, Any],
    budget: _Budget,
    *,
    depth: int,
    top_level: bool = False,
) -> bool:
    if depth > MAX_ARGUMENT_DEPTH or not budget.spend():
        return False
    if not isinstance(schema, Mapping):
        return False

    # enum / const — exact allowed values.
    if "const" in schema:
        if value != schema["const"]:
            return False
    enum = schema.get("enum")
    if isinstance(enum, (list, tuple)) and enum:
        if not any(value == option for option in enum):
            return False

    # anyOf / oneOf — value must satisfy a bounded branch set.
    for combiner in ("anyOf", "oneOf"):
        branches = schema.get(combiner)
        if isinstance(branches, (list, tuple)) and branches:
            matched = 0
            for branch in branches[:MAX_ANYOF_BRANCHES]:
                if not isinstance(branch, Mapping):
                    return False
                if _check_value(value, branch, budget, depth=depth + 1):
                    matched += 1
            if combiner == "anyOf" and matched == 0:
                return False
            if combiner == "oneOf" and matched != 1:
                return False

    types = _json_types(schema.get("type"))
    if types is not None and not _type_ok(value, types):
        return False

    if isinstance(value, str):
        if len(value) > MAX_ARGUMENT_STRING_CHARS:
            return False
        max_length = schema.get("maxLength")
        if isinstance(max_length, int) and len(value) > max_length:
            return False
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            return False
        return True

    if isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        return minimum is None and maximum is None

    if isinstance(value, (int, float)):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            return False
        maximum = schema.get("maximum")
        if isinstance(maximum, (int, float)) and value > maximum:
            return False
        return True

    if isinstance(value, (list, tuple)):
        if len(value) > MAX_ARGUMENT_ARRAY_ITEMS:
            return False
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            return False
        max_items = schema.get("maxItems")
        if isinstance(max_items, int) and len(value) > max_items:
            return False
        items_schema = schema.get("items")
        if isinstance(items_schema, Mapping):
            for item in value:
                if not _check_value(
                    item, items_schema, budget, depth=depth + 1
                ):
                    return False
        else:
            # No item schema declared: items must still stay inside
            # deterministic bounds.
            for item in value:
                if not _check_value(item, {}, budget, depth=depth + 1):
                    return False
        return True

    if isinstance(value, Mapping):
        if len(value) > MAX_ARGUMENT_OBJECT_KEYS:
            return False
        properties = schema.get("properties")
        declared = (
            set(str(k) for k in properties)
            if isinstance(properties, Mapping)
            else set()
        )
        additional = schema.get("additionalProperties")
        required = schema.get("required")
        if isinstance(required, (list, tuple)):
            missing = {
                str(r)
                for r in required
                if not (top_level and str(r) in ORCHESTRATED_FIELDS)
            }
            if not missing.issubset(value.keys()):
                return False
        for key, item in value.items():
            key = str(key)
            if top_level and key in ORCHESTRATED_FIELDS:
                return False
            if isinstance(properties, Mapping) and key in properties:
                prop_schema = properties[key]
                if not isinstance(prop_schema, Mapping):
                    return False
                if not _check_value(
                    item, prop_schema, budget, depth=depth + 1
                ):
                    return False
                continue
            # Undeclared key: rejected at the parameter boundary only
            # when the owner schema declares a properties set; a
            # schema with no properties leaves keys to the owner.
            if top_level and isinstance(properties, Mapping):
                return False
            if additional is False:
                return False
            if isinstance(additional, Mapping):
                if not _check_value(
                    item, additional, budget, depth=depth + 1
                ):
                    return False
                continue
            # additionalProperties absent/true: bounded pass-through
            # (owner business payload — owner stays final validator).
            if not _check_value(item, {}, budget, depth=depth + 1):
                return False
        return True

    # value is None or unhandled scalar
    if value is None:
        return types is None or "null" in types
    return False
