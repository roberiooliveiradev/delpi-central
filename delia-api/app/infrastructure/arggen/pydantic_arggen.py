"""Pydantic AI structured argument generation (doc 217+ remediation).

Eval-scoped adapter: builds a pydantic-ai Agent whose output_type is
a dynamic model derived from the capability's real JSON Schema —
the model produces typed, schema-constrained arguments instead of
freeform JSON. The orchestrator's existing `_validate_instance`
remains the definitive contract check before any invocation.

No second planner, no MCP execution — intent -> structured args only.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Mapping

from pydantic import create_model
from pydantic_ai import Agent

_logger = logging.getLogger(__name__)

_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict,
    "array": list,
}


def _model_from_schema(schema: Mapping[str, Any]):
    """Dynamic pydantic model mirroring the published JSON Schema."""
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    fields: dict[str, Any] = {}
    for name, spec in props.items():
        if not isinstance(spec, Mapping):
            continue
        py_type = _TYPE_MAP.get(spec.get("type"), str)
        description = spec.get("description")
        if name in required:
            fields[name] = (py_type, ...)
        else:
            default = spec.get("default")
            fields[name] = (
                py_type | None,
                default if default is not None else None,
            )
    return create_model("CapabilityArgs", **fields)


def propose_arguments(
    *,
    objective: str,
    capability_name: str,
    schema: Mapping[str, Any],
    previous_arguments: Mapping[str, Any] | None = None,
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: float = 30.0,
) -> dict:
    """One bounded structured-generation call.

    Returns the model's proposed argument dict — never invokes the
    capability; orchestration validates and decides.
    """
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    args_model = _model_from_schema(schema)
    provider = OpenAIProvider(base_url=base_url, api_key=api_key)
    from pydantic_ai.settings import ModelSettings

    agent = Agent(
        OpenAIChatModel(model, provider=provider),
        model_settings=ModelSettings(max_tokens=2048),
        output_type=args_model,
        # ``instructions=``: delivered on the new ModelRequest even if
        # a history is ever attached — ``system_prompt`` would be
        # silently dropped by pydantic-ai in that case.
        instructions=(
            "You produce arguments for one approved capability call. "
            "Return ONLY the argument values themselves — never "
            "explanations, comments or JSON-encoded strings inside "
            "field values. Map each user-supplied identifier, code or "
            "entity to the semantically matching field declared by "
            "the schema — an exact product code goes to the typed "
            "identifier/code field, free searchable text to the "
            "description field. Omit optional fields you cannot fill "
            "from the objective. Never invent fields or values."
        ),
    )
    prompt_parts = [
        f"Objective: {objective}",
        f"Capability: {capability_name}",
        "Schema fields (name, type, required, description):",
        json.dumps(
            {
                k: {
                    "type": v.get("type"),
                    "required": k in set(schema.get("required") or []),
                    "description": v.get("description"),
                }
                for k, v in (schema.get("properties") or {}).items()
                if isinstance(v, Mapping)
            },
            ensure_ascii=False,
        ),
    ]
    if previous_arguments:
        prompt_parts.append(
            "Previous arguments that produced an inadequate result: "
            + json.dumps(previous_arguments, ensure_ascii=False)
        )
    result = agent.run_sync("\n".join(prompt_parts))
    data = (
        result.output
        if hasattr(result, "output")
        else getattr(result, "data", None)
    )
    if data is None:
        return {}
    if hasattr(data, "model_dump"):
        payload = data.model_dump()
    elif isinstance(data, Mapping):
        payload = dict(data)
    else:
        return {}
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            continue
        # Deterministic unwrap: a field value that is itself a
        # single-key JSON object string naming the same field unwraps
        # to the inner value (model-side double-serialization).
        if isinstance(value, str):
            try:
                inner = json.loads(value)
            except Exception:
                inner = None
            if (
                isinstance(inner, dict)
                and len(inner) == 1
                and key in inner
            ):
                value = inner[key]
        out[key] = value
    return out
