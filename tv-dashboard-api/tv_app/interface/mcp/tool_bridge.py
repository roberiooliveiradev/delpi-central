"""Tool implementations for FastMCP — adapter over GptActionsDispatchService.

The MCP layer translates protocol + context only. Every tool rebuilds the
request/user/authorization context from the shared delpi_auth ContextVars and
delegates to the canonical application dispatch — the same object the HTTP
`/gpt-actions` surface uses. No business logic, AuthZ, persistence, or
allowlist lives here.
"""

from __future__ import annotations

import logging
from typing import Any

from delpi_mcp.errors import kind_for_http_status, mcp_tool_result
from delpi_mcp.identity import (
    build_mcp_request as _shared_build_request,
    current_mcp_context,
)
from fastapi import Request
from mcp.types import CallToolResult, Tool as _Tool
from mcp.server.mcpserver.exceptions import ToolError

from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.services.tv_presentation_write_service import (
    PresentationWriteError,
    TvPresentationWriteService,
)
from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
    PostgresIdempotencyRepository,
)
from tv_app.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository

from .oauth_contract import build_www_authenticate_challenge

logger = logging.getLogger(__name__)

_repo = PlaylistRepository()
_writes = TvPresentationWriteService(repo=_repo)
_commit = TvGptCommitService(writes=_writes, idempotency=PostgresIdempotencyRepository())
_dispatch = GptActionsDispatchService(repo=_repo, writes=_writes, commit=_commit)


def build_mcp_request() -> tuple[Request, Any, str]:
    """Reconstruct the request context expected by application services.

    Reads the shared delpi_auth ContextVars populated by the OAuth-bearing MCP
    HTTP middleware — never forges identity or permissions. S4: scope/header
    reconstruction delegated to delpi_mcp.identity.
    """
    context = current_mcp_context()
    request = _shared_build_request(
        context=context,
        server=("tv-dashboard-api", 443),
        client=("mcp-bridge", 0),
        extra_headers={"mcp-context": "tv-dashboard"},
    )
    return request, context.user, context.authorization


def _authed_context() -> tuple[Any, str]:
    """Return (user, authorization) or fail the call with 401 semantics."""
    _, user, auth = build_mcp_request()
    if user is None:
        raise PermissionError("Unauthorized")
    return user, auth


def _ok_result(data: dict) -> CallToolResult:
    payload = {"status": "success", "data": data}
    return mcp_tool_result(payload, is_error=False)


def _kind_for_status(status: int) -> str:
    return kind_for_http_status(status)


def _error_result(
    *,
    status: str,
    http_status: int,
    error_kind: str,
    code: str,
    message: str,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> CallToolResult:
    err: dict[str, Any] = {
        "status": status,
        "httpStatus": http_status,
        "error_kind": error_kind,
        "code": code,
        "message": message,
    }
    if retryable:
        err["retryable"] = True
    if details:
        err["details"] = dict(details)
    meta = None
    if http_status == 401:
        meta = {"mcp/www_authenticate": build_www_authenticate_challenge()}
    return mcp_tool_result(err, is_error=True, meta=meta)


def handle_tool_error(exc: Exception, *, tool: str, label: str) -> CallToolResult:
    """Translate exceptions into MCP-safe structured errors.

    Preserves `GptActionsError` codes verbatim (application/domain codes such
    as `data_model.not_found`, `m.unknown_column`, `INVALID_CHANGE` are the
    contract). Generic errors never leak internals; logs carry exception type
    and tool label only — never payload arguments or tokens.
    """
    if isinstance(exc, ToolError):
        raise exc
    if isinstance(exc, PermissionError):
        unauthorized = str(exc).strip() == "Unauthorized"
        return _error_result(
            status="unauthenticated" if unauthorized else "forbidden",
            http_status=401 if unauthorized else 403,
            error_kind="unauthenticated" if unauthorized else "forbidden",
            code="AUTHENTICATION_REQUIRED" if unauthorized else "FORBIDDEN",
            message="Autenticação necessária." if unauthorized else str(exc),
        )
    if isinstance(exc, GptActionsError):
        http_status = exc.status_code if 400 <= exc.status_code <= 599 else 400
        return _error_result(
            status="error",
            http_status=http_status,
            error_kind=_kind_for_status(http_status),
            code=exc.code,
            message=str(exc),
            retryable=exc.retryable,
            details=exc.details or None,
        )
    # PresentationWriteError carries typed code/status (e.g. REVISION_CONFLICT,
    # DATA_BINDING_FIELD_MISSING) — preserve them; the HTTP surface collapses
    # these into UPSTREAM_FAILURE, but MCP keeps the canonical typed domain code.
    if isinstance(exc, PresentationWriteError):
        http_status = exc.status_code if 400 <= exc.status_code <= 599 else 400
        return _error_result(
            status="error",
            http_status=http_status,
            error_kind=_kind_for_status(http_status),
            code=exc.code or "INVALID_CHANGE",
            message=str(exc),
            details=exc.details or None,
        )
    if isinstance(exc, LookupError):
        return _error_result(
            status="error",
            http_status=404,
            error_kind="not_found",
            code="RESOURCE_NOT_FOUND",
            message=str(exc) or "Recurso não encontrado.",
        )
    if isinstance(exc, ValueError):
        return _error_result(
            status="error",
            http_status=422,
            error_kind="validation",
            code="INVALID_CHANGE",
            message=str(exc),
        )
    logger.exception("%s failed: %s (%s)", label, type(exc).__name__, tool)
    return _error_result(
        status="error",
        http_status=500,
        error_kind="internal",
        code="INTERNAL_ERROR",
        message="Falha interna na tool.",
    )


def tool_list_playlists(limit: int = 50, offset: int = 0) -> CallToolResult:
    try:
        user, _ = _authed_context()
        return _ok_result(_dispatch.list_playlists(user=user, limit=limit, offset=offset))
    except Exception as e:
        return handle_tool_error(e, tool="list_playlists", label="mcp tool")


def tool_get_playlist_context(
    playlist_id: str,
    slide_id: str | None = None,
    include_preview: bool = False,
    scope: str | None = None,
    data_source_id: str | None = None,
    include_runtime: bool = False,
) -> CallToolResult:
    try:
        user, auth = _authed_context()
        return _ok_result(
            _dispatch.get_playlist_context(
                user=user,
                playlist_id=playlist_id,
                include_preview=include_preview,
                preview_slide_id=slide_id,
                scope=scope,
                data_source_id=data_source_id,
                include_runtime=include_runtime,
                authorization=auth,
            )
        )
    except Exception as e:
        return handle_tool_error(e, tool="get_playlist_context", label="mcp tool")


def tool_get_catalog() -> CallToolResult:
    try:
        user, _ = _authed_context()
        return _ok_result(_dispatch.get_catalog(user=user, transport="mcp"))
    except Exception as e:
        return handle_tool_error(e, tool="get_catalog", label="mcp tool")


def tool_search_data_routes(
    query: str,
    limit: int = 8,
    category: str | None = None,
) -> CallToolResult:
    try:
        user, _ = _authed_context()
        return _ok_result(
            _dispatch.search_data_routes(
                user=user, query=query, limit=limit, category=category
            )
        )
    except Exception as e:
        return handle_tool_error(e, tool="search_data_routes", label="mcp tool")


def tool_inspect_data_model(
    playlist_id: str,
    slide_id: str,
    model_id: str,
    include_runtime: bool = True,
) -> CallToolResult:
    try:
        user, auth = _authed_context()
        return _ok_result(
            _dispatch.inspect_data_model(
                user=user,
                playlist_id=playlist_id,
                slide_id=slide_id,
                model_id=model_id,
                authorization=auth,
                include_runtime=include_runtime,
            )
        )
    except Exception as e:
        return handle_tool_error(e, tool="inspect_data_model", label="mcp tool")


def tool_preview_data_model(
    playlist_id: str | None = None,
    slide_id: str | None = None,
    model_id: str | None = None,
    model: dict | None = None,
    playlist_defaults: dict | None = None,
) -> CallToolResult:
    try:
        if model is None and not (model_id or "").strip():
            raise GptActionsError(
                "modelId (modelo persistido) ou model (candidato inline) é obrigatório.",
                code="INVALID_CHANGE",
                status_code=422,
            )
        body: dict[str, Any] = {}
        if playlist_id:
            body["playlistId"] = playlist_id
        if slide_id:
            body["slideId"] = slide_id
        if model is not None:
            body["model"] = model
        elif model_id:
            body["modelId"] = model_id
        if playlist_defaults is not None:
            body["playlistDefaults"] = playlist_defaults
        user, auth = _authed_context()
        return _ok_result(_dispatch.preview_data_model(user=user, body=body, authorization=auth))
    except Exception as e:
        return handle_tool_error(e, tool="preview_data_model", label="mcp tool")


# ---------------------------------------------------------------------------
# MCP2 — governed write envelope (PREPARE → proposal_handle → ACT).
# Adapter only: ops[] are canonical catalog vocabulary validated by the
# application pipeline; proposal_handle is opaque, HMAC-signed, actor-bound,
# single-use, TTL'd — owned entirely by the application layer.
# ---------------------------------------------------------------------------


def tool_prepare_change(
    target: dict | None = None,
    ops: list | None = None,
    catalog_version: str | None = None,
) -> CallToolResult:
    """Evaluate a governed candidate mutation without material persistence.

    Returns the canonical proposal payload (proposal_handle, canCommit, risk,
    confirmationPolicy, sideEffectHints, diff/candidate preview). PREPARE never
    commits — commit happens only via ``commit_proposal``.
    """
    try:
        if not isinstance(ops, list) or not ops:
            raise GptActionsError(
                "ops[] é obrigatório (vocabulary do catálogo de operações).",
                code="INVALID_CHANGE",
                status_code=422,
            )
        user, auth = _authed_context()
        return _ok_result(
            _dispatch.preview_change(
                user=user,
                target=target if isinstance(target, dict) else {},
                ops=ops,
                catalog_version=catalog_version,
                authorization=auth,
                commit_now=False,
            )
        )
    except Exception as e:
        return handle_tool_error(e, tool="prepare_change", label="mcp tool")


def tool_commit_proposal(
    proposal_handle: str,
    idempotency_key: str,
    confirmation: bool = False,
) -> CallToolResult:
    """Commit a proposal returned by ``prepare_change``.

    Caller must supply the exact opaque ``proposal_handle`` and a
    caller-owned ``idempotency_key``. ``confirmation=True`` is required
    only when the proposal's policy demands explicit user confirmation
    (confirmationPolicy=confirm / destructive); direct proposals commit
    without it. Postcondition is verified by the canonical backend
    (VERIFIED / OUTCOME_NOT_VERIFIED).
    """
    try:
        user, auth = _authed_context()
        return _ok_result(
            _dispatch.commit_change(
                user=user,
                proposal_handle=proposal_handle,
                confirmation=confirmation,
                idempotency_key=idempotency_key,
                authorization=auth,
            )
        )
    except Exception as e:
        return handle_tool_error(e, tool="commit_proposal", label="mcp tool")


def list_tool_names() -> list[str]:
    return [t.name for t in _iter_registered_tools()]


def _iter_registered_tools() -> list[_Tool]:
    from .server import create_mcp_server

    mcp = create_mcp_server()
    return list(mcp._tool_manager.list_tools())
