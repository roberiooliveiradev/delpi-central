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
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
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


GPT_OPAQUE_OBJECT_EXTENSION = "x-delpi-gpt-opaque-object"

# OpenAI Custom GPT Builder rejects operation.description longer than this.
CUSTOM_GPT_OPERATION_DESCRIPTION_MAX_CHARS = 300


def _opaque_object_schema(*, description: str) -> dict[str, Any]:
    """Intentional free-form object. Requires marker + description."""
    return {
        "type": "object",
        "description": description,
        GPT_OPAQUE_OBJECT_EXTENSION: True,
        "additionalProperties": True,
        "properties": {},
    }


def _project_schema_node(node: Any) -> Any:
    """Deep-copy JSON Schema preserving composition, maps and typed items."""
    if isinstance(node, list):
        return [_project_schema_node(item) for item in node]
    if not isinstance(node, dict):
        return node

    out: dict[str, Any] = {}
    for key, value in node.items():
        if key == "example":
            out[key] = copy.deepcopy(value)
            continue
        out[key] = _project_schema_node(value)

    if out.get("type") == "object" and "$ref" not in out:
        additional = out.get("additionalProperties")
        typed_map = isinstance(additional, dict)
        if not isinstance(out.get("properties"), dict) and not typed_map:
            if out.get(GPT_OPAQUE_OBJECT_EXTENSION) is True:
                out["properties"] = {}
            # Leave typed maps without dummy properties.
        elif isinstance(out.get("properties"), dict):
            out["properties"] = {
                key: _project_schema_node(value)
                for key, value in out["properties"].items()
            }

    if out.get("type") == "array" and "items" not in out and "$ref" not in out:
        raise ValueError("canonical array schema missing items")

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

    # GPT Builder: scalar + nullable:true (never type unions with null).
    t = out.get("type")
    if isinstance(t, list):
        normalized = [("null" if x in (None, "None") else x) for x in t]
        non_null = [x for x in normalized if x != "null"]
        if "null" in normalized and len(non_null) == 1:
            out["type"] = non_null[0]
            out["nullable"] = True
        elif "null" in normalized and non_null:
            out["type"] = non_null[0]
            out["nullable"] = True
        elif len(normalized) == 1:
            out["type"] = normalized[0]
        # Multi-scalar unions (e.g. integer|string) stay as-is so catalog owners
        # must fix the canonical content; CI audit will fail the artifact.

    if out.get(GPT_OPAQUE_OBJECT_EXTENSION) is True and not str(
        out.get("description") or ""
    ).strip():
        out["description"] = (
            "Intentionally opaque object for GPT Builder import "
            f"({GPT_OPAQUE_OBJECT_EXTENSION})."
        )

    return out


def normalize_json_schema_for_gpt_builder(node: Any) -> Any:
    """Project canonical JSON Schema for GPT Builder without inventing shapes."""
    return _project_schema_node(node)


def _project_operation_input_schemas() -> list[dict[str, Any]]:
    """Canonical PresentationOps operations → OpenAPI oneOf branches (no parallel catalog)."""
    branches: list[dict[str, Any]] = []
    for op_name, spec in sorted(PresentationOpsContentService.operations().items()):
        if not isinstance(spec, dict):
            continue
        raw = spec.get("inputSchema")
        if not isinstance(raw, dict):
            continue
        schema = normalize_json_schema_for_gpt_builder(copy.deepcopy(raw))
        schema.setdefault("title", op_name)
        props = schema.get("properties")
        if not isinstance(props, dict):
            props = {}
            schema["properties"] = props
        if "op" not in props:
            props["op"] = {"type": "string", "const": op_name}
        # Compound plan chaining (optional; PlanCompiler resolves order + refs).
        produces = spec.get("produces") if isinstance(spec.get("produces"), list) else []
        consumes = spec.get("consumes") if isinstance(spec.get("consumes"), list) else []
        if produces:
            props.setdefault(
                "as",
                {
                    "type": "string",
                    "description": "Local alias for the resource this op produces (compound plans).",
                },
            )
        if "playlist" in consumes or "playlist" in produces:
            props.setdefault(
                "playlistRef",
                {
                    "type": "string",
                    "description": "Alias or authoritative playlist UUID. Omit to use current playlist slot.",
                },
            )
        if "slide" in consumes or "slide" in produces:
            props.setdefault(
                "slideRef",
                {
                    "type": "string",
                    "description": "Alias or authoritative slide UUID. Omit to use current slide slot.",
                },
            )
        if "section" in consumes or "section" in produces:
            props.setdefault(
                "sectionRef",
                {
                    "type": "string",
                    "description": "Alias or authoritative section UUID. Omit to use current section slot.",
                },
            )
        required = schema.get("required")
        if isinstance(required, list) and "op" not in required:
            schema["required"] = ["op", *required]
        elif not isinstance(required, list):
            schema["required"] = ["op"]
        example = raw.get("example")
        if isinstance(example, dict) and example:
            schema["example"] = copy.deepcopy(example)
        branches.append(schema)
    return branches


def _typed_ops_schema() -> dict[str, Any]:
    branches = _project_operation_input_schemas()
    return {
        "type": "array",
        "description": (
            "Typed presentation ops from the canonical TV catalog (objects with op — "
            "never bare strings). Shape projected from PresentationOpsContentService."
        ),
        "minItems": 1,
        "items": {
            "oneOf": branches,
            "description": "One canonical PresentationMutation operation.",
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
    return PresentationOpsContentService.catalog_version()


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
                            "Machine code e.g. INVALID_CHANGE, AUTHZ_DENIED, NOT_FOUND, "
                            "PROPOSAL_CHANGED, PROPOSAL_EXPIRED, PROPOSAL_NOT_FOUND, "
                            "CONFIRMATION_REQUIRED, IDEMPOTENCY_CONFLICT, "
                            "CATALOG_VERSION_STALE, OUTCOME_NOT_VERIFIED, UPSTREAM_FAILURE."
                        ),
                    },
                    "message": {
                        "type": "string",
                        "description": "Human-readable explanation for VISTA to relay.",
                    },
                    "retryable": {"type": "boolean"},
                    "details": _opaque_object_schema(
                        description=(
                            "Optional diagnostics: operation, opIndex, validationPath, "
                            "received, expected, internalReason, suggestedCorrection. "
                            "Never includes tokens, SQL, or stack traces. "
                            "Intentionally opaque (response-side only)."
                        )
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
        "properties": {
            "operationId": {
                "type": "string",
                "description": (
                    "Preferred shortcut: allowlisted catalog operationId. "
                    "Server builds canonical binding; do not invent block/nativeConfig."
                ),
            },
            "params": _opaque_object_schema(
                description=(
                    "Params validated against the route paramSchema (enums/required). "
                    "Use values from gpt_search_data_routes paramSchema."
                )
            ),
            "block": _opaque_object_schema(
                description=(
                    "Legacy editor block blob. Prefer operationId+params. "
                    "Runtime validates downstream when provided."
                )
            ),
            "nativeConfig": _opaque_object_schema(
                description=(
                    "Candidate slide config for dry-run. When provided with "
                    "block, the block is upserted by id inside this context. "
                    "Optional when operationId is provided."
                )
            ),
            "playlistId": {
                "type": "string",
                "description": (
                    "Authoritative context: loads the persisted playlist "
                    "(dataDefaults) and, with slideId, the slide nativeConfig so "
                    "merge.sourceId siblings materialize in preview."
                ),
            },
            "slideId": {
                "type": "string",
                "description": (
                    "With playlistId: preview inside the persisted slide "
                    "context. Merge dependencies of the target block resolve "
                    "from slide blocks."
                ),
            },
            "blockId": {
                "type": "string",
                "description": (
                    "Persisted block to preview inside playlistId+slideId "
                    "context, or the target block id within nativeConfig."
                ),
            },
            "playlistDefaults": _opaque_object_schema(
                description=(
                    "Optional playlist dataDefaults blob inherited during dry-run. "
                    "Route-specific; not a fixed GPT construction contract."
                )
            ),
            "forceRefresh": {"type": "boolean"},
            "targetStepName": {"type": "string"},
            "previewOptions": _opaque_object_schema(
                description=(
                    "Optional resolver flags for dry-run. Intentionally open-ended "
                    "preview knobs, not a persisted write contract."
                )
            ),
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
            "commit_now": {
                "type": "boolean",
                "default": False,
                "description": (
                    "If true and confirmationPolicy=direct, PREPARE+COMMIT in one call "
                    "(requires confirmation + Idempotency-Key). Ignored when policy=confirm."
                ),
            },
            "confirmation": {
                "oneOf": [
                    {"type": "boolean"},
                    {
                        "type": "object",
                        "required": ["confirmed"],
                        "properties": {"confirmed": {"type": "boolean"}},
                        "additionalProperties": False,
                    },
                ],
                "description": "Required when commit_now=true (confirmed must be true).",
            },
            "idempotency_key": {
                "type": "string",
                "description": (
                    "Fallback when Idempotency-Key header is missing. Required for commit_now."
                ),
            },
        },
    }

    commit_schema = {
        "type": "object",
        "required": ["proposal_handle", "confirmation"],
        "properties": {
            "proposal_handle": {
                "type": "string",
                "minLength": 8,
                "description": (
                    "Exact opaque string from gpt_preview_change.proposal_handle. "
                    "Never invent values like latest/current/null."
                ),
            },
            "confirmation": {
                "oneOf": [
                    {
                        "type": "boolean",
                        "description": "Pass true after explicit user confirmation.",
                    },
                    {
                        "type": "object",
                        "required": ["confirmed"],
                        "properties": {
                            "confirmed": {
                                "type": "boolean",
                                "description": "Must be true to commit.",
                            }
                        },
                        "additionalProperties": False,
                    },
                ],
                "description": (
                    "Explicit user confirmation. Conversational OK is not AuthZ; "
                    "backend revalidates permission and proposal binding."
                ),
            },
            "idempotency_key": {
                "type": "string",
                "description": "Fallback if Idempotency-Key header is omitted.",
            },
        },
        "additionalProperties": False,
    }

    paths: dict[str, Any] = {
        f"{base}/catalog": {
            "get": {
                "operationId": "gpt_get_catalog",
                "summary": "TV presentation mutation capability catalog",
                "description": (
                    "Returns catalogVersion, compact ops index, capabilities, and "
                    "capability_surface.agent_directives. Full op schemas live in this "
                    "OpenAPI requestBody. Call before writes; obey agent_directives. "
                    "Backend authorizes. Requires tv-dashboard.write."
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
                    "Compact playlist list for the authenticated actor (id/name/role/revision). "
                    "No coverSlide/nativeConfig. When the actor has a live editor session, "
                    "editorFocus is returned first (playlistId/slideId/selectedIds, ephemeral TTL)."
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
                    "Playlist context with slides and focused slide. "
                    "editorFocus omits nativeConfig and returns dataSources + blockIndex. "
                    "full may auto-downgrade when over budget. "
                    "objectQuery can return persisted objectMatches. "
                    "includePreview adds a signed slide preview."
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
                    },
                    {
                        "name": "includePreview",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "boolean", "default": False},
                        "description": (
                            "When true, include slidePreview with signed previewUrl "
                            "(schematic PNG). Prefer over a dedicated preview Action."
                        ),
                    },
                    {
                        "name": "slideId",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string", "format": "uuid"},
                        "description": (
                            "Selects focusedSlide (full nativeConfig) and optional includePreview. "
                            "Defaults to editorFocus.slideId or the first slide."
                        ),
                    },
                    {
                        "name": "scope",
                        "in": "query",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["full", "editorFocus"],
                            "default": "full",
                        },
                        "description": (
                            "full: focusedSlide.nativeConfig + digests. "
                            "editorFocus: omit nativeConfig; return dataSources[] + "
                            "blockIndex for existing-object addressability."
                        ),
                    },
                    {
                        "name": "objectQuery",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": (
                            "Optional filter for objectMatches[] "
                            "(contentPreview/label/groupId/role). Persisted IDs only."
                        ),
                    },
                    {
                        "name": "objectTypes",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": (
                            "Optional comma-separated types filter for blockIndex/objectMatches."
                        ),
                    },
                    {
                        "name": "blockCursor",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Absolute offset cursor for blockIndex pagination.",
                    },
                    {
                        "name": "blockLimit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer"},
                        "description": "Max items in blockIndex.items for this page.",
                    },
                ],
                "responses": {"200": _ok_response("Playlist context"), **_error_responses()},
            }
        },
        f"{base}/data-routes": {
            "get": {
                "operationId": "gpt_search_data_routes",
                "summary": "Search allowlisted data routes",
                "description": (
                    "Required NL query over the TV allowlist (owner-local discovery). "
                    "Never dump the full catalog; never invent operationId. "
                    "Miss does not prove absence — refine query. Returns compact "
                    "DTO with paramSchema."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "query",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string", "minLength": 1},
                        "description": "Business intent (ex.: otd comercial).",
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 8, "minimum": 1, "maximum": 20},
                        "description": "Max routes (default 8, max 20).",
                    },
                    {
                        "name": "category",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Optional category filter (commercial, supplies, …).",
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
                    "Prefer operationId+params from search hits; server validates "
                    "paramSchema and builds the canonical binding. Legacy "
                    "block+nativeConfig remains for editor-shaped clients. No persistence."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "requestBody": _json_body(
                    data_preview_schema,
                    example={
                        "operationId": "get_sales_order_otd_series",
                        "params": {"granularity": "week"},
                        "forceRefresh": False,
                    },
                ),
                "responses": {"200": _ok_response("Block preview"), **_error_responses()},
            }
        },
        f"{base}/changes/suggest": {
            "post": {
                "operationId": "gpt_suggest_change",
                "summary": "Suggest typed presentation ops from NL",
                "description": (
                    "Uses the canonical presentation planner. Returns ready|clarification|"
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
                    "PREPARE PresentationMutation compound plan. Server topo-sorts ops "
                    "(as/playlistRef/slideRef). NO WRITE by default. Additive: "
                    "commit_now=true + confirmation + Idempotency-Key → PREPARE+COMMIT. "
                    "Destructive ignores commit_now."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {
                        "name": "Idempotency-Key",
                        "in": "header",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": "Required when commit_now=true (or use body idempotency_key).",
                    }
                ],
                "requestBody": _json_body(
                    preview_schema,
                    example={
                        "target": {},
                        "ops": create_ops,
                        "catalogVersion": catalog_version,
                        "commit_now": True,
                        "confirmation": {"confirmed": True},
                        "idempotency_key": "vista-create-playlist-1",
                    },
                ),
                "responses": {"200": _ok_response("Change preview or verified commit"), **_error_responses()},
            }
        },
        f"{base}/changes/commit": {
            "post": {
                "operationId": "gpt_commit_change",
                "summary": "Commit a previously previewed change",
                "description": (
                    "COMMIT prepared proposal. WRITE. Body: exact proposal_handle + "
                    "confirmation (+ Idempotency-Key). Never invent handle (no latest). "
                    "Prefer commit_now on preview for additive direct policies."
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
                        "proposal_handle": "dnBfYWJjMTIz.dGVzdGhtYWMtc2lnbmF0dXJl",
                        "confirmation": {"confirmed": True},
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
                "Compact OAuth façade over tv-dashboard-api (VISTA). Owner of catalog "
                "and writes remains TV. Eight Actions under GOVERNED_PREPARE_COMMIT_V2; "
                "openapi.json is import-only and not listed here."
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
