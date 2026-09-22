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
from tm_app.application.methodology.guide import list_method_ids, list_task_ids
from tm_app.application.gpt_actions.improvement_package_contract import (
    NESTING_RULES,
    openapi_investment_properties,
    openapi_measurement_properties,
    openapi_revision_properties,
)
from tm_app.application.gpt_actions.record_write_contract import (
    openapi_record_data_properties,
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
    "gpt_get_my_context",
    "gpt_get_catalog",
    "gpt_get_methodology_guide",
    "gpt_analyze",
    "gpt_search_records",
    "gpt_get_record",
    "gpt_prepare_record_change",
    "gpt_commit_proposal",
    "gpt_activate_revision",
    "gpt_recalculate_dashboard",
    "gpt_meeting_minute_workflow",
    "gpt_validate_improvement_package",
    "gpt_get_process_context",
    "gpt_list_evidence",
    "gpt_manage_evidence",
    "gpt_get_process_timeline",
    "gpt_adjust_shared_resource_cost",
    "gpt_meeting_minute_manage",
)

# Legacy HTTP still mounted (prepare-only shim) — not Builder-importable.
GPT_ACTIONS_LEGACY_OPERATION_IDS: tuple[str, ...] = (
    "gpt_create_record",
    "gpt_update_record",
    "gpt_delete_record",
    "gpt_duplicate_record",
    "gpt_commit_improvement_package",
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
    "Process knowledge (Markdown): process_document. "
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
        "description": (
            "Canonical API envelope. On errors ALWAYS read message and data.errors — "
            "never report only the HTTP status code to the user."
        ),
        "properties": {
            "success": {"type": "boolean"},
            "message": {
                "type": "string",
                "description": (
                    "Human-readable outcome or validation summary "
                    "(e.g. missing required fields)."
                ),
            },
            "data": {
                "description": (
                    "Payload on success, or structured error details "
                    "(often {errors:[{field,reason}], error_count})."
                ),
            },
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
        "400": {
            "description": (
                "Validation or domain error. Body is ApiEnvelope with success=false; "
                "read message + data.errors (do not show only HTTP 400)."
            ),
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ApiEnvelope"},
                    "example": {
                        "success": False,
                        "message": (
                            "Campos obrigatórios ausentes: nome_recurso, tipo_custo, "
                            "recorrencia"
                        ),
                        "data": {
                            "error_count": 3,
                            "errors": [
                                {"field": "nome_recurso", "reason": "Field required"},
                                {"field": "tipo_custo", "reason": "Field required"},
                                {"field": "recorrencia", "reason": "Field required"},
                            ],
                        },
                    },
                }
            },
        },
        "401": {
            "description": (
                "Missing/invalid Bearer. ApiEnvelope message explains AuthN; "
                "read message (not only HTTP 401)."
            ),
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ApiEnvelope"},
                    "example": {
                        "success": False,
                        "message": "Unauthorized",
                        "data": {"error_kind": "authn"},
                    },
                }
            },
        },
        "403": {
            "description": (
                "Authenticated but lacking permission. Read message + data.error_kind."
            ),
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ApiEnvelope"},
                    "example": {
                        "success": False,
                        "message": "Acesso negado.",
                        "data": {"error_kind": "authz"},
                    },
                }
            },
        },
        "404": _ok_response("Record not found"),
        "422": {
            "description": (
                "Request body/query schema invalid. Read message + data.errors."
            ),
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ApiEnvelope"}
                }
            },
        },
        "503": {
            "description": (
                "Persistence/infrastructure failure. Read message + data.error_kind=persistence."
            ),
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ApiEnvelope"}
                }
            },
        },
    }


def _example_process_create() -> dict[str, Any]:
    return {
        "data": {
            "nome_processo": "Processo teste GPT",
            "status_processo": "ativo",
            "descricao_processo": "Criado via Custom GPT Action",
        }
    }


def _example_instance_create() -> dict[str, Any]:
    return {
        "data": {
            "processo_id": "<processo_uuid>",
            "filial_id": "01",
            "setor_ids": ["<setor_id_or_codigo>"],
            "resumo_melhoria": "Melhoria teste GPT",
            "fase_melhoria": "planejado",
            "prioridade": "media",
            "status_instancia": "ativo",
        }
    }


def _example_instance_create_all_units() -> dict[str, Any]:
    """Corporate instance: all active units, no filial_id."""
    return {
        "data": {
            "processo_id": "<processo_uuid>",
            "todas_filiais_ativas": True,
            "setor_ids": ["<setor_id_or_codigo>"],
            "resumo_melhoria": "Melhoria corporativa (todas as filiais)",
            "fase_melhoria": "planejado",
            "prioridade": "media",
            "status_instancia": "ativo",
        }
    }


def _example_revision_create() -> dict[str, Any]:
    return {
        "data": {
            "processo_id": "<processo_uuid>",
            "instancia_id": "<instancia_uuid>",
            "versao_revisao": "2.1.0",
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-09-14",
            "revisao_referencia_id": "<baseline_revisao_uuid>",
            "beneficio_calculo_categoria": "automatico",
            "descricao_revisao": "Cenário teste GPT",
        }
    }


def _example_measurement_upsert() -> dict[str, Any]:
    return {
        "data": {
            "revisao_id": "<revisao_uuid>",
            "volume_mensal": 100,
            "tempo_medio_execucao_min": 30,
            "percentual_retrabalho": 0,
            "percentual_erro": 0,
            "custo_hora_mao_obra": 34.38,
            "base_referencia_mes": "2026-09",
        }
    }


def _example_investment_create() -> dict[str, Any]:
    return {
        "data": {
            "revisao_id": "<revisao_uuid>",
            "tipo_investimento": "unico",
            "descricao_item": "Licença teste GPT",
            "quantidade": 1,
            "valor_unitario": 1000,
            "recorrencia": "unico",
        }
    }


def _example_resource_cost_create() -> dict[str, Any]:
    return {
        "data": {
            "recurso_compartilhado_id": "<recurso_compartilhado_uuid>",
            "valor_mensal": 6051.61,
            "data_inicio_vigencia": "2026-07-06",
            "data_fim_vigencia": None,
            "observacoes": "Vigência de custo mensal",
        }
    }


def _example_resource_cost_update() -> dict[str, Any]:
    return {
        "data": {
            "valor_mensal": 6051.61,
        }
    }


def _example_shared_resource_create() -> dict[str, Any]:
    return {
        "data": {
            "nome_recurso": "Embaixador exemplo",
            "tipo_custo": "mao_obra",
            "recorrencia": "mensal",
            "criterio_rateio": "igualitario",
            "escopo_recurso": "empresa",
            "status_recurso": "ativo",
            "valor_total_recorrente": 0,
        }
    }


def _record_body_media(*, primary: dict[str, Any] | None = None) -> dict[str, Any]:
    """Typed {data:{...}} media object with multi-entity examples for Custom GPT."""
    primary = primary or _example_process_create()
    return {
        "schema": {"$ref": "#/components/schemas/GptRecordBody"},
        "example": primary,
        "examples": {
            "process_create": {
                "summary": "entity=process create",
                "value": _example_process_create(),
            },
            "instance_create": {
                "summary": "entity=instance create (one filial)",
                "value": _example_instance_create(),
            },
            "instance_create_all_units": {
                "summary": "entity=instance create (todas_filiais_ativas)",
                "value": _example_instance_create_all_units(),
            },
            "revision_create": {
                "summary": "entity=revision create",
                "value": _example_revision_create(),
            },
            "revision_clear_end_date": {
                "summary": "entity=revision update — clear data_fim_vigencia",
                "value": {
                    "data": {
                        "data_fim_vigencia": None,
                        "confirm_vigencia_change": True,
                    }
                },
            },
            "measurement_upsert": {
                "summary": "entity=measurement upsert",
                "value": _example_measurement_upsert(),
            },
            "investment_create": {
                "summary": "entity=investment create",
                "value": _example_investment_create(),
            },
            "shared_resource_create": {
                "summary": "entity=shared_resource create",
                "value": _example_shared_resource_create(),
            },
            "resource_cost_create": {
                "summary": "entity=resource_cost create",
                "value": _example_resource_cost_create(),
            },
            "resource_cost_update": {
                "summary": "entity=resource_cost update (partial valor_mensal)",
                "value": _example_resource_cost_update(),
            },
        },
    }


def _package_validate_example() -> dict[str, Any]:
    from tm_app.application.gpt_actions.improvement_package_contract import (
        build_package_hints,
    )

    return build_package_hints()["validate_example"]


def _package_commit_example() -> dict[str, Any]:
    from tm_app.application.gpt_actions.improvement_package_contract import (
        build_package_hints,
    )

    example = dict(build_package_hints()["reuse_existing_example"])
    example["dry_run"] = False
    example["activate_scenario"] = False
    example["recalculate"] = False
    return example


def build_gpt_actions_openapi(*, server_url: str | None = None) -> dict[str, Any]:
    """Return OpenAPI 3.0 document with ≤30 operations for Custom GPT import."""
    if not server_url or not str(server_url).startswith(("http://", "https://")):
        server_url = resolve_gpt_actions_server_url(explicit=server_url)
    paths: dict[str, Any] = {
        f"{GPT_ACTIONS_BASE_PATH}/me": {
            "get": {
                "operationId": "gpt_get_my_context",
                "summary": "Minimal personal context for the authenticated user",
                "description": (
                    "Read-only personal context (display name, email, job title). "
                    "PROFILE CONTEXT != AUTHORIZATION — never exposes roles, "
                    "permissions, groups or access_scope. Identity is resolved "
                    "only from the authenticated Bearer token; no user_id input."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": _ok_response("Personal context payload"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": False,
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/catalog": {
            "get": {
                "operationId": "gpt_get_catalog",
                "summary": "Catalog options for Transformômetro forms",
                "description": (
                    "Returns units, departments, enums, access scope, and "
                    "registration_guide (concepts, flow, entity_schemas) for guided signup. "
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
        f"{GPT_ACTIONS_BASE_PATH}/methodology-guide": {
            "get": {
                "operationId": "gpt_get_methodology_guide",
                "summary": "Read-only process methodology playbooks",
                "description": (
                    "READ-only guidance. Not a fact, not authorization, and not a write. "
                    "Optional method and task. Same source as MCP get_methodology_guide."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "x-openai-isConsequential": False,
                "parameters": [
                    {
                        "name": "method",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string", "enum": list(list_method_ids())},
                        "description": (
                            "Optional method id: "
                            + ", ".join(list_method_ids())
                            + ". Omit to receive the router."
                        ),
                    },
                    {
                        "name": "task",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string", "enum": list(list_task_ids())},
                        "description": (
                            "Optional task: "
                            + ", ".join(list_task_ids())
                            + ". Selects the smallest recommended methods."
                        ),
                    },
                ],
                "responses": {
                    "200": _ok_response("Methodology guide payload"),
                    **_error_responses(),
                },
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/process-context": {
            "get": {
                "operationId": "gpt_get_process_context",
                "summary": "Aggregated read-only process intelligence context",
                "description": (
                    "Ephemeral Process Business Graph from authoritative records. "
                    "No side effects. Use before diagnosis or registration."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "process_id",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Master process UUID (processo_id).",
                    },
                    {
                        "name": "instance_id",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Optional melhoria UUID to isolate one instance.",
                    },
                    {
                        "name": "revision_id",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Optional revision UUID for scenario selection.",
                    },
                ],
                "responses": {
                    "200": _ok_response("Process intelligence context"),
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
                        "description": (
                            "Department reference: UUID (setor_id) or business code "
                            "(codigo_setor, e.g. comercial)."
                        ),
                    },
                    {
                        "name": "processo_id",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": (
                            "Filter processes/instances/rows to this process UUID. "
                            "Does not widen authorization scope."
                        ),
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
                    "(instances/revisions of a process, investments of a revision). "
                    "For revisions prefer `instance_id` to isolate one melhoria. "
                    "Use `q` for process text search."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    _entity_path_param(),
                    {"name": "parent_id", "in": "query", "schema": {"type": "string"}},
                    {
                        "name": "instance_id",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": (
                            "When entity=revision, list only revisions of this "
                            "instancia_id (melhoria). Preferred over parent_id."
                        ),
                    },
                    {"name": "filial_id", "in": "query", "schema": {"type": "string"}},
                    {
                        "name": "setor_id",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": (
                            "Department reference: UUID (setor_id) or business code "
                            "(codigo_setor, e.g. comercial)."
                        ),
                    },
                    {"name": "status", "in": "query", "schema": {"type": "string"}},
                    {"name": "familia_processo", "in": "query", "schema": {"type": "string"}},
                    {
                        "name": "q",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": (
                            "Process text search (nome, codigo, familia, descricao, objetivo). "
                            "Use short keywords; try progressive fallbacks if empty."
                        ),
                    },
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
                    "Body MUST be {data:{...}}. process: nome_processo+status_processo. "
                    "instance: processo_id+setor_ids+(filial_id|todas_filiais_ativas). "
                    "resource_cost: recurso_compartilhado_id+valor_mensal+data_inicio_vigencia."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    _entity_path_param(),
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": _record_body_media(
                            primary=_example_process_create()
                        )
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
                "description": (
                    "Body MUST be {data:{...}}. Partial updates merge omitted fields for "
                    "resource_cost, shared_resource and investment."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    _entity_path_param(),
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": _record_body_media(
                            primary={
                                "data": {
                                    "nome_processo": "Processo teste GPT (atualizado)",
                                    "status_processo": "ativo",
                                }
                            }
                        )
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
                "description": (
                    "Destructive soft-delete. Path: entity + id. No JSON body. "
                    "Requires the same manage permissions as the UI."
                ),
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
                "description": (
                    "Entities: process|instance|revision. Optional body {data:{...}} "
                    "for rename fields (e.g. nome_processo)."
                ),
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
                            "schema": {"$ref": "#/components/schemas/GptRecordBody"},
                            "example": {
                                "data": {
                                    "nome_processo": "Processo teste GPT (cópia)",
                                    "status_processo": "ativo",
                                }
                            },
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
                "description": (
                    "Path id = revisao_id UUID. No required body. Consequential write."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "revisao_id to activate.",
                    },
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
                "description": (
                    "Optional filters in JSON body: revisao_id, processo_id, "
                    "competencia_inicio, competencia_fim."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/GptRecalculateBody"
                            },
                            "example": {
                                "processo_id": "<processo_uuid>",
                                "revisao_id": "<revisao_uuid>",
                            },
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
                    "Body requires action enum. Handwritten signature stays in UI/magic link."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "meeting_minute id.",
                    },
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/GptMeetingMinuteWorkflowBody"
                            },
                            "example": {"action": "send"},
                            "examples": {
                                "send": {"summary": "Send", "value": {"action": "send"}},
                                "finalize": {
                                    "summary": "Finalize",
                                    "value": {"action": "finalize"},
                                },
                                "cancel": {
                                    "summary": "Cancel",
                                    "value": {
                                        "action": "cancel",
                                        "reason": "Cancelado no teste GPT",
                                    },
                                },
                            },
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
        f"{GPT_ACTIONS_BASE_PATH}/improvement-packages/validate": {
            "post": {
                "operationId": "gpt_validate_improvement_package",
                "summary": "Validate a guided improvement package (no write)",
                "description": (
                    "Validates a nested improvement package. Never writes, activates or "
                    "recalculates. Returns ready/missing/checklist."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/GptValidateImprovementPackageBody"
                            },
                            "example": _package_validate_example(),
                        }
                    },
                },
                "responses": {
                    "200": _ok_response("Validation checklist (never persists)"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": False,
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/improvement-packages": {
            "post": {
                "operationId": "gpt_commit_improvement_package",
                "summary": "Commit a guided improvement package",
                "description": (
                    "Commits an already-reviewed improvement package. This operation may "
                    "persist data. Prefer gpt_validate_improvement_package first."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/GptImprovementPackageBody"
                            },
                            "example": _package_commit_example(),
                        }
                    },
                },
                "responses": {
                    "200": _ok_response("Dry-run checklist or commit result"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/evidence": {
            "get": {
                "operationId": "gpt_list_evidence",
                "summary": "List process or revision evidence metadata",
                "description": (
                    "Read-only. scope=process|revision. No binary download."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "scope",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string",
                            "enum": ["process", "revision"],
                        },
                    },
                    {
                        "name": "parent_id",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "processo_id or revisao_id",
                    },
                ],
                "responses": {
                    "200": _ok_response("Evidence list"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": False,
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/evidence/manage": {
            "post": {
                "operationId": "gpt_manage_evidence",
                "summary": "Manage external-link evidence metadata",
                "description": (
                    "create_link|update_description|delete. Binary upload blocked. "
                    "Delete requires confirm_delete=true."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/GptEvidenceManageBody"
                            }
                        }
                    },
                },
                "responses": {
                    "200": _ok_response("Evidence write result"),
                    "201": _ok_response("Evidence created"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/processes/{'{processo_id}'}/timeline": {
            "get": {
                "operationId": "gpt_get_process_timeline",
                "summary": "Read process audit timeline",
                "description": "Process-scoped audit trail only.",
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "processo_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "page",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "default": 1},
                    },
                    {
                        "name": "page_size",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "default": 100},
                    },
                ],
                "responses": {
                    "200": _ok_response("Timeline"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": False,
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/shared-resources/adjust-cost": {
            "post": {
                "operationId": "gpt_adjust_shared_resource_cost",
                "summary": "Register shared-resource cost adjustment",
                "description": (
                    "Canonical registrar_reajuste. Not generic resource_cost update."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/GptAdjustSharedResourceCostBody"
                            }
                        }
                    },
                },
                "responses": {
                    "201": _ok_response("Cost adjustment"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            }
        },
        f"{GPT_ACTIONS_BASE_PATH}/meeting-minutes/manage": {
            "post": {
                "operationId": "gpt_meeting_minute_manage",
                "summary": "Meeting-minute extras (not send/finalize/cancel)",
                "description": (
                    "pending_signatures|audit|versions|resend|create_version|"
                    "set_participants|set_signers|generate_from_transcript. "
                    "No PDF/PNG/public sign."
                ),
                "tags": ["Transformômetro GPT"],
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/GptMeetingMinuteManageBody"
                            }
                        }
                    },
                },
                "responses": {
                    "200": _ok_response("Meeting minute manage result"),
                    **_error_responses(),
                },
                "x-openai-isConsequential": True,
            }
        },
    }

    doc = {
        "openapi": "3.1.1",
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
                "GptMyContextResponse": {
                    "type": "object",
                    "description": (
                        "Minimal personal context. Not authorization metadata."
                    ),
                    "properties": {
                        "display_name": {
                            "type": "string",
                            "nullable": True,
                            "description": "Canonical display name from Core identity.",
                        },
                        "email": {
                            "type": "string",
                            "nullable": True,
                            "description": "Corporate email from Core identity.",
                        },
                        "job_title": {
                            "type": "string",
                            "nullable": True,
                            "description": "PersonProfile.job_title when registered.",
                        },
                        "profile_complete": {
                            "type": "boolean",
                            "description": (
                                "True when display_name and email are both present."
                            ),
                        },
                    },
                    "required": [
                        "display_name",
                        "email",
                        "job_title",
                        "profile_complete",
                    ],
                    "additionalProperties": False,
                    "example": {
                        "display_name": "Robério",
                        "email": "roberio@example.com",
                        "job_title": "Gerente de Processos",
                        "profile_complete": True,
                    },
                },
                "GptRecordBody": {
                    "type": "object",
                    "required": ["data"],
                    "description": (
                        "Wrapper required by GPT Actions. Never put CRUD fields at the root; "
                        "always nest them under data. See gpt_get_catalog.registration_guide "
                        "entity_schemas for required/optional per entity."
                    ),
                    "properties": {
                        "data": {
                            "type": "object",
                            "description": (
                                "CRUD payload keyed by entity. Explicit properties cover "
                                "process, instance, revision, measurement, investment, "
                                "shared_resource, resource_cost, resource_link, catalogs, "
                                "documents and matrix writes."
                            ),
                            "properties": openapi_record_data_properties(),
                            "additionalProperties": True,
                            "example": {
                                "nome_processo": "Processo teste GPT",
                                "status_processo": "ativo",
                                "descricao_processo": "Criado via Custom GPT Action",
                            },
                        }
                    },
                    "example": {
                        "data": {
                            "nome_processo": "Processo teste GPT",
                            "status_processo": "ativo",
                            "descricao_processo": "Criado via Custom GPT Action",
                        }
                    },
                },
                "GptRecalculateBody": {
                    "type": "object",
                    "description": "Optional filters for dashboard recalculation.",
                    "properties": {
                        "revisao_id": {
                            "type": "string",
                            "description": "Limit recalculation to one revision.",
                        },
                        "processo_id": {
                            "type": "string",
                            "description": "Limit recalculation to one process.",
                        },
                        "competencia_inicio": {
                            "type": "string",
                            "description": "Optional YYYY-MM start competence.",
                        },
                        "competencia_fim": {
                            "type": "string",
                            "description": "Optional YYYY-MM end competence.",
                        },
                    },
                    "additionalProperties": False,
                    "example": {
                        "processo_id": "<processo_uuid>",
                        "revisao_id": "<revisao_uuid>",
                    },
                },
                "GptMeetingMinuteWorkflowBody": {
                    "type": "object",
                    "required": ["action"],
                    "description": "Meeting-minute workflow command.",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": _WORKFLOW_ENUM,
                            "description": "Workflow verb for the ata.",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Optional cancel reason.",
                        },
                    },
                    "additionalProperties": False,
                    "example": {"action": "send"},
                },
                "GptEvidenceManageBody": {
                    "type": "object",
                    "required": ["scope", "operation", "parent_id"],
                    "description": (
                        "Link/metadata evidence only. Binary upload/download is "
                        "BLOCKED_BY_PLATFORM for Custom GPT Actions."
                    ),
                    "properties": {
                        "scope": {
                            "type": "string",
                            "enum": ["process", "revision"],
                        },
                        "operation": {
                            "type": "string",
                            "enum": [
                                "create_link",
                                "update_description",
                                "delete",
                            ],
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "processo_id or revisao_id",
                        },
                        "evidence_id": {
                            "type": "string",
                            "description": "Required for update_description|delete",
                        },
                        "url_externa": {
                            "type": "string",
                            "description": "Required for create_link",
                        },
                        "descricao": {"type": "string"},
                        "confirm_delete": {
                            "type": "boolean",
                            "default": False,
                            "description": "Must be true for delete",
                        },
                    },
                    "additionalProperties": False,
                    "example": {
                        "scope": "process",
                        "operation": "create_link",
                        "parent_id": "<processo_uuid>",
                        "url_externa": "https://example.com/evidence",
                        "descricao": "Link de evidência",
                    },
                },
                "GptAdjustSharedResourceCostBody": {
                    "type": "object",
                    "required": [
                        "recurso_compartilhado_id",
                        "valor_mensal",
                        "vigente_desde",
                    ],
                    "description": (
                        "Canonical shared-resource cost adjustment "
                        "(registrar_reajuste). Not a generic resource_cost CRUD."
                    ),
                    "properties": {
                        "recurso_compartilhado_id": {"type": "string"},
                        "valor_mensal": {"type": "number", "minimum": 0},
                        "vigente_desde": {
                            "type": "string",
                            "format": "date",
                            "description": "YYYY-MM-DD",
                        },
                        "observacoes": {"type": "string"},
                    },
                    "additionalProperties": False,
                    "example": {
                        "recurso_compartilhado_id": "<recurso_uuid>",
                        "valor_mensal": 1500.0,
                        "vigente_desde": "2026-10-01",
                        "observacoes": "Reajuste anual",
                    },
                },
                "GptMeetingMinuteManageBody": {
                    "type": "object",
                    "required": ["action"],
                    "description": (
                        "Meeting-minute extras beyond send/finalize/cancel "
                        "(use gpt_meeting_minute_workflow for those)."
                    ),
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "pending_signatures",
                                "audit",
                                "versions",
                                "resend",
                                "create_version",
                                "set_participants",
                                "set_signers",
                                "generate_from_transcript",
                            ],
                        },
                        "minute_id": {
                            "type": "string",
                            "description": "Required except pending_signatures",
                        },
                        "data": {
                            "type": "object",
                            "additionalProperties": True,
                            "description": (
                                "Action-specific payload. For resend: "
                                "{confirm_resend:true}. For set_participants/"
                                "set_signers: participants[]/signers[]. For "
                                "generate_from_transcript: unit_code + "
                                "transcript_html."
                            ),
                            "properties": {
                                "confirm_resend": {"type": "boolean"},
                                "participants": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": True,
                                        "properties": {
                                            "user_id": {"type": "string"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string"},
                                        },
                                    },
                                },
                                "signers": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": True,
                                        "properties": {
                                            "user_id": {"type": "string"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string"},
                                        },
                                    },
                                },
                                "unit_code": {"type": "string"},
                                "transcript_html": {"type": "string"},
                                "meeting_date": {"type": "string"},
                                "title": {"type": "string"},
                                "source": {"type": "string"},
                            },
                        },
                    },
                    "additionalProperties": False,
                    "example": {
                        "action": "pending_signatures",
                    },
                },
                "GptImprovementPackageBody": {
                    "type": "object",
                    "description": (
                        "Nested improvement package only. "
                        + " ".join(NESTING_RULES[:4])
                    ),
                    "properties": {
                        "dry_run": {
                            "type": "boolean",
                            "default": False,
                            "description": (
                                "When true: HTTP 200, no writes; ready=false + missing[] if incomplete. "
                                "ready=false is checklist guidance, not tool failure."
                            ),
                        },
                        "activate_scenario": {
                            "type": "boolean",
                            "default": False,
                            "description": (
                                "Activate the scenario revision after successful commit only "
                                "(never during dry_run)."
                            ),
                        },
                        "recalculate": {
                            "type": "boolean",
                            "default": False,
                            "description": "Recalculate dashboard cache after successful commit.",
                        },
                        "process": {
                            "type": "object",
                            "description": (
                                "REQUIRED. Reuse with id or processo_id, OR create with "
                                "nome_processo + status_processo (+ optional process fields)."
                            ),
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Existing processo_id alias.",
                                },
                                "processo_id": {
                                    "type": "string",
                                    "description": "Existing process id to reuse.",
                                },
                                "nome_processo": {"type": "string"},
                                "status_processo": {"type": "string"},
                                "descricao_processo": {"type": "string"},
                                "gestor_responsavel": {"type": "string"},
                                "objetivo_processo": {"type": "string"},
                                "codigo_processo": {"type": "string"},
                                "familia_processo": {"type": "string"},
                                "agrupador_ferramenta": {"type": "string"},
                                "filial_id": {"type": "string"},
                            },
                            "additionalProperties": True,
                        },
                        "instance": {
                            "type": "object",
                            "description": (
                                "REQUIRED. Reuse with id or instancia_id, OR create with "
                                "setor_ids and filial_id|todas_filiais_ativas."
                            ),
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Existing instancia_id alias.",
                                },
                                "instancia_id": {
                                    "type": "string",
                                    "description": "Existing instance id to reuse.",
                                },
                                "filial_id": {"type": "string"},
                                "todas_filiais_ativas": {"type": "boolean"},
                                "setor_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "setor_id": {
                                    "type": "string",
                                    "description": "Legacy single setor; prefer setor_ids.",
                                },
                                "resumo_melhoria": {"type": "string"},
                                "fase_melhoria": {"type": "string"},
                                "prioridade": {"type": "string"},
                                "status_instancia": {"type": "string"},
                            },
                            "additionalProperties": True,
                        },
                        "baseline": {
                            "type": "object",
                            "description": (
                                "Optional baseline block. Nested revision + measurement "
                                "(volume_mensal + tempo_medio_execucao_min required when creating). "
                                "cenario_tipo is forced to baseline by the service."
                            ),
                            "properties": {
                                "revision": {
                                    "$ref": "#/components/schemas/GptPackageRevision",
                                },
                                "measurement": {
                                    "$ref": "#/components/schemas/GptPackageMeasurement",
                                },
                            },
                            "additionalProperties": False,
                        },
                        "scenario": {
                            "type": "object",
                            "description": (
                                "Optional scenario block. MUST nest revision under scenario.revision "
                                "(never flat versao_revisao/processo_id on scenario root). "
                                "New scenario.revision REQUIRES scenario.measurement "
                                "(volume_mensal + tempo_medio_execucao_min). "
                                "revisao_referencia_id required unless baseline is in the same package. "
                                "investments may be []."
                            ),
                            "properties": {
                                "revision": {
                                    "$ref": "#/components/schemas/GptPackageRevision",
                                },
                                "measurement": {
                                    "$ref": "#/components/schemas/GptPackageMeasurement",
                                },
                                "investments": {
                                    "type": "array",
                                    "description": "Investment lines; empty array is valid.",
                                    "items": {
                                        "$ref": "#/components/schemas/GptPackageInvestment"
                                    },
                                },
                            },
                            "additionalProperties": False,
                        },
                    },
                },
                "GptPackageRevision": {
                    "type": "object",
                    "description": (
                        "Revision fields for baseline.revision or scenario.revision. "
                        "beneficio_calculo_categoria belongs here, not on measurement."
                    ),
                    "properties": openapi_revision_properties(),
                    "additionalProperties": True,
                },
                "GptPackageMeasurement": {
                    "type": "object",
                    "description": (
                        "Required when creating a new revision in the package. "
                        "Must include volume_mensal and tempo_medio_execucao_min."
                    ),
                    "required": ["volume_mensal", "tempo_medio_execucao_min"],
                    "properties": openapi_measurement_properties(),
                    "additionalProperties": True,
                },
                "GptPackageInvestment": {
                    "type": "object",
                    "description": "One investment item inside scenario.investments[].",
                    "properties": openapi_investment_properties(),
                    "additionalProperties": True,
                },
            },
        },
    }
    commit_props = doc["components"]["schemas"]["GptImprovementPackageBody"]["properties"]
    doc["components"]["schemas"]["GptValidateImprovementPackageBody"] = {
        "type": "object",
        "description": (
            "Nested package only: process, instance, baseline?, scenario?. "
            "No dry_run/activate_scenario/recalculate. Never persists."
        ),
        "properties": {
            key: commit_props[key]
            for key in ("process", "instance", "baseline", "scenario")
        },
    }

    # --- V2 surface: governed prepare/commit + strip legacy CRUD from import ---
    doc["components"]["schemas"]["GptPrepareRecordChangeBody"] = {
        "type": "object",
        "required": ["entity", "operation"],
        "additionalProperties": False,
        "properties": {
            "entity": {
                "type": "string",
                "enum": _ENTITY_ENUM,
                "description": _ENTITY_DESCRIPTION,
            },
            "operation": {
                "type": "string",
                "enum": ["create", "update", "delete", "duplicate"],
                "description": "Entity must allow the operation (see catalog.capability_surface).",
            },
            "record_id": {
                "type": "string",
                "description": "Required for update/delete/duplicate.",
            },
            "changes": {
                "type": "object",
                "additionalProperties": True,
                "description": (
                    "Canonical entity fields only (same as former data{}). "
                    "Server-owned fields rejected."
                ),
                "properties": openapi_record_data_properties(),
            },
        },
    }
    doc["components"]["schemas"]["GptCommitProposalBody"] = {
        "type": "object",
        "required": ["proposal_handle", "confirmation"],
        "additionalProperties": False,
        "properties": {
            "proposal_handle": {
                "type": "string",
                "description": "Opaque server handle from PREPARE. Do not invent.",
            },
            "confirmation": {
                "type": "boolean",
                "description": (
                    "Must be true after showing proposal to the user. "
                    "Not AuthZ; backend revalidates."
                ),
            },
        },
    }

    paths = doc["paths"]
    # Remove legacy write methods from Builder-visible OpenAPI.
    legacy_ids = set(GPT_ACTIONS_LEGACY_OPERATION_IDS)
    for path_key, methods in list(paths.items()):
        if not isinstance(methods, dict):
            continue
        for method in list(methods.keys()):
            op = methods.get(method)
            if not isinstance(op, dict):
                continue
            if op.get("operationId") in legacy_ids:
                del methods[method]
        if not methods:
            del paths[path_key]

    paths[f"{GPT_ACTIONS_BASE_PATH}/records/prepare-change"] = {
        "post": {
            "operationId": "gpt_prepare_record_change",
            "summary": "PREPARE entity create/update/delete/duplicate (no write)",
            "description": (
                "READ CURRENT STATE → validate → return opaque proposal_handle. "
                "No DB write. Then show proposal and call gpt_commit_proposal."
            ),
            "tags": ["Transformômetro GPT"],
            "security": [{"BearerAuth": []}],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/GptPrepareRecordChangeBody"
                        },
                        "example": {
                            "entity": "process_document",
                            "operation": "create",
                            "changes": {
                                "processo_id": "00000000-0000-0000-0000-000000000001",
                                "title": "AS-IS notes",
                                "content_md": "# Draft",
                            },
                        },
                    }
                },
            },
            "responses": {
                "200": _ok_response("proposal_ready envelope"),
                **_error_responses(),
            },
            "x-openai-isConsequential": False,
        }
    }
    paths[f"{GPT_ACTIONS_BASE_PATH}/proposals/commit"] = {
        "post": {
            "operationId": "gpt_commit_proposal",
            "summary": "COMMIT opaque proposal_handle after confirmation",
            "description": (
                "NOT a generic proxy: executes only a server-side PREPARE proposal. "
                "Revalidates AuthZ + state fingerprint; authoritative read-back."
            ),
            "tags": ["Transformômetro GPT"],
            "security": [{"BearerAuth": []}],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/GptCommitProposalBody"
                        },
                        "example": {
                            "proposal_handle": "…",
                            "confirmation": True,
                        },
                    }
                },
            },
            "responses": {
                "200": _ok_response("verified commit outcome"),
                **_error_responses(),
            },
            "x-openai-isConsequential": True,
        }
    }

    # Tighten specialized write descriptions: PREPARE-only.
    for methods in paths.values():
        if not isinstance(methods, dict):
            continue
        for op in methods.values():
            if not isinstance(op, dict):
                continue
            oid = op.get("operationId")
            if oid in {
                "gpt_activate_revision",
                "gpt_recalculate_dashboard",
                "gpt_meeting_minute_workflow",
                "gpt_manage_evidence",
                "gpt_adjust_shared_resource_cost",
                "gpt_validate_improvement_package",
            }:
                desc = str(op.get("description") or "")
                if "gpt_commit_proposal" not in desc:
                    op["description"] = (
                        (desc + " ").strip()
                        + " PREPARE only — commit via gpt_commit_proposal."
                    )[:300]
                op["x-openai-isConsequential"] = False
            if oid == "gpt_meeting_minute_manage":
                op["description"] = (
                    "READ actions return immediately. WRITE actions return a PREPARE "
                    "proposal; commit via gpt_commit_proposal."
                )[:300]

    return doc


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
