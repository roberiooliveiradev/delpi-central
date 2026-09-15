"""Build the compact OpenAPI 3.1 schema for OpenAI Custom GPT Actions (TV)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from tv_app.application.gpt_actions import (
    GPT_ACTIONS_BASE_PATH,
    GPT_ACTIONS_GATEWAY_ROOT,
    GPT_ACTIONS_OPERATION_IDS,
    GPT_ACTIONS_PUBLIC_FALLBACK_ORIGIN,
)
from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)


def resolve_gpt_actions_server_url(
    *,
    public_base_url: str | None = None,
    root_path: str | None = None,
    explicit: str | None = None,
) -> str:
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


def _opaque_object_schema(*, description: str | None = None) -> dict[str, Any]:
    """Builder-compatible free-form object (never bare type=object)."""
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "additionalProperties": True,
    }
    if description:
        schema["description"] = description
    return schema


def normalize_json_schema_for_gpt_builder(node: Any) -> Any:
    """Ensure every type=object has properties; arrays have items (TÉO invariant)."""
    if isinstance(node, list):
        return [normalize_json_schema_for_gpt_builder(item) for item in node]
    if not isinstance(node, dict):
        return node

    out = {key: normalize_json_schema_for_gpt_builder(value) for key, value in node.items()}

    if out.get("type") == "object" and "$ref" not in out:
        props = out.get("properties")
        if not isinstance(props, dict):
            out["properties"] = {}
        else:
            out["properties"] = {
                key: normalize_json_schema_for_gpt_builder(value)
                for key, value in props.items()
            }

    if out.get("type") == "array" and "items" not in out and "$ref" not in out:
        out["items"] = _opaque_object_schema()

    # OpenAPI/GPT Builder: pair const with an explicit type when missing.
    if "const" in out and "type" not in out and "$ref" not in out:
        const_val = out["const"]
        if isinstance(const_val, bool):
            out["type"] = "boolean"
        elif isinstance(const_val, int) and not isinstance(const_val, bool):
            out["type"] = "integer"
        elif isinstance(const_val, float):
            out["type"] = "number"
        else:
            out["type"] = "string"

    return out


def _project_operation_input_schemas() -> list[dict[str, Any]]:
    """Canonical TvCopilot operations → OpenAPI oneOf branches (no parallel catalog)."""
    branches: list[dict[str, Any]] = []
    for op_name, spec in sorted(TvCopilotContentService.operations().items()):
        if not isinstance(spec, dict):
            continue
        raw = spec.get("inputSchema")
        if not isinstance(raw, dict):
            continue
        schema = normalize_json_schema_for_gpt_builder(copy.deepcopy(raw))
        schema.setdefault("title", op_name)
        props = schema.setdefault("properties", {})
        if isinstance(props, dict) and "op" not in props:
            props["op"] = {"type": "string", "const": op_name}
        required = schema.get("required")
        if isinstance(required, list) and "op" not in required:
            schema["required"] = ["op", *required]
        elif not isinstance(required, list):
            schema["required"] = ["op"]
        branches.append(schema)
    return branches


def _typed_ops_schema() -> dict[str, Any]:
    branches = _project_operation_input_schemas()
    return {
        "type": "array",
        "description": (
            "Typed Copilot ops from the canonical TV catalog (objects with op — "
            "never bare strings). Shape projected from TvCopilotContentService."
        ),
        "minItems": 1,
        "items": {
            "oneOf": branches,
            "description": "One canonical TV Copilot operation.",
        },
    }


def _change_target_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "description": (
            "Change target. Omit or leave empty for create_playlist without an "
            "existing playlist. playlistId is required by ops that need a playlist."
        ),
        "properties": {
            "playlistId": {
                "type": "string",
                "format": "uuid",
                "description": "Existing playlist UUID when the op requires one.",
            },
            "slideId": {
                "type": "string",
                "format": "uuid",
                "description": "Slide UUID when the op requires slide context.",
            },
        },
        "additionalProperties": False,
    }


def _host_context_schema() -> dict[str, Any]:
    """Smallest truthful hostContext from Copilot planner/suggest consumers."""
    return {
        "type": "object",
        "description": (
            "Optional editor/host focus. Custom GPT usually omits this; useful when "
            "the user already named a playlist/slide in-session."
        ),
        "properties": {
            "playlistId": {"type": "string", "format": "uuid"},
            "slideId": {"type": "string", "format": "uuid"},
            "sectionId": {"type": "string"},
            "selectedBlockIds": {
                "type": "array",
                "items": {"type": "string"},
            },
            "selectedBlockId": {"type": "string"},
            "selectedDataSourceId": {"type": "string"},
            "selectedVisualId": {"type": "string"},
            "presetKey": {"type": "string"},
            "hasLocalDraft": {"type": "boolean"},
        },
        "additionalProperties": True,
    }


def _catalog_version_placeholder() -> str:
    return TvCopilotContentService.catalog_version()


def _create_playlist_ops_example() -> list[dict[str, Any]]:
    return [{"op": "create_playlist", "name": "Testando a VISTA"}]


def _envelope_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["success", "message", "data"],
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            # Keep data untyped (no type=object) — same pattern as prior TV + TÉO envelope.
            "data": {},
        },
    }


def _error_envelope_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["ok", "error", "meta"],
        "properties": {
            "ok": {"type": "boolean", "enum": [False]},
            "error": {
                "type": "object",
                "required": ["code", "message", "retryable"],
                "properties": {
                    "code": {
                        "type": "string",
                        "description": (
                            "Machine code e.g. INVALID_CHANGE, FORBIDDEN, NOT_FOUND, "
                            "REVISION_CONFLICT, IDEMPOTENCY_CONFLICT, PLAN_MISMATCH, "
                            "CATALOG_VERSION_STALE, UPSTREAM_ERROR."
                        ),
                    },
                    "message": {
                        "type": "string",
                        "description": "Human-readable explanation for VISTA to relay.",
                    },
                    "retryable": {"type": "boolean"},
                    "details": _opaque_object_schema(
                        description="Optional structured fields (no secrets)."
                    ),
                },
            },
            "meta": {
                "type": "object",
                "properties": {"correlationId": {"type": "string"}},
                "additionalProperties": True,
            },
        },
    }


def _ok_response(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/GptSuccessEnvelope"}
            }
        },
    }


def _error_response(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/GptErrorEnvelope"}
            }
        },
    }


def _error_responses() -> dict[str, Any]:
    return {
        "400": _error_response("Validation or unsupported capability"),
        "401": _error_response("Missing or invalid Bearer token"),
        "403": _error_response("Authenticated but lacking TV permission"),
        "404": _error_response("Resource not found"),
        "409": _error_response(
            "Conflict (revision/catalog/plan/idempotency/partial/in-progress)"
        ),
        "422": _error_response("Invalid change payload"),
        "502": _error_response("Upstream failure"),
    }


def _json_body(schema: dict[str, Any], *, example: dict[str, Any] | None = None) -> dict[str, Any]:
    content: dict[str, Any] = {"schema": schema}
    if example is not None:
        content["example"] = example
    return {
        "required": True,
        "content": {"application/json": content},
    }


def build_gpt_actions_openapi(*, server_url: str | None = None) -> dict[str, Any]:
    if not server_url or not str(server_url).startswith(("http://", "https://")):
        server_url = resolve_gpt_actions_server_url(explicit=server_url)
    base = GPT_ACTIONS_BASE_PATH
    tag = "TV Dashboard GPT"
    catalog_version = _catalog_version_placeholder()
    create_ops = _create_playlist_ops_example()
    typed_ops = _typed_ops_schema()

    data_preview_schema = {
        "type": "object",
        "required": ["block", "nativeConfig"],
        "properties": {
            "block": _opaque_object_schema(
                description="Slide block payload (same shape as editor preview)."
            ),
            "nativeConfig": _opaque_object_schema(
                description="Native slide config used for dry-run resolution."
            ),
            "playlistId": {"type": "string"},
            "playlistDefaults": _opaque_object_schema(),
            "forceRefresh": {"type": "boolean"},
            "targetStepName": {"type": "string"},
            "previewOptions": _opaque_object_schema(),
        },
    }

    suggest_schema = {
        "type": "object",
        "required": ["message"],
        "properties": {
            "message": {
                "type": "string",
                "minLength": 1,
                "description": "Natural-language change request.",
            },
            "hostContext": {"$ref": "#/components/schemas/GptHostContext"},
        },
    }

    preview_schema = {
        "type": "object",
        "required": ["ops"],
        "properties": {
            "target": {"$ref": "#/components/schemas/GptChangeTarget"},
            "ops": typed_ops,
            "catalogVersion": {
                "type": "string",
                "description": "Must match gpt_get_catalog.catalogVersion.",
            },
        },
    }

    commit_schema = {
        "type": "object",
        "required": ["ops", "catalogVersion", "planDigest"],
        "properties": {
            "target": {"$ref": "#/components/schemas/GptChangeTarget"},
            "ops": typed_ops,
            "catalogVersion": {"type": "string"},
            "expectedRevision": {
                "type": "integer",
                "description": (
                    "Required OCC revision for an existing playlist. "
                    "Omit only for create_playlist without playlistId."
                ),
            },
            "planDigest": {
                "type": "string",
                "description": "Digest returned by gpt_preview_change for the same ops.",
            },
        },
    }

    paths: dict[str, Any] = {
        f"{base}/catalog": {
            "get": {
                "operationId": "gpt_get_catalog",
                "summary": "TV Copilot capability catalog",
                "description": (
                    "Returns catalogVersion, operations, capabilities and limits from the "
                    "canonical TvCopilotPatchV1 authority. Call before planning changes."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "responses": {"200": _ok_response("Catalog"), **_error_responses()},
            }
        },
        f"{base}/playlists": {
            "get": {
                "operationId": "gpt_list_playlists",
                "summary": "List owned and shared playlists",
                "description": (
                    "Lists playlists visible to the authenticated actor (owner/share). "
                    "Does not return a global admin dump."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 50},
                        "description": "Max items (1-100).",
                    },
                    {
                        "name": "offset",
                        "in": "query",
                        "schema": {"type": "integer", "default": 0},
                        "description": "Pagination offset.",
                    },
                ],
                "responses": {"200": _ok_response("Playlist list"), **_error_responses()},
            }
        },
        f"{base}/playlists/{{playlist_id}}": {
            "get": {
                "operationId": "gpt_get_playlist_context",
                "summary": "Authorized playlist context",
                "description": (
                    "Returns persisted playlist, slides, sections, accessRole, currentRevision. "
                    "localDraftCoordination is unavailable_external for Custom GPT."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "playlist_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string", "format": "uuid"},
                        "description": "Playlist UUID.",
                    }
                ],
                "responses": {"200": _ok_response("Playlist context"), **_error_responses()},
            }
        },
        f"{base}/data-routes": {
            "get": {
                "operationId": "gpt_search_data_routes",
                "summary": "Search allowlisted data routes",
                "description": (
                    "Searches the TV data route catalog. Never invent operationId; "
                    "only use returned route identifiers."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "query",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Optional NL query; empty lists catalog head.",
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 20},
                        "description": "Max routes to return.",
                    },
                ],
                "responses": {"200": _ok_response("Data routes"), **_error_responses()},
            }
        },
        f"{base}/data-preview": {
            "post": {
                "operationId": "gpt_preview_data_block",
                "summary": "Preview a data block without persisting",
                "description": (
                    "Dry-run data resolution for a block using the same preview pipeline "
                    "as the editor. No persistence."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "requestBody": _json_body(
                    data_preview_schema,
                    example={
                        "block": {
                            "id": "blk-demo",
                            "type": "kpi",
                            "title": "Exemplo",
                        },
                        "nativeConfig": {"version": 1, "blocks": []},
                        "forceRefresh": False,
                    },
                ),
                "responses": {"200": _ok_response("Block preview"), **_error_responses()},
            }
        },
        f"{base}/changes/suggest": {
            "post": {
                "operationId": "gpt_suggest_change",
                "summary": "Suggest typed Copilot ops from NL",
                "description": (
                    "Uses the canonical Copilot planner. Returns ready|clarification|"
                    "unsupported|error with typed ops — no free M/SQL. "
                    "Example: create a playlist named Testando a VISTA."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "requestBody": _json_body(
                    suggest_schema,
                    example={
                        "message": "Crie uma playlist chamada Testando a VISTA",
                    },
                ),
                "responses": {"200": _ok_response("Suggestion plan"), **_error_responses()},
            }
        },
        f"{base}/changes/preview": {
            "post": {
                "operationId": "gpt_preview_change",
                "summary": "Preview typed change without persisting",
                "description": (
                    "Dry-run TvCopilotPatchV1. Returns planDigest, risk, confirmationPolicy, "
                    "diff. Does not persist. Does not expose httpCommands. "
                    "For create_playlist, target may be empty and expectedRevision is N/A."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "requestBody": _json_body(
                    preview_schema,
                    example={
                        "target": {},
                        "ops": create_ops,
                        "catalogVersion": catalog_version,
                    },
                ),
                "responses": {"200": _ok_response("Change preview"), **_error_responses()},
            }
        },
        f"{base}/changes/commit": {
            "post": {
                "operationId": "gpt_commit_change",
                "summary": "Commit a previously previewed change",
                "description": (
                    "ACT via shared write boundary. Requires Idempotency-Key, planDigest, "
                    "catalogVersion. expectedRevision is required when target.playlistId "
                    "refers to an existing playlist; omit only for create_playlist without "
                    "pre-existing playlist. Authoritative read-back required."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "x-openai-isConsequential": True,
                "parameters": [
                    {
                        "name": "Idempotency-Key",
                        "in": "header",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": (
                            "Client-generated key scoped to actor+operation. Atomic acquire "
                            "before write; same key+payload replays; different payload → 409."
                        ),
                    }
                ],
                "requestBody": _json_body(
                    commit_schema,
                    example={
                        "target": {},
                        "ops": create_ops,
                        "catalogVersion": catalog_version,
                        "planDigest": (
                            "0123456789abcdef0123456789abcdef"
                            "0123456789abcdef0123456789abcdef"
                        ),
                    },
                ),
                "responses": {"200": _ok_response("Verified commit"), **_error_responses()},
            }
        },
    }

    return {
        "openapi": "3.1.1",
        "info": {
            "title": "TV Dashboard Custom GPT Actions",
            "version": "1.0.0",
            "description": (
                "Compact OAuth façade over tv-dashboard-api. Owner of catalog and writes "
                "remains TV. Eight Actions; openapi.json is import-only and not listed here."
            ),
        },
        "servers": [{"url": server_url}],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Keycloak access token for the authenticated human actor.",
                }
            },
            "schemas": {
                "GptSuccessEnvelope": _envelope_schema(),
                "GptErrorEnvelope": _error_envelope_schema(),
                "GptChangeTarget": _change_target_schema(),
                "GptHostContext": _host_context_schema(),
                "ApiEnvelope": _envelope_schema(),
            },
        },
    }


def write_gpt_actions_openapi(path: Path, *, server_url: str | None = None) -> dict[str, Any]:
    doc = build_gpt_actions_openapi(server_url=server_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return doc


def count_operations(doc: dict[str, Any] | None = None) -> int:
    document = doc or build_gpt_actions_openapi()
    total = 0
    for methods in (document.get("paths") or {}).values():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.startswith("x-") or not isinstance(op, dict):
                continue
            if op.get("operationId"):
                total += 1
    return total


def assert_operation_ids(doc: dict[str, Any] | None = None) -> list[str]:
    document = doc or build_gpt_actions_openapi()
    found: list[str] = []
    for methods in (document.get("paths") or {}).values():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.startswith("x-") or not isinstance(op, dict):
                continue
            oid = op.get("operationId")
            if oid:
                found.append(str(oid))
    expected = list(GPT_ACTIONS_OPERATION_IDS)
    if found != expected:
        raise AssertionError(f"operationIds mismatch: {found} != {expected}")
    return found
