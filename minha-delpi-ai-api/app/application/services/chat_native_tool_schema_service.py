from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.domain.ports.internal_tool_port import InternalToolPort

NATIVE_TOOL_PARAMETERS: dict[str, dict] = {
    "get_current_user": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "get_allowed_apps": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "get_allowed_routes": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "search_knowledge_base": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Texto da busca na base documental."},
            "limit": {
                "type": "integer",
                "description": "Máximo de trechos (1 a 5).",
                "minimum": 1,
                "maximum": 5,
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    "web_search": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Consulta pública na internet."},
            "limit": {
                "type": "integer",
                "description": "Máximo de resultados (1 a 8).",
                "minimum": 1,
                "maximum": 8,
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    "tv_dashboard_copilot": {
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "description": "preview (dry-run) ou apply (persiste; exige confirmação).",
                "enum": ["preview", "apply"],
            },
            "target": {
                "type": "object",
                "description": "playlistId e slideId do editor TV.",
                "properties": {
                    "playlistId": {"type": "string"},
                    "slideId": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "ops": {
                "type": "array",
                "description": (
                    "Ops TvCopilotPatchV1 do catálogo do BFF TV "
                    "(GET /data/copilot/capabilities). Não invente op fora do catálogo."
                ),
                "items": {"type": "object", "additionalProperties": True},
            },
            "includeFingerprint": {
                "type": "boolean",
                "description": "Só em preview: incluir fingerprint via SlideDataResolution.",
            },
        },
        "required": ["mode", "ops"],
        "additionalProperties": False,
    },
}


class ChatNativeToolSchemaService:
    def build_openai_tools(
        self,
        *,
        allowed_tool_names: list[str] | None,
        tools_registry: dict[str, InternalToolPort],
        tv_capability_catalog: dict[str, Any] | None = None,
    ) -> list[dict]:
        allowed = {
            str(name).strip()
            for name in (allowed_tool_names or tools_registry.keys())
            if str(name).strip()
        }

        schemas: list[dict] = []

        for name in sorted(allowed):
            if name not in tools_registry or name not in NATIVE_TOOL_PARAMETERS:
                continue

            tool = tools_registry[name]
            parameters = deepcopy(NATIVE_TOOL_PARAMETERS[name])
            description = tool.description
            if name == "tv_dashboard_copilot":
                parameters, description = self._enrich_tv_dashboard_schema(
                    parameters,
                    description,
                    tv_capability_catalog,
                )
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": description,
                        "parameters": parameters,
                    },
                }
            )

        return schemas

    @staticmethod
    def _enrich_tv_dashboard_schema(
        parameters: dict[str, Any],
        description: str,
        catalog: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], str]:
        """Injeta ops/whenToUse do catálogo BFF no schema native (AP8 fase 5)."""
        if not isinstance(catalog, dict):
            return parameters, description

        capabilities = catalog.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities:
            return parameters, description

        op_names: list[str] = []
        when_lines: list[str] = []
        for item in capabilities:
            if not isinstance(item, dict):
                continue
            op = str(item.get("op") or "").strip()
            if op and op not in op_names:
                op_names.append(op)
            when = str(item.get("whenToUse") or "").strip()
            key = str(item.get("key") or op).strip()
            if when:
                when_lines.append(f"- {key} ({op}): {when}")

        version = str(catalog.get("catalogVersion") or "").strip()
        desc_parts = [description.strip()]
        if version:
            desc_parts.append(f"Catálogo TV version={version}.")
        if when_lines:
            desc_parts.append("Quando usar cada op:\n" + "\n".join(when_lines[:20]))

        ops_prop = (parameters.get("properties") or {}).get("ops")
        if isinstance(ops_prop, dict) and op_names:
            ops_prop["description"] = (
                "Ops TvCopilotPatchV1 permitidas neste catálogo: "
                + ", ".join(op_names)
                + "."
            )

        return parameters, "\n".join(desc_parts)
