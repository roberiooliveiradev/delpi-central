"""Extensão x-delpi em operações OpenAPI — Playbook 22 Fase D."""

from __future__ import annotations

from typing import Any

HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})


class OpenApiDelpiExtensionService:
    EXTENSION_KEYS: tuple[str, ...] = ("x-delpi", "xDelpi", "x_delpi")

    @classmethod
    def extract_raw(cls, operation: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(operation, dict):
            return None

        for key in cls.EXTENSION_KEYS:
            raw = operation.get(key)

            if isinstance(raw, dict):
                return raw

        return None

    @classmethod
    def normalize(cls, raw: dict[str, Any]) -> dict[str, Any]:
        entity = str(raw.get("entity") or "").strip() or None
        shape = str(raw.get("shape") or "").strip() or None
        presentation = raw.get("presentation")
        pres = dict(presentation) if isinstance(presentation, dict) else {}

        normalized: dict[str, Any] = {}

        if entity:
            normalized["entity"] = entity

        if shape:
            normalized["shape"] = shape

        if pres:
            normalized["presentation"] = pres

        return normalized

    @classmethod
    def extract_from_operation(cls, operation: dict[str, Any]) -> dict[str, Any] | None:
        raw = cls.extract_raw(operation)

        if raw:
            normalized = cls.normalize(raw)

            return normalized if normalized else None

        return cls.infer_from_response_example(operation)

    @classmethod
    def infer_from_response_example(cls, operation: dict[str, Any]) -> dict[str, Any] | None:
        responses = operation.get("responses")

        if not isinstance(responses, dict):
            return None

        ok = responses.get("200") or responses.get("201")

        if not isinstance(ok, dict):
            return None

        content = ok.get("content")

        if not isinstance(content, dict):
            return None

        json_content = content.get("application/json")

        if not isinstance(json_content, dict):
            return None

        example = json_content.get("example")

        if not isinstance(example, dict):
            return None

        meta = example.get("meta")

        if not isinstance(meta, dict):
            return None

        normalized = cls.normalize(meta)

        return normalized if normalized else None

    @classmethod
    def summarize_schema_coverage(cls, schema: dict[str, Any]) -> dict[str, int]:
        paths = schema.get("paths")

        if not isinstance(paths, dict):
            return {"operations": 0, "withDelpiMetadata": 0}

        operations = 0
        with_delpi = 0

        for path_item in paths.values():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                    continue

                operations += 1

                if cls.extract_from_operation(operation):
                    with_delpi += 1

        return {
            "operations": operations,
            "withDelpiMetadata": with_delpi,
        }
