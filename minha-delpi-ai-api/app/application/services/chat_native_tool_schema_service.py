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
                "description": "Ops TvCopilotPatchV1 (upsert_data_source, set_data_transform, upsert_block, bind_visual, add_slide_from_preset, create_playlist).",
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
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": NATIVE_TOOL_PARAMETERS[name],
                    },
                }
            )

        return schemas
