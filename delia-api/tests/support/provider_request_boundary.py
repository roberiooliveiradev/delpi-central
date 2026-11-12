"""INT-1 provider-request boundary capture — B1/B2/B3 fingerprints.

Supported capture path (pydantic-ai 2.50): the last framework-stable
boundary before provider-specific HTTP serialization is
``ModelRequestParameters.declared_function_tools`` after
``prepare_request``. Two equivalent observers:

* ``FunctionModel`` → ``AgentInfo.function_tools`` (deterministic tests)
* ``WrapperModel.request`` MRP on the live OpenAI-compatible path

```text
B1 = owner MCP tools/list
B2 = DÉLIA composed toolset (rename + EnvelopeHint)
B3 = provider request boundary (declared_function_tools)
```

HTTP wire bytes are intentionally out of scope unless a supported
non-egress HTTP capture exists — document ``HTTP_WIRE_BYTES=NOT_OBSERVED``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence


CAPTURE_MECHANISM = (
    "pydantic_ai ModelRequestParameters.declared_function_tools "
    "after prepare_request "
    "(FunctionModel AgentInfo.function_tools | WrapperModel.request MRP)"
)
CAPTURE_BOUNDARY_B3 = "pydantic_ai_provider_request_pre_http"
PYDANTIC_AI_PROVIDER_BOUNDARY = "PROVEN"
HTTP_WIRE_BYTES = "NOT_OBSERVED"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tool_fingerprint(
    *,
    name: str,
    description: str | None,
    parameters_json_schema: Mapping[str, Any] | None,
    tool_kind: str | None = None,
    order: int | None = None,
) -> dict[str, Any]:
    """Structured fingerprint for one tool at a boundary."""
    desc = description or ""
    schema = dict(parameters_json_schema or {})
    props = schema.get("properties") if isinstance(schema, Mapping) else None
    prop_count = len(props) if isinstance(props, Mapping) else 0
    required = schema.get("required") if isinstance(schema, Mapping) else None
    if not isinstance(required, list):
        required = []
    lowered = desc.lower()
    return {
        "name": name,
        "description": desc,
        "description_length": len(desc),
        "description_sha256": _sha256_text(desc),
        "parameters_json_schema": schema,
        "schema_sha256": _sha256_text(_stable_json(schema)),
        "schema_property_count": prop_count,
        "required_fields": list(required),
        "tool_kind": tool_kind,
        "tool_order": order,
        "description_has_process_wbs": (
            "wbs" in lowered and "process" in lowered
        ),
        "description_has_bom_negative": (
            "bill-of-materials" in lowered
            or "materials/product" in lowered
        ),
        "description_mentions_get_product_structure": (
            "get_product_structure" in lowered
        ),
    }


def fingerprint_from_tool_definition(
    tool_def: Any, *, order: int | None = None
) -> dict[str, Any]:
    return tool_fingerprint(
        name=str(getattr(tool_def, "name", "") or ""),
        description=getattr(tool_def, "description", None),
        parameters_json_schema=getattr(
            tool_def, "parameters_json_schema", None
        ),
        tool_kind=str(getattr(tool_def, "kind", None) or "") or None,
        order=order,
    )


def fingerprint_from_mcp_tool(
    tool: Any, *, order: int | None = None, name_prefix: str = ""
) -> dict[str, Any]:
    remote = str(getattr(tool, "name", "") or "")
    name = f"{name_prefix}{remote}" if name_prefix else remote
    schema = getattr(tool, "input_schema", None)
    if schema is None:
        schema = getattr(tool, "inputSchema", None)
    return tool_fingerprint(
        name=name,
        description=getattr(tool, "description", None),
        parameters_json_schema=schema if isinstance(schema, Mapping) else {},
        tool_kind="mcp",
        order=order,
    )


def fingerprint_from_catalog_entry(
    entry: Mapping[str, Any], *, order: int | None = None
) -> dict[str, Any]:
    return tool_fingerprint(
        name=str(entry.get("capability_id") or entry.get("name") or ""),
        description=str(entry.get("description") or ""),
        parameters_json_schema=(
            entry.get("input_schema")
            if isinstance(entry.get("input_schema"), Mapping)
            else {}
        ),
        tool_kind="catalog_projection",
        order=order,
    )


def boundary_snapshot(
    *,
    boundary: str,
    tools: Sequence[Mapping[str, Any]],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ordered = list(tools)
    snap: dict[str, Any] = {
        "boundary": boundary,
        "tool_count": len(ordered),
        "tool_order": [t.get("name") for t in ordered],
        "tools": ordered,
        "tools_by_name": {t["name"]: t for t in ordered if t.get("name")},
    }
    if extra:
        snap.update(dict(extra))
    return snap


def request_fingerprint(capture: Mapping[str, Any]) -> str:
    """Stable fingerprint of tools + instructions + user prompt."""
    payload = {
        "tool_order": capture.get("tool_order"),
        "tool_shas": [
            {
                "name": t.get("name"),
                "description_sha256": t.get("description_sha256"),
                "schema_sha256": t.get("schema_sha256"),
            }
            for t in (capture.get("tools") or [])
        ],
        "agent_instructions_sha256": _sha256_text(
            str(capture.get("agent_instructions") or "")
        ),
        "user_prompt_sha256": _sha256_text(
            str(capture.get("user_prompt") or "")
        ),
        "model_request_parameters": capture.get("model_request_parameters"),
        "tool_choice_policy": capture.get("tool_choice_policy"),
    }
    return _sha256_text(_stable_json(payload))[:16]


def _messages_user_and_system(
    messages: Sequence[Any] | None,
) -> tuple[str | None, list[str]]:
    user_prompt = None
    system_from_messages: list[str] = []
    if not messages:
        return user_prompt, system_from_messages
    from pydantic_ai.messages import SystemPromptPart, UserPromptPart

    for msg in messages:
        parts = getattr(msg, "parts", None) or ()
        for part in parts:
            if isinstance(part, UserPromptPart) and user_prompt is None:
                user_prompt = str(getattr(part, "content", "") or "")
            if isinstance(part, SystemPromptPart):
                system_from_messages.append(
                    str(getattr(part, "content", "") or "")
                )
    return user_prompt, system_from_messages


def _mrp_summary(mrp: Any) -> dict[str, Any]:
    if mrp is None:
        return {}
    return {
        "allow_text_output": getattr(mrp, "allow_text_output", None),
        "allow_image_output": getattr(mrp, "allow_image_output", None),
        "output_mode": str(getattr(mrp, "output_mode", None) or "") or None,
        "function_tool_count": len(getattr(mrp, "function_tools", ()) or ()),
        "declared_function_tool_count": len(
            getattr(mrp, "declared_function_tools", ()) or ()
        ),
        "output_tool_names": [
            getattr(t, "name", None)
            for t in (getattr(mrp, "output_tools", None) or ())
        ],
        "has_tool_choice_field": hasattr(mrp, "tool_choice"),
        "tool_choice": getattr(mrp, "tool_choice", None),
    }


def _instructions_from_mrp(mrp: Any) -> str | None:
    parts = getattr(mrp, "instruction_parts", None) if mrp is not None else None
    if not parts:
        return None
    texts: list[str] = []
    for part in parts:
        content = getattr(part, "content", None)
        if content is None and isinstance(part, Mapping):
            content = part.get("content")
        if content:
            texts.append(str(content))
    return "\n".join(texts) if texts else None


def capture_b3_from_model_request_parameters(
    mrp: Any,
    messages: Sequence[Any] | None = None,
    *,
    agent_instructions: str | None = None,
) -> dict[str, Any]:
    """Capture B3 from prepared ``ModelRequestParameters`` (no HTTP)."""
    declared = list(getattr(mrp, "declared_function_tools", None) or ())
    if not declared:
        declared = list(getattr(mrp, "function_tools", None) or ())
    tools = [
        fingerprint_from_tool_definition(td, order=i)
        for i, td in enumerate(declared)
    ]
    user_prompt, system_from_messages = _messages_user_and_system(messages)
    mrp_summary = _mrp_summary(mrp)
    instructions = agent_instructions
    if instructions is None:
        instructions = _instructions_from_mrp(mrp)
    if instructions is None and system_from_messages:
        instructions = "\n".join(system_from_messages)
    snap = boundary_snapshot(
        boundary=CAPTURE_BOUNDARY_B3,
        tools=tools,
        extra={
            "capture_mechanism": CAPTURE_MECHANISM,
            "pydantic_ai_provider_boundary": PYDANTIC_AI_PROVIDER_BOUNDARY,
            "http_wire_bytes": HTTP_WIRE_BYTES,
            "agent_instructions": instructions,
            "system_prompt_parts": system_from_messages,
            "user_prompt": user_prompt,
            "model_request_parameters": mrp_summary,
            "tool_choice_policy": (
                "UNFORCED"
                if not mrp_summary.get("tool_choice")
                else str(mrp_summary.get("tool_choice"))
            ),
        },
    )
    snap["request_fingerprint"] = request_fingerprint(snap)
    return snap


def capture_b3_from_agent_info(
    info: Any,
    messages: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Capture B3 from FunctionModel ``AgentInfo`` (no HTTP)."""
    function_tools = list(getattr(info, "function_tools", None) or ())
    tools = [
        fingerprint_from_tool_definition(td, order=i)
        for i, td in enumerate(function_tools)
    ]
    mrp = getattr(info, "model_request_parameters", None)
    mrp_summary = _mrp_summary(mrp)
    user_prompt, system_from_messages = _messages_user_and_system(messages)
    instructions = getattr(info, "instructions", None)
    snap = boundary_snapshot(
        boundary=CAPTURE_BOUNDARY_B3,
        tools=tools,
        extra={
            "capture_mechanism": CAPTURE_MECHANISM,
            "pydantic_ai_provider_boundary": PYDANTIC_AI_PROVIDER_BOUNDARY,
            "http_wire_bytes": HTTP_WIRE_BYTES,
            "agent_instructions": instructions,
            "system_prompt_parts": system_from_messages,
            "user_prompt": user_prompt,
            "model_request_parameters": mrp_summary,
            "tool_choice_policy": (
                "UNFORCED"
                if not mrp_summary.get("tool_choice")
                else str(mrp_summary.get("tool_choice"))
            ),
        },
    )
    snap["request_fingerprint"] = request_fingerprint(snap)
    return snap


def public_b3_summary(capture: Mapping[str, Any]) -> dict[str, Any]:
    """Trace-safe summary: fingerprints + integrity flags, not full prose."""
    tools_public = []
    for t in capture.get("tools") or []:
        tools_public.append(
            {
                "name": t.get("name"),
                "description_length": t.get("description_length"),
                "description_sha256": t.get("description_sha256"),
                "schema_sha256": t.get("schema_sha256"),
                "schema_property_count": t.get("schema_property_count"),
                "required_fields": t.get("required_fields"),
                "tool_order": t.get("tool_order"),
                "description_has_process_wbs": t.get(
                    "description_has_process_wbs"
                ),
                "description_has_bom_negative": t.get(
                    "description_has_bom_negative"
                ),
                "description_mentions_get_product_structure": t.get(
                    "description_mentions_get_product_structure"
                ),
            }
        )
    instructions = str(capture.get("agent_instructions") or "")
    return {
        "boundary": capture.get("boundary"),
        "capture_mechanism": capture.get("capture_mechanism"),
        "pydantic_ai_provider_boundary": capture.get(
            "pydantic_ai_provider_boundary"
        ),
        "http_wire_bytes": capture.get("http_wire_bytes"),
        "tool_count": capture.get("tool_count"),
        "tool_order": capture.get("tool_order"),
        "tools": tools_public,
        "tool_choice_policy": capture.get("tool_choice_policy"),
        "model_request_parameters": capture.get("model_request_parameters"),
        "user_prompt": capture.get("user_prompt"),
        "agent_instructions_sha256": _sha256_text(instructions),
        "agent_instructions_length": len(instructions),
        "request_fingerprint": capture.get("request_fingerprint")
        or request_fingerprint(capture),
    }


def compare_tool_pair(
    left: Mapping[str, Any] | None,
    right: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if left is None or right is None:
        return {
            "present_left": left is not None,
            "present_right": right is not None,
            "name_equal": False,
            "description_prefix_preserved": False,
            "schema_equal": False,
            "description_length_delta": None,
        }
    left_desc = str(left.get("description") or "")
    right_desc = str(right.get("description") or "")
    prefix_ok = right_desc.startswith(left_desc) if left_desc else True
    return {
        "present_left": True,
        "present_right": True,
        "name_equal": left.get("name") == right.get("name"),
        "description_sha_equal": (
            left.get("description_sha256") == right.get("description_sha256")
        ),
        "description_prefix_preserved": prefix_ok,
        "schema_equal": left.get("schema_sha256") == right.get("schema_sha256"),
        "description_length_delta": (
            int(right.get("description_length") or 0)
            - int(left.get("description_length") or 0)
        ),
        "required_fields_equal": (
            list(left.get("required_fields") or [])
            == list(right.get("required_fields") or [])
        ),
        "wbs_left": bool(left.get("description_has_process_wbs")),
        "wbs_right": bool(right.get("description_has_process_wbs")),
        "bom_neg_left": bool(left.get("description_has_bom_negative")),
        "bom_neg_right": bool(right.get("description_has_bom_negative")),
        "gps_left": bool(
            left.get("description_mentions_get_product_structure")
        ),
        "gps_right": bool(
            right.get("description_mentions_get_product_structure")
        ),
    }


def compare_boundaries(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    names: Iterable[str] | None = None,
) -> dict[str, Any]:
    left_by = left.get("tools_by_name") or {}
    right_by = right.get("tools_by_name") or {}
    selected = list(names) if names is not None else sorted(
        set(left_by) | set(right_by)
    )
    per_tool = {
        name: compare_tool_pair(left_by.get(name), right_by.get(name))
        for name in selected
    }
    return {
        "left_boundary": left.get("boundary"),
        "right_boundary": right.get("boundary"),
        "left_tool_count": left.get("tool_count"),
        "right_tool_count": right.get("tool_count"),
        "names_only_left": sorted(set(left_by) - set(right_by)),
        "names_only_right": sorted(set(right_by) - set(left_by)),
        "per_tool": per_tool,
    }
