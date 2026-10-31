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

    data_model_preview_schema = {
        "type": "object",
        "properties": {
            "modelId": {
                "type": "string",
                "description": (
                    "Persisted DataModel id inside playlistId+slideId (or "
                    "nativeConfig) context."
                ),
            },
            "model": _opaque_object_schema(
                description=(
                    "Candidate DataModel definition (DM0 contract: id/label/"
                    "primaryInputId/inputs[]/transform). Previewed without "
                    "persisting; merge.sourceId references input.id."
                )
            ),
            "nativeConfig": _opaque_object_schema(
                description=(
                    "Candidate slide config providing dataModels[] context. "
                    "Inline model is upserted by id inside this context."
                )
            ),
            "playlistId": {
                "type": "string",
                "description": (
                    "Authoritative context: loads the persisted playlist "
                    "(dataDefaults) and, with slideId, the slide nativeConfig."
                ),
            },
            "slideId": {
                "type": "string",
                "description": "With playlistId: resolve the model inside the persisted slide.",
            },
            "playlistDefaults": _opaque_object_schema(
                description="Optional playlist dataDefaults blob for dry-run."
            ),
            "forceRefresh": {"type": "boolean"},
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
        # SEMANTIC_TOOLS_V1 — closed-vocabulary verbs (coexist with gpt_*).
        # ------------------------------------------------------------------
        f"{base}/semantic/context": {
            "post": {
                "operationId": "vista_get_context",
                "summary": "VISTA context + effective capabilities",
                "description": (
                    "Specialist context: assistant identity, principal type, "
                    "effectiveCapabilities (derived from real AuthZ — catalog "
                    "informs, never grants), confirmation model, catalogVersion. "
                    "action=catalog returns the full canonical catalog."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "requestBody": _json_body(
                    {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["context", "catalog"],
                                "default": "context",
                            },
                        },
                    },
                    example={"action": "context"},
                ),
                "responses": {"200": _ok_response("VISTA context"), **_error_responses()},
            }
        },
        f"{base}/semantic/read": {
            "post": {
                "operationId": "vista_read",
                "summary": "Closed-vocabulary semantic read",
                "description": (
                    "READ by closed entity+action: playlist.list|get|context, "
                    "playlist_history.history, data_route.search, "
                    "data_model.inspect, product_guide.guide. BlockIndex/DataSources "
                    "coverage. Unknown entity/action -> errors."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "requestBody": _json_body(
                    {
                        "type": "object",
                        "required": ["entity", "action"],
                        "properties": {
                            "entity": {
                                "type": "string",
                                "enum": [
                                    "playlist",
                                    "playlist_history",
                                    "data_route",
                                    "data_model",
                                    "product_guide",
                                    "slide_preset",
                                    "media_asset",
                                ],
                            },
                            "action": {
                                "type": "string",
                                "enum": [
                                    "list",
                                    "get",
                                    "context",
                                    "history",
                                    "search",
                                    "inspect",
                                    "guide",
                                ],
                            },
                            "ref": {
                                "type": "string",
                                "description": (
                                    "Entity id: playlistId for playlist.get/context "
                                    "and playlist_history.history; modelId for "
                                    "data_model.inspect; topic for product_guide.guide."
                                ),
                            },
                            "filters": _opaque_object_schema(
                                description=(
                                    "Declared filter keys only per action (e.g. "
                                    "slideId, scope, snapshotId, page, query, "
                                    "playlistId, topic, section). Undeclared keys "
                                    "are rejected."
                                )
                            ),
                            "pagination": _opaque_object_schema(
                                description="Optional {limit<=100, cursor}."
                            ),
                        },
                    },
                    example={
                        "entity": "playlist",
                        "action": "list",
                        "pagination": {"limit": 20},
                    },
                ),
                "responses": {"200": _ok_response("Semantic read"), **_error_responses()},
            }
        },
        f"{base}/semantic/analyze": {
            "post": {
                "operationId": "vista_analyze",
                "summary": "Closed-vocabulary semantic analysis",
                "description": (
                    "Owner analyses that never persist: data_block_preview, "
                    "data_model_preview, intent_materialization (NL intent → "
                    "typed ops candidates for the governed envelope). "
                    "Response carries evidenceClass (preview|calculation)."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "requestBody": _json_body(
                    {
                        "type": "object",
                        "required": ["analysis"],
                        "properties": {
                            "analysis": {
                                "type": "string",
                                "enum": [
                                    "data_block_preview",
                                    "data_model_preview",
                                    "intent_materialization",
                                ],
                            },
                            "subjectRefs": _opaque_object_schema(
                                description=(
                                    "Authoritative refs: playlistId, slideId, "
                                    "blockId, modelId, hostContext fields."
                                )
                            ),
                            "parameters": _opaque_object_schema(
                                description=(
                                    "Per-analysis params (operationId/params for "
                                    "data_block_preview; model/nativeConfig for "
                                    "data_model_preview; message for "
                                    "intent_materialization)."
                                )
                            ),
                        },
                    },
                    example={
                        "analysis": "intent_materialization",
                        "subjectRefs": {"playlistId": "uuid"},
                        "parameters": {"message": "Crie um slide de OTD"},
                    },
                ),
                "responses": {"200": _ok_response("Semantic analysis"), **_error_responses()},
            }
        },
        f"{base}/semantic/knowledge": {
            "post": {
                "operationId": "vista_knowledge",
                "summary": "Canonical product knowledge",
                "description": (
                    "Product guide registry (GUIDANCE_NOT_DOMAIN_TRUTH). "
                    "action=get: one guide by topic (+optional section); "
                    "omit topic for the index. action=search: bounded "
                    "deterministic index projection filtered by query."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "requestBody": _json_body(
                    {
                        "type": "object",
                        "required": ["action"],
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["search", "get"],
                            },
                            "topic": {"type": "string"},
                            "section": {
                                "type": "string",
                                "enum": [
                                    "overview",
                                    "when_to_use",
                                    "how_to_use",
                                    "field_guidance",
                                    "quality",
                                    "relationships",
                                    "all",
                                ],
                            },
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "default": 20},
                        },
                    },
                    example={"action": "search", "query": "playlist"},
                ),
                "responses": {"200": _ok_response("Knowledge"), **_error_responses()},
            }
        },
        f"{base}/semantic/execute": {
            "post": {
                "operationId": "vista_execute",
                "summary": "Governed mutation — PREPARE→COMMIT facade",
                "description": (
                    "Governed mutation facade (entity=presentation, "
                    "action=apply_mutation). phase=prepare: operations[] + "
                    "target → sealed proposal_handle (+consentChallenge when "
                    "confirm). phase=commit: proposal_handle + idempotency "
                    "+ consent_artifact + target_echo. Never re-send "
                    "operations[] at commit (PLAN_MISMATCH)."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "x-openai-isConsequential": True,
                "parameters": [
                    {
                        "name": "Idempotency-Key",
                        "in": "header",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": (
                            "Required for phase=commit (or commit_now) — or "
                            "use body idempotency_key. Atomic acquire before "
                            "write; same key+payload replays."
                        ),
                    }
                ],
                "requestBody": _json_body(
                    {
                        "type": "object",
                        "required": ["entity", "action"],
                        "properties": {
                            "entity": {
                                "type": "string",
                                "enum": ["presentation"],
                            },
                            "action": {
                                "type": "string",
                                "enum": ["apply_mutation"],
                            },
                            "phase": {
                                "type": "string",
                                "enum": ["prepare", "commit"],
                                "default": "prepare",
                            },
                            "target": {
                                "$ref": "#/components/schemas/GptChangeTarget"
                            },
                            "operations": typed_ops,
                            "proposal_handle": {
                                "type": "string",
                                "description": (
                                    "phase=commit: exact opaque handle from "
                                    "prepare — binds the sealed plan."
                                ),
                            },
                            "consent_artifact": {
                                "type": "string",
                                "description": (
                                    "phase=commit on confirm plans: consent "
                                    "challenge id approved by the human via "
                                    "the trusted channel. No boolean "
                                    "substitute exists on this surface."
                                ),
                            },
                            "target_echo": {
                                "type": "string",
                                "description": (
                                    "phase=commit on confirm plans: exact "
                                    "consentChallenge.targetRef — target "
                                    "identity check, never consent proof."
                                ),
                            },
                            "idempotency_key": {"type": "string"},
                            "catalogVersion": {"type": "string"},
                            "commit_now": {
                                "type": "boolean",
                                "default": False,
                                "description": (
                                    "Actions-only: phase=prepare commits "
                                    "inline when every op policy is direct. "
                                    "Ignored for confirm plans."
                                ),
                            },
                        },
                    },
                    example={
                        "entity": "presentation",
                        "action": "apply_mutation",
                        "phase": "prepare",
                        "target": {},
                        "operations": create_ops,
                        "catalogVersion": catalog_version,
                    },
                ),
                "responses": {
                    "200": _ok_response("Sealed proposal or verified commit"),
                    **_error_responses(),
                },
            }
        },
        f"{base}/semantic/delete": {
            "post": {
                "operationId": "vista_delete",
                "summary": "Governed delete — PREPARE→COMMIT facade",
                "description": (
                    "Destructive ops only (entity in block|section|slide). "
                    "phase=prepare: entity + target -> sealed proposal_handle "
                    "+ consentChallenge. phase=commit: proposal_handle + "
                    "idempotency_key + consent_artifact + target_echo. Only "
                    "the artifact proves consent."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "x-openai-isConsequential": True,
                "parameters": [
                    {
                        "name": "Idempotency-Key",
                        "in": "header",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": (
                            "Required for phase=commit — or use body "
                            "idempotency_key."
                        ),
                    }
                ],
                "requestBody": _json_body(
                    {
                        "type": "object",
                        "required": ["entity"],
                        "properties": {
                            "entity": {
                                "type": "string",
                                "enum": ["block", "section", "slide"],
                            },
                            "phase": {
                                "type": "string",
                                "enum": ["prepare", "commit"],
                                "default": "prepare",
                            },
                            "target": _opaque_object_schema(
                                description="playlistId + entity id " +
                                "(slideId|sectionId|blockId); " +
                                "deleteSlides optional for section."
                            ),
                            "proposal_handle": {"type": "string"},
                            "consent_artifact": {"type": "string"},
                            "target_echo": {"type": "string"},
                            "idempotency_key": {"type": "string"},
                            "catalogVersion": {"type": "string"},
                        },
                    },
                    example={
                        "entity": "slide",
                        "phase": "prepare",
                        "target": {"playlistId": "<uuid>", "slideId": "<uuid>"},
                        "catalogVersion": catalog_version,
                    },
                ),
                "responses": {
                    "200": _ok_response("Sealed proposal or verified commit"),
                    **_error_responses(),
                },
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
                "and writes remains TV. Legacy gpt_* Actions under "
                "GOVERNED_PREPARE_COMMIT_V2 coexist with the vista_* semantic "
                "verbs (SEMANTIC_TOOLS_V1); openapi.json is import-only and "
                "not listed here."
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
