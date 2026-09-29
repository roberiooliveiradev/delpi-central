"""Wire-level validation of serialized MCP tool definitions.

Operates on plain mappings as produced by ``types.Tool.model_dump(
mode="json", by_alias=True)`` (both mcp 1.x and 2.x generations) — never on
server objects, SDK types, or domain internals. This module has no MCP SDK
dependency on purpose: the conformance contract is the JSON wire shape.

Validation layers are kept explicit so a failure preserves *which* contract
was violated:

- ``MCP_STANDARD``: spec-level wire shape (required fields, types,
  reserved ``_meta`` keys carrying schema-valid values, JSON
  serializability).
- ``DELPI_POLICY``: DELPI-owned conventions (``delpi/<key>`` namespacing,
  rejection of unknown bare ``_meta`` keys).
- ``OPENAI_COMPATIBILITY``: checks proven necessary by real OpenAI/ChatGPT
  incidents (e.g. ``securitySchemes`` objects carrying ``type``/``scopes``).
  Only evaluated under ``profile="openai"``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping

_TOOL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

# Tool fields defined by the MCP specification (all generations we support).
# Anything else at top level is a provider extension and is reported under
# the matching provider profile instead of silently accepted.
_SPEC_TOP_LEVEL_KEYS = frozenset(
    {
        "name",
        "title",
        "description",
        "inputSchema",
        "outputSchema",
        "annotations",
        "icons",
        "execution",
        "_meta",
    }
)

# Reserved (non-namespaced) ``_meta`` keys we recognize and validate.
# Each maps to a validator for its value shape.
_RESERVED_META_KEYS = frozenset({"securitySchemes"})

# Top-level extensions the OpenAI connector emits/reads. Reported only under
# the openai profile; flagged as unknown under the core profile.
_OPENAI_TOP_LEVEL_KEYS = frozenset({"securitySchemes"})

# Annotation keys with defined types in the MCP spec. Unknown annotation
# keys are tolerated (spec extensions); known ones must be typed correctly.
_ANNOTATION_BOOL_KEYS = ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")
_ANNOTATION_STR_KEYS = ("title",)


class ValidationLayer(str, Enum):
    MCP_STANDARD = "MCP_STANDARD"
    DELPI_POLICY = "DELPI_POLICY"
    OPENAI_COMPATIBILITY = "OPENAI_COMPATIBILITY"


@dataclass(frozen=True)
class ValidationIssue:
    """One wire-level finding. ``path`` is a dotted locator, e.g.
    ``_meta.securitySchemes[0]``; ``code`` is a stable diagnostic id."""

    layer: ValidationLayer
    code: str
    message: str
    path: str = ""


def _issue(layer: ValidationLayer, code: str, message: str, path: str = "") -> ValidationIssue:
    return ValidationIssue(layer=layer, code=code, message=message, path=path)


def _json_serializable(value: Any) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    return True


def _is_namespaced_meta_key(key: str) -> bool:
    """``prefix/name`` namespaced key (e.g. ``delpi/toolClass``)."""
    prefix, sep, _ = key.partition("/")
    return bool(sep and prefix and "." not in prefix and " " not in key)


def _is_delpi_namespace(key: str) -> bool:
    return key.startswith("delpi/")


def _validate_security_scheme_objects(value: Any, path: str) -> list[ValidationIssue]:
    """Reserved ``securitySchemes`` must be a list of typed objects.

    A list of strings is the historical VISTA defect that broke ChatGPT
    discovery (the connector parses reserved ``_meta.securitySchemes`` as
    typed OAuthSecurityScheme objects).
    """
    issues: list[ValidationIssue] = []
    if not isinstance(value, list):
        return [
            _issue(
                ValidationLayer.MCP_STANDARD,
                "RESERVED_META_SECURITY_SCHEMES_INVALID",
                "reserved _meta.securitySchemes must be a list of typed scheme objects",
                path,
            )
        ]
    for i, item in enumerate(value):
        item_path = f"{path}[{i}]"
        if not isinstance(item, dict):
            issues.append(
                _issue(
                    ValidationLayer.MCP_STANDARD,
                    "RESERVED_META_SECURITY_SCHEMES_INVALID",
                    "securitySchemes entries must be objects, not scalars/strings",
                    item_path,
                )
            )
            continue
        if not _json_serializable(item):
            issues.append(
                _issue(
                    ValidationLayer.MCP_STANDARD,
                    "RESERVED_META_SECURITY_SCHEMES_INVALID",
                    "securitySchemes entry is not JSON-serializable",
                    item_path,
                )
            )
    return issues


def _validate_security_scheme_openai_fields(value: Any, path: str) -> list[ValidationIssue]:
    """OpenAI connector needs ``type``/``scopes`` on each scheme object."""
    issues: list[ValidationIssue] = []
    for i, item in enumerate(value if isinstance(value, list) else []):
        if not isinstance(item, dict):
            continue  # already reported by the standard-layer shape check
        item_path = f"{path}[{i}]"
        if item.get("type") != "oauth2":
            issues.append(
                _issue(
                    ValidationLayer.OPENAI_COMPATIBILITY,
                    "OPENAI_SECURITY_SCHEME_TYPE_MISSING",
                    "OpenAI connector expects securitySchemes entries with type='oauth2'",
                    item_path,
                )
            )
        scopes = item.get("scopes")
        if not isinstance(scopes, list) or not all(isinstance(s, str) for s in scopes):
            issues.append(
                _issue(
                    ValidationLayer.OPENAI_COMPATIBILITY,
                    "OPENAI_SECURITY_SCHEME_SCOPES_MISSING",
                    "OpenAI connector expects securitySchemes entries with scopes: list[str]",
                    item_path,
                )
            )
    return issues


def _validate_meta(meta: Any, profile: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(meta, dict):
        return [
            _issue(
                ValidationLayer.MCP_STANDARD,
                "META_NOT_OBJECT",
                "_meta must be an object/map when present",
                "_meta",
            )
        ]
    if not _json_serializable(meta):
        issues.append(
            _issue(
                ValidationLayer.MCP_STANDARD,
                "META_NOT_SERIALIZABLE",
                "_meta is not JSON-serializable",
                "_meta",
            )
        )
    for key, value in meta.items():
        if not isinstance(key, str):
            issues.append(
                _issue(
                    ValidationLayer.MCP_STANDARD,
                    "META_KEY_NOT_STRING",
                    "_meta keys must be strings",
                    "_meta",
                )
            )
            continue
        path = f"_meta.{key}"
        if _is_delpi_namespace(key):
            # DELPI-owned metadata: opaque JSON-serializable value.
            continue
        if _is_namespaced_meta_key(key):
            # Other vendor namespaces are allowed but not DELPI-governed.
            continue
        if key in _RESERVED_META_KEYS:
            issues.extend(_validate_security_scheme_objects(value, path))
            if profile == "openai":
                issues.extend(_validate_security_scheme_openai_fields(value, path))
            continue
        issues.append(
            _issue(
                ValidationLayer.DELPI_POLICY,
                "DELPI_META_UNNAMESPACED_KEY",
                f"bare _meta key '{key}' is not a recognized reserved key; "
                "DELPI metadata must use the delpi/<key> namespace",
                path,
            )
        )
    return issues


def _validate_annotations(annotations: Any) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(annotations, dict):
        return [
            _issue(
                ValidationLayer.MCP_STANDARD,
                "ANNOTATIONS_NOT_OBJECT",
                "annotations must be an object when present",
                "annotations",
            )
        ]
    for key in _ANNOTATION_BOOL_KEYS:
        if key in annotations and not isinstance(annotations[key], bool):
            issues.append(
                _issue(
                    ValidationLayer.MCP_STANDARD,
                    "ANNOTATION_HINT_TYPE_INVALID",
                    f"annotations.{key} must be a boolean",
                    f"annotations.{key}",
                )
            )
    for key in _ANNOTATION_STR_KEYS:
        if key in annotations and not isinstance(annotations[key], str):
            issues.append(
                _issue(
                    ValidationLayer.MCP_STANDARD,
                    "ANNOTATION_TITLE_TYPE_INVALID",
                    f"annotations.{key} must be a string",
                    f"annotations.{key}",
                )
            )
    return issues


def _validate_schema_field(tool: Mapping[str, Any], key: str, *, required: bool) -> list[ValidationIssue]:
    value = tool.get(key)
    if value is None:
        if required:
            return [
                _issue(
                    ValidationLayer.MCP_STANDARD,
                    "TOOL_INPUT_SCHEMA_MISSING",
                    f"{key} is required on the MCP wire",
                    key,
                )
            ]
        return []
    if not isinstance(value, dict) or not _json_serializable(value):
        return [
            _issue(
                ValidationLayer.MCP_STANDARD,
                "TOOL_SCHEMA_INVALID",
                f"{key} must be a JSON-serializable object",
                key,
            )
        ]
    if key == "inputSchema" and value.get("type") not in (None, "object"):
        return [
            _issue(
                ValidationLayer.MCP_STANDARD,
                "TOOL_INPUT_SCHEMA_NOT_OBJECT",
                "inputSchema must declare type 'object'",
                "inputSchema.type",
            )
        ]
    return []


def validate_tool_wire(
    tool: Mapping[str, Any], *, profile: str = "core"
) -> list[ValidationIssue]:
    """Validate one serialized tool definition.

    ``profile``: ``"core"`` (provider-neutral MCP shape) or ``"openai"``
    (core plus checks proven necessary by real ChatGPT/OpenAI incidents).
    """
    if profile not in ("core", "openai"):
        raise ValueError(f"unknown conformance profile: {profile!r}")

    issues: list[ValidationIssue] = []

    if not isinstance(tool, Mapping):
        return [
            _issue(
                ValidationLayer.MCP_STANDARD,
                "TOOL_NOT_OBJECT",
                "tool definition must be a JSON object",
            )
        ]
    if not _json_serializable(dict(tool)):
        issues.append(
            _issue(
                ValidationLayer.MCP_STANDARD,
                "TOOL_NOT_SERIALIZABLE",
                "tool definition does not serialize to JSON",
            )
        )

    name = tool.get("name")
    if not isinstance(name, str) or not name:
        issues.append(
            _issue(
                ValidationLayer.MCP_STANDARD,
                "TOOL_NAME_MISSING",
                "tool name must be a non-empty string",
                "name",
            )
        )
    elif not _TOOL_NAME_RE.match(name):
        issues.append(
            _issue(
                ValidationLayer.MCP_STANDARD,
                "TOOL_NAME_INVALID",
                f"tool name {name!r} is not a valid MCP tool name",
                "name",
            )
        )

    issues.extend(_validate_schema_field(tool, "inputSchema", required=True))
    issues.extend(_validate_schema_field(tool, "outputSchema", required=False))
    if "annotations" in tool:
        issues.extend(_validate_annotations(tool.get("annotations")))
    if "_meta" in tool:
        issues.extend(_validate_meta(tool.get("_meta"), profile))

    for key in tool.keys():
        if key in _SPEC_TOP_LEVEL_KEYS:
            continue
        if profile == "openai" and key in _OPENAI_TOP_LEVEL_KEYS:
            value = tool[key]
            issues.extend(_validate_security_scheme_objects(value, key))
            issues.extend(_validate_security_scheme_openai_fields(value, key))
            continue
        issues.append(
            _issue(
                ValidationLayer.MCP_STANDARD,
                "TOOL_UNKNOWN_TOP_LEVEL_FIELD",
                f"top-level field '{key}' is not part of the MCP Tool spec",
                key,
            )
        )

    return issues


def validate_tools_wire(
    tools: Iterable[Mapping[str, Any]], *, profile: str = "core"
) -> list[ValidationIssue]:
    """Validate a serialized ``tools/list`` payload, including uniqueness."""
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    for tool in tools:
        issues.extend(validate_tool_wire(tool, profile=profile))
        name = tool.get("name") if isinstance(tool, Mapping) else None
        if isinstance(name, str) and name:
            if name in seen:
                issues.append(
                    _issue(
                        ValidationLayer.MCP_STANDARD,
                        "TOOL_NAME_DUPLICATE",
                        f"duplicate tool name {name!r} in tools/list",
                        f"name.{name}",
                    )
                )
            seen.add(name)
    return issues
