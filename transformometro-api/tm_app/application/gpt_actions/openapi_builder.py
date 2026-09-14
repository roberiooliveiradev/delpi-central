"""Build the compact OpenAPI 3 schema for OpenAI Custom GPT Actions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tm_app.application.gpt_actions.entities import (
    GptAnalysisView,
    GptEntity,
    GptMeetingMinuteWorkflow,
)

GPT_ACTIONS_BASE_PATH = "/transformometro/gpt-actions/v1"
GPT_ACTIONS_GATEWAY_ROOT = "/apps/transformometro-api"
# OpenAI Custom GPT rejects relative servers[].url ("Não foi possível encontrar uma URL válida").
GPT_ACTIONS_PUBLIC_FALLBACK_ORIGIN = "https://minhadelpi.com.br"


def resolve_gpt_actions_server_url(
    *,
    public_base_url: str | None = None,
    root_path: str | None = None,
    explicit: str | None = None,
) -> str:
    """Absolute gateway URL for Custom GPT Actions (OpenAI requires https/http origin)."""
    if explicit and str(explicit).startswith(("http://", "https://")):
        return str(explicit).rstrip("/")
    root = (root_path or GPT_ACTIONS_GATEWAY_ROOT).strip() or GPT_ACTIONS_GATEWAY_ROOT
    if not root.startswith("/"):
        root = f"/{root}"
    root = root.rstrip("/") or GPT_ACTIONS_GATEWAY_ROOT
    base = (public_base_url or "").rstrip("/")
    if base.startswith(("http://", "https://")):
        return f"{base}{root}"
    return f"{GPT_ACTIONS_PUBLIC_FALLBACK_ORIGIN}{root}"

GPT_ACTIONS_OPERATION_IDS: tuple[str, ...] = (
    "gpt_get_catalog",
    "gpt_analyze",
    "gpt_search_records",
    "gpt_get_record",
    "gpt_create_record",
    "gpt_update_record",
    "gpt_delete_record",
    "gpt_duplicate_record",
    "gpt_activate_revision",
    "gpt_recalculate_dashboard",
    "gpt_meeting_minute_workflow",
)

# HTTP público para import no GPT Builder — não entra no schema importado.
# O ChatGPT trata GET .../openapi.json como documento OpenAPI 3.1 e rejeita o schema.
GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID = "gpt_get_openapi_schema"

_ENTITY_ENUM = [e.value for e in GptEntity]
_VIEW_ENUM = [v.value for v in GptAnalysisView]
_WORKFLOW_ENUM = [w.value for w in GptMeetingMinuteWorkflow]

# OpenAI Custom GPT: parameter description ≤700 chars, operation description ≤300.
_ENTITY_DESCRIPTION = (
    "Entity slug (see enum). Cadastro: process, instance, revision, measurement, "
    "investment. Catalog: branch, department, shared_resource. Atas: meeting_minute. "
    "Documents: decomposition_tree, process_diagram, impact_effort_matrix and related overlays."
)


def _entity_path_param() -> dict[str, Any]:
    return {
        "name": "entity",
        "in": "path",
        "required": True,
        "schema": {"type": "string", "enum": _ENTITY_ENUM},
        "description": _ENTITY_DESCRIPTION,
    }


def _envelope_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["success", "message", "data"],
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "data": {},
        },
    }


def _ok_response(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {"schema": {"$ref": "#/components/schemas/ApiEnvelope"}}
        },
    }


def _error_responses() -> dict[str, Any]:
    return {
        "400": _ok_response("Validation or domain error"),
        "401": _ok_response("Missing or invalid Bearer token"),
        "403": _ok_response("Authenticated but lacking Transformômetro permission"),
        "404": _ok_response("Record not found"),
    }


def build_gpt_actions_openapi(*, server_url: str | None = None) -> dict[str, Any]:
    """Return OpenAPI 3.0 document with ≤30 operations for Custom GPT import."""
    if not server_url or not str(server_url).startswith(("http://", "https://")):
        server_url = resolve_gpt_actions_server_url(explicit=server_url)
    paths: dict[str, Any] = {
        f"{GPT_ACTIONS_BASE_PATH}/catalog": {
            "get": {
                "operationId": "gpt_get_catalog",
                "summary": "Catalog options for Transformômetro forms",
                "description": (
                    "Returns units (filiais), departments (setores), enums "
                    "(status, cenário, investimento, etc.) and the user's access scope. "
                    "Call this before creating processes or instances."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": _ok_response("Catalog payload"),
                    **_error_responses(),
                },
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/analysis": {
            "get": {
                "operationId": "gpt_analyze",
                "summary": "Analyze dashboard KPIs from snapshot/live cache",
                "description": (
                    "Read-only analytics. Prefer `summary` for totals, `processes` for ranking, "
                    "`instances` for operational improvements, `rows` for revision-level detail, "
                    "`meta` to check cache freshness. Competencies use YYYY-MM."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "view",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string", "enum": _VIEW_ENUM},
                        "description": "Analysis view to return.",
                    },
                    {
                        "name": "filial_id",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Unit code (01, 02).",
                    },
                    {
                        "name": "setor_id",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Department id.",
                    },
                    {
                        "name": "processo_id",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "revisao_id",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "familia_processo",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "competencia_inicio",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string", "pattern": "^\\d{4}-\\d{2}$"},
                        "description": "Start month YYYY-MM.",
                    },
                    {
                        "name": "competencia_fim",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string", "pattern": "^\\d{4}-\\d{2}$"},
                        "description": "End month YYYY-MM.",
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "minimum": 1, "maximum": 500},
                    },
                ],
                "responses": {
                    "200": _ok_response("Analysis payload"),
                    **_error_responses(),
                },
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/records/{'{entity}'}": {
            "get": {
                "operationId": "gpt_search_records",
                "summary": "Search or list records by entity",
                "description": (
                    "List records. Use `parent_id` for children "
                    "(instances of a process, revisions of a process, investments of a revision, "
                    "costs/links of a resource). Use `q` for process text search."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    _entity_path_param(),
                    {"name": "parent_id", "in": "query", "schema": {"type": "string"}},
                    {"name": "filial_id", "in": "query", "schema": {"type": "string"}},
                    {"name": "setor_id", "in": "query", "schema": {"type": "string"}},
                    {"name": "status", "in": "query", "schema": {"type": "string"}},
                    {"name": "familia_processo", "in": "query", "schema": {"type": "string"}},
                    {"name": "q", "in": "query", "schema": {"type": "string"}},
                    {"name": "unit_code", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": _ok_response("List of records"),
                    **_error_responses(),
                },
            },
            "post": {
                "operationId": "gpt_create_record",
                "summary": "Create a Transformômetro record",
                "description": (
                    "Create record. Body `{data:{...}}` matches UI CRUD fields. "
                    "For tree/diagram overlays, put parent id in data "
                    "(processo_id, instancia_id, or revisao_id)."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    _entity_path_param(),
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/GptRecordBody"}
                        }
                    },
                },
                "responses": {
                    "200": _ok_response("Created or upserted record"),
                    "201": _ok_response("Created record"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            },
        },
        f"{GPT_ACTIONS_BASE_PATH}/records/{'{entity}'}/{'{id}'}": {
            "get": {
                "operationId": "gpt_get_record",
                "summary": "Get one record by entity and id",
                "description": (
                    "For measurement, id is revisao_id. "
                    "For decomposition/diagram entities, id is the parent "
                    "(processo_id / instancia_id / revisao_id)."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    _entity_path_param(),
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": _ok_response("Record"),
                    **_error_responses(),
                },
            },
            "put": {
                "operationId": "gpt_update_record",
                "summary": "Update a Transformômetro record",
                "description": "Full/partial update depending on entity. Body: `{ \"data\": { ... } }`.",
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    _entity_path_param(),
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/GptRecordBody"}
                        }
                    },
                },
                "responses": {
                    "200": _ok_response("Updated record"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            },
            "delete": {
                "operationId": "gpt_delete_record",
                "summary": "Soft-delete a Transformômetro record",
                "description": "Destructive. Requires the same manage permissions as the UI.",
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    _entity_path_param(),
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": _ok_response("Deleted"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            },
        },
        f"{GPT_ACTIONS_BASE_PATH}/records/{'{entity}'}/{'{id}'}/duplicate": {
            "post": {
                "operationId": "gpt_duplicate_record",
                "summary": "Duplicate process, instance, or revision",
                "description": "Supported entities: process, instance, revision. Optional body `data` with rename fields.",
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "entity",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "enum": ["process", "instance", "revision"],
                        },
                    },
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/GptRecordBody"}
                        }
                    },
                },
                "responses": {
                    "200": _ok_response("Duplicated record"),
                    "201": _ok_response("Duplicated record"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/revisions/{'{id}'}/activate": {
            "post": {
                "operationId": "gpt_activate_revision",
                "summary": "Activate a revision as the operational current version",
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": _ok_response("Activated revision"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/dashboard/recalculate": {
            "post": {
                "operationId": "gpt_recalculate_dashboard",
                "summary": "Recalculate materialised dashboard cache",
                "description": "Optional filters: revisao_id, processo_id, competencia_inicio, competencia_fim.",
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "revisao_id": {"type": "string"},
                                    "processo_id": {"type": "string"},
                                    "competencia_inicio": {"type": "string"},
                                    "competencia_fim": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": _ok_response("Recalculation result"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/meeting-minutes/{'{id}'}/workflow": {
            "post": {
                "operationId": "gpt_meeting_minute_workflow",
                "summary": "Send, finalize, or cancel a meeting minute",
                "description": (
                    "Workflow actions for atas. Handwritten signature stays in the UI / magic link."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["action"],
                                "properties": {
                                    "action": {
                                        "type": "string",
                                        "enum": _WORKFLOW_ENUM,
                                    },
                                    "reason": {
                                        "type": "string",
                                        "description": "Optional cancel reason.",
                                    },
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": _ok_response("Workflow result"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            }
        },
    }

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Transformômetro API — Custom GPT Actions",
            "description": (
                "Compact facade for OpenAI Custom GPT. Analyzes KPIs and creates/edits "
                "Transformômetro records with the same Keycloak JWT + Core RBAC as the UI. "
                "Do not expose binary uploads, collaboration locks, or public signature signing here."
            ),
            "version": "1.0.0",
        },
        "servers": [
            {"url": server_url, "description": "Minha DELPI gateway"},
        ],
        "tags": [
            {
                "name": "Transformômetro GPT",
                "description": "Custom GPT Actions for analyze / register / edit.",
            }
        ],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": (
                        "Keycloak access token from OAuth Authorization Code "
                        "(client chatgpt-transformometro). Audience must include delpi-central."
                    ),
                }
            },
            "schemas": {
                "ApiEnvelope": _envelope_schema(),
                "GptRecordBody": {
                    "type": "object",
                    "required": ["data"],
                    "properties": {
                        "data": {
                            "type": "object",
                            "description": (
                                "Entity payload. Field names match transformometro-api CRUD "
                                "(nome_processo, filial_id, setor_ids, versao_revisao, "
                                "volume_mensal, unit_code, title, conteudo, etc.)."
                            ),
                            "additionalProperties": True,
                        }
                    },
                },
            },
        },
    }


def write_gpt_actions_openapi(path: Path, *, server_url: str | None = None) -> dict[str, Any]:
    doc = build_gpt_actions_openapi(server_url=server_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def count_operations(doc: dict[str, Any] | None = None) -> int:
    schema = doc or build_gpt_actions_openapi()
    total = 0
    for methods in (schema.get("paths") or {}).values():
        if not isinstance(methods, dict):
            continue
        for method in methods:
            if method.lower() in {"get", "post", "put", "patch", "delete"}:
                total += 1
    return total
