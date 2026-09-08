"""Resolve OpenAPI $ref pointers into materialized schemas for the action catalog."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class OpenApiRefResolver:
    """Materialize local ``#/components/...`` refs. Cycle-safe; leaves external refs intact."""

    @classmethod
    def resolve_document(cls, schema: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(schema, dict):
            raise ValueError("OpenAPI schema must be an object")

        root = deepcopy(schema)
        paths = root.get("paths")
        if not isinstance(paths, dict):
            return root

        for path, path_item in list(paths.items()):
            if not isinstance(path_item, dict):
                continue
            paths[path] = cls._resolve_node(path_item, root, stack=())

        return root

    @classmethod
    def resolve_node(
        cls,
        node: Any,
        root: dict[str, Any],
        *,
        stack: tuple[str, ...] = (),
    ) -> Any:
        return cls._resolve_node(node, root, stack=stack)

    @classmethod
    def _resolve_node(
        cls,
        node: Any,
        root: dict[str, Any],
        *,
        stack: tuple[str, ...],
    ) -> Any:
        if isinstance(node, list):
            return [cls._resolve_node(item, root, stack=stack) for item in node]

        if not isinstance(node, dict):
            return node

        ref = node.get("$ref")
        if isinstance(ref, str) and ref.strip():
            return cls._resolve_ref(ref.strip(), root, stack=stack)

        resolved: dict[str, Any] = {}
        for key, value in node.items():
            resolved[key] = cls._resolve_node(value, root, stack=stack)

        if "allOf" in resolved and isinstance(resolved["allOf"], list):
            merged = cls._merge_all_of(resolved["allOf"])
            extras = {key: value for key, value in resolved.items() if key != "allOf"}
            merged.update(extras)
            return merged

        return resolved

    @classmethod
    def _resolve_ref(
        cls,
        ref: str,
        root: dict[str, Any],
        *,
        stack: tuple[str, ...],
    ) -> Any:
        if not ref.startswith("#/"):
            return {"$ref": ref}

        if ref in stack:
            return {"$ref": ref, "xDelpiUnresolvedCycle": True}

        target = cls._lookup_pointer(root, ref)
        if target is None:
            return {"$ref": ref, "xDelpiUnresolvedRef": True}

        return cls._resolve_node(deepcopy(target), root, stack=stack + (ref,))

    @classmethod
    def _lookup_pointer(cls, root: dict[str, Any], ref: str) -> Any | None:
        parts = ref[2:].split("/")
        current: Any = root
        for part in parts:
            token = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(current, dict) or token not in current:
                return None
            current = current[token]
        return current

    @classmethod
    def _merge_all_of(cls, parts: list[Any]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        properties: dict[str, Any] = {}
        required: list[str] = []

        for part in parts:
            if not isinstance(part, dict):
                continue
            for key, value in part.items():
                if key == "properties" and isinstance(value, dict):
                    properties.update(value)
                    continue
                if key == "required" and isinstance(value, list):
                    for item in value:
                        token = str(item)
                        if token and token not in required:
                            required.append(token)
                    continue
                if key not in merged:
                    merged[key] = value

        if properties:
            merged["properties"] = properties
        if required:
            merged["required"] = required
        return merged
