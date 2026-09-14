"""Build the compact OpenAPI 3.1 schema for OpenAI Custom GPT Actions (TV)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tv_app.application.gpt_actions import (
    GPT_ACTIONS_BASE_PATH,
    GPT_ACTIONS_GATEWAY_ROOT,
    GPT_ACTIONS_OPERATION_IDS,
    GPT_ACTIONS_PUBLIC_FALLBACK_ORIGIN,
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
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "retryable": {"type": "boolean"},
                    "details": {"type": "object"},
                },
            },
            "meta": {
                "type": "object",
                "properties": {"correlationId": {"type": "string"}},
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


def build_gpt_actions_openapi(*, server_url: str | None = None) -> dict[str, Any]:
    if not server_url or not str(server_url).startswith(("http://", "https://")):
        server_url = resolve_gpt_actions_server_url(explicit=server_url)
    base = GPT_ACTIONS_BASE_PATH
    tag = "TV Dashboard GPT"
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
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["block", "nativeConfig"],
                                "properties": {
                                    "block": {"type": "object"},
                                    "nativeConfig": {"type": "object"},
                                    "playlistId": {"type": "string"},
                                    "playlistDefaults": {"type": "object"},
                                    "forceRefresh": {"type": "boolean"},
                                    "targetStepName": {"type": "string"},
                                    "previewOptions": {"type": "object"},
                                },
                            }
                        }
                    },
                },
                "responses": {"200": _ok_response("Block preview"), **_error_responses()},
            }
        },
        f"{base}/changes/suggest": {
            "post": {
                "operationId": "gpt_suggest_change",
                "summary": "Suggest typed Copilot ops from NL",
                "description": (
                    "Uses the canonical Copilot planner. Returns ready|clarification|"
                    "unsupported|error with typed ops — no free M/SQL."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["message"],
                                "properties": {
                                    "message": {"type": "string"},
                                    "hostContext": {"type": "object"},
                                },
                            }
                        }
                    },
                },
                "responses": {"200": _ok_response("Suggestion plan"), **_error_responses()},
            }
        },
        f"{base}/changes/preview": {
            "post": {
                "operationId": "gpt_preview_change",
                "summary": "Preview typed change without persisting",
                "description": (
                    "Dry-run TvCopilotPatchV1. Returns planDigest, risk, confirmationPolicy, "
                    "diff. Does not persist. Does not expose httpCommands."
                ),
                "tags": [tag],
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["ops"],
                                "properties": {
                                    "target": {"type": "object"},
                                    "ops": {"type": "array", "items": {"type": "object"}},
                                    "catalogVersion": {"type": "string"},
                                },
                            }
                        }
                    },
                },
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
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["ops", "catalogVersion", "planDigest"],
                                "properties": {
                                    "target": {"type": "object"},
                                    "ops": {
                                        "type": "array",
                                        "items": {"type": "object"},
                                        "description": (
                                            "Typed Copilot ops from gpt_preview_change "
                                            "(objects with op field — never string names)."
                                        ),
                                    },
                                    "catalogVersion": {"type": "string"},
                                    "expectedRevision": {
                                        "type": "integer",
                                        "description": (
                                            "Required OCC revision for existing playlist. "
                                            "Omit only when creating a new playlist without "
                                            "playlistId. Missing on existing playlist → 422."
                                        ),
                                    },
                                    "planDigest": {"type": "string"},
                                },
                            }
                        }
                    },
                },
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
                # Compat alias
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
