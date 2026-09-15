"""Validate Copilot op payloads against canonical operation inputSchema.

The published JSON Schema in ``tv_copilot_content.json`` is the single
authority. This module implements a focused subset (type/required/enum/const/
items/oneOf/additionalProperties) so runtime 4xx matches the GPT projection.
"""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)

class NestedContractError(ValueError):
    """Payload does not match the canonical operation inputSchema."""


def validate_operation_payload(op_name: str, raw_op: dict[str, Any]) -> None:
    spec = TvCopilotContentService.operation_spec(op_name)
    schema = spec.get("inputSchema") if isinstance(spec, dict) else None
    if not isinstance(schema, dict):
        return
    _validate(raw_op, schema, path=op_name, op_name=op_name)


def _validate(instance: Any, schema: dict[str, Any], *, path: str, op_name: str) -> None:
    if "const" in schema and instance != schema["const"]:
        _fail(op_name, f"{path} deve ser {schema['const']!r}")

    enum = schema.get("enum")
    if isinstance(enum, list) and instance not in enum:
        _fail(op_name, f"{path} deve ser um de {enum!r}")

    declared = schema.get("type")
    types = declared if isinstance(declared, list) else [declared] if declared else []
    types = [str(item) for item in types if item]

    if types and not _matches_type(instance, types):
        _fail(op_name, f"{path} deve ser {'/'.join(types)}")

    if instance is None:
        return

    one_of = schema.get("oneOf")
    if isinstance(one_of, list) and one_of:
        errors: list[str] = []
        for branch in one_of:
            if not isinstance(branch, dict):
                continue
            try:
                _validate(instance, branch, path=path, op_name=op_name)
                break
            except NestedContractError as exc:
                errors.append(str(exc))
        else:
            if path.endswith(".steps") or path.endswith("/items") or "steps" in path:
                step_op = ""
                if isinstance(instance, dict):
                    step_op = str(instance.get("op") or "").strip()
                if step_op:
                    raise NestedContractError(
                        TvCopilotContentService.message(
                            "transformStepUnknown",
                            stepOp=step_op,
                        )
                    )
            _fail(op_name, f"{path} não corresponde a nenhuma variante tipada")
        return

    if "object" in types or (not types and isinstance(schema.get("properties"), dict)):
        if not isinstance(instance, dict):
            _fail(op_name, f"{path} deve ser objeto")
        required = schema.get("required")
        if isinstance(required, list):
            for field in required:
                key = str(field or "").strip()
                if not key:
                    continue
                if key not in instance:
                    _fail(op_name, f"{path}.{key} é obrigatório")
                value = instance.get(key)
                if isinstance(value, str) and not value.strip() and key != "op":
                    _fail(op_name, f"{path}.{key} é obrigatório")
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        additional = schema.get("additionalProperties")
        for key, value in instance.items():
            if key in properties and isinstance(properties[key], dict):
                _validate(value, properties[key], path=f"{path}.{key}", op_name=op_name)
                continue
            if additional is False:
                _fail(op_name, f"{path} não aceita o campo «{key}»")
            if isinstance(additional, dict):
                _validate(value, additional, path=f"{path}.{key}", op_name=op_name)
        min_props = schema.get("minProperties")
        if isinstance(min_props, int) and len(instance) < min_props:
            _fail(op_name, f"{path} não pode ser vazio")

    if "array" in types:
        if not isinstance(instance, list):
            _fail(op_name, f"{path} deve ser array")
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(instance) < min_items:
            _fail(op_name, f"{path} exige ao menos {min_items} item(ns)")
        items = schema.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(instance):
                _validate(item, items, path=f"{path}[{index}]", op_name=op_name)

    if "integer" in types and isinstance(instance, bool):
        _fail(op_name, f"{path} deve ser integer")
    minimum = schema.get("minimum")
    if isinstance(minimum, (int, float)) and isinstance(instance, (int, float)) and not isinstance(
        instance, bool
    ):
        if instance < minimum:
            _fail(op_name, f"{path} deve ser ≥ {minimum}")


def _matches_type(instance: Any, types: list[str]) -> bool:
    for declared in types:
        if declared == "null" and instance is None:
            return True
        if declared == "object" and isinstance(instance, dict):
            return True
        if declared == "array" and isinstance(instance, list):
            return True
        if declared == "string" and isinstance(instance, str):
            return True
        if declared == "boolean" and isinstance(instance, bool):
            return True
        if declared == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
            return True
        if declared == "number" and isinstance(instance, (int, float)) and not isinstance(
            instance, bool
        ):
            return True
    return False


def _fail(op_name: str, reason: str) -> None:
    raise NestedContractError(
        TvCopilotContentService.message(
            "nestedSchemaInvalid",
            op=op_name,
            reason=reason,
        )
    )


def patch_native_keys() -> frozenset[str]:
    spec = TvCopilotContentService.operation_spec("patch_native_config") or {}
    schema = spec.get("inputSchema") if isinstance(spec, dict) else {}
    patch = ((schema or {}).get("properties") or {}).get("patch")
    props = (patch or {}).get("properties") if isinstance(patch, dict) else {}
    if isinstance(props, dict) and props:
        return frozenset(str(key) for key in props)
    return frozenset({"background", "dataFilters", "speakerNotes", "groupTransforms"})
