"""Schemas OpenAPI enxutos para o planner agentic (Onda 11.3.2)."""

from __future__ import annotations

import json
import re
from typing import Any

from app.domain.services.chat_domain_config_service import ChatDomainConfigService


class ChatAgenticActionSchemaService:
    _DESCRIPTION_MAX_CHARS = 220
    _PARAM_DESCRIPTION_MAX_CHARS = 120
    _MAX_PARAMETERS = 10

    _PARAM_EXAMPLES: dict[str, Any] = {
        "code": "10080022",
        "branch": "01",
        "warehouse": "01",
        "page": 1,
        "page_size": 50,
        "top_limit": 10,
        "granularity": "month",
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
        "date_start": "2026-03-01",
        "date_end": "2026-03-31",
        "sale_number": "12345",
        "query": "parafuso",
        "description": "TERMINAL FASTON",
        "table_name": "products",
        "tableName": "products",
    }

    @classmethod
    def build_slim_action(cls, action: dict[str, Any]) -> dict[str, Any]:
        action_id = str(action.get("actionId") or "").strip()

        if not action_id:
            return {}

        parameters = cls._build_slim_parameters(action)
        example_arguments = cls._build_example_arguments(parameters)

        return {
            "actionId": action_id,
            "method": str(action.get("method") or "GET").upper(),
            "path": str(action.get("path") or "").strip(),
            "description": cls._build_description(action),
            "parameters": parameters,
            "exampleArguments": example_arguments,
        }

    @classmethod
    def format_planner_catalog(cls, entries: list[dict[str, Any]]) -> str:
        if not entries:
            return "[]"

        return json.dumps(entries, ensure_ascii=False, indent=2)

    @classmethod
    def _build_description(cls, action: dict[str, Any]) -> str:
        summary = cls._optional_text(action.get("summary"))
        description = cls._optional_text(action.get("description"))

        if summary and description and description.lower() != summary.lower():
            merged = f"{summary}. {description}"
        else:
            merged = summary or description or str(action.get("path") or action.get("actionId") or "")

        return cls._truncate(merged, cls._DESCRIPTION_MAX_CHARS)

    @classmethod
    def _build_slim_parameters(cls, action: dict[str, Any]) -> list[dict[str, Any]]:
        raw_parameters = action.get("parametersSchema") or action.get("parameters_schema") or []

        if not isinstance(raw_parameters, list):
            return []

        slim: list[dict[str, Any]] = []

        for parameter in raw_parameters:
            if not isinstance(parameter, dict):
                continue

            name = str(parameter.get("name") or "").strip()

            if not name:
                continue

            entry: dict[str, Any] = {
                "name": name,
                "in": str(parameter.get("in") or "query").strip() or "query",
                "required": bool(parameter.get("required")),
                "type": cls._resolve_parameter_type(parameter),
            }

            description = cls._optional_text(parameter.get("description"))

            if description:
                entry["description"] = cls._truncate(
                    description,
                    cls._PARAM_DESCRIPTION_MAX_CHARS,
                )

            example = cls._resolve_parameter_example(parameter, name)

            if example is not None:
                entry["example"] = example

            slim.append(entry)

            if len(slim) >= cls._max_parameters():
                break

        return slim

    @classmethod
    def _build_example_arguments(cls, parameters: list[dict[str, Any]]) -> dict[str, Any]:
        parameters_payload: dict[str, Any] = {}
        body_payload: dict[str, Any] | None = None

        for parameter in parameters:
            if "example" not in parameter:
                continue

            location = str(parameter.get("in") or "query").lower()
            name = str(parameter.get("name") or "").strip()
            value = parameter["example"]

            if location in {"path", "query", "header", "cookie"}:
                parameters_payload[name] = value
            elif location == "body":
                if body_payload is None:
                    body_payload = {}
                body_payload[name] = value

        arguments: dict[str, Any] = {}

        if parameters_payload:
            arguments["parameters"] = parameters_payload

        if body_payload:
            arguments["body"] = body_payload

        return arguments

    @classmethod
    def _resolve_parameter_type(cls, parameter: dict[str, Any]) -> str:
        schema = parameter.get("schema")

        if isinstance(schema, dict):
            schema_type = schema.get("type")

            if isinstance(schema_type, str) and schema_type.strip():
                return schema_type.strip()

        param_type = parameter.get("type")

        if isinstance(param_type, str) and param_type.strip():
            return param_type.strip()

        return "string"

    @classmethod
    def _resolve_parameter_example(cls, parameter: dict[str, Any], name: str) -> Any:
        if parameter.get("example") is not None:
            return parameter.get("example")

        examples = parameter.get("examples")

        if isinstance(examples, dict):
            for item in examples.values():
                if isinstance(item, dict) and item.get("value") is not None:
                    return item.get("value")

        if isinstance(examples, list):
            for item in examples:
                if item is not None:
                    return item

        schema = parameter.get("schema")

        if isinstance(schema, dict):
            if schema.get("example") is not None:
                return schema.get("example")

            if schema.get("default") is not None:
                return schema.get("default")

        if parameter.get("default") is not None:
            return parameter.get("default")

        normalized_name = name.strip().lower()

        if normalized_name in cls._PARAM_EXAMPLES:
            return cls._PARAM_EXAMPLES[normalized_name]

        snake_name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()

        if snake_name in cls._PARAM_EXAMPLES:
            return cls._PARAM_EXAMPLES[snake_name]

        return None

    @classmethod
    def _max_parameters(cls) -> int:
        configured = ChatDomainConfigService.chat_agentic_schema_max_parameters()

        try:
            return max(1, min(int(configured), 20))
        except (TypeError, ValueError):
            return cls._MAX_PARAMETERS

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None

        normalized = re.sub(r"\s+", " ", str(value).strip())

        return normalized or None

    @staticmethod
    def _truncate(value: str, max_chars: int) -> str:
        text = str(value or "").strip()

        if len(text) <= max_chars:
            return text

        clipped = text[: max_chars - 1].rsplit(" ", 1)[0].strip()

        return f"{clipped or text[: max_chars - 1]}…"
