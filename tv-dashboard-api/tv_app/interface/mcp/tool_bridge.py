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
from tv_app.infrastructure.gateways.core_solution_catalog_gateway import (
    CoreSolutionCatalogGateway,
)
from tv_app.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository
from tv_app.infrastructure.persistence.repositories.playlist_history_repository import (
    PlaylistHistoryRepository,
)
from tv_app.infrastructure.persistence.repositories.vista_consent_challenge_repository import (
    get_vista_consent_challenge_repository,
)
from tv_app.application.gpt_actions.vista_consent_service import (
    VistaConsentService,
)

from .oauth_contract import build_www_authenticate_challenge

logger = logging.getLogger(__name__)

_repo = PlaylistRepository()
_writes = TvPresentationWriteService(repo=_repo)
_consent = VistaConsentService(challenges=get_vista_consent_challenge_repository())
_commit = TvGptCommitService(
    writes=_writes,
    idempotency=PostgresIdempotencyRepository(),
    consent=_consent,
)
_solutions = CoreSolutionCatalogGateway()
_history = PlaylistHistoryRepository()
_dispatch = GptActionsDispatchService(
    repo=_repo, writes=_writes, commit=_commit, solutions=_solutions,
    history=_history, consent=_consent,
)


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


_MCP_IMAGE_MAX_BYTES = 8_000_000


def _canonical_stage_image(data: dict) -> Any | None:
    """Exact revision-bound canonical_stage bytes as MCP ImageContent.

    Additive projection only — the text/structured payload is unchanged. Any
    miss (no ready artifact, stale revision, oversized bytes) degrades to the
    normal text-only result; the model must never receive a schematic PNG
    presented as canonical pixels.
    """
    import base64

    from mcp.types import ImageContent

    preview = data.get("slidePreview")
    if not isinstance(preview, dict):
        return None
    rendered = preview.get("rendered")
    if not isinstance(rendered, dict):
        return None
    if (
        rendered.get("status") != "ready"
        or rendered.get("kind") != "canonical_stage"
        or rendered.get("mimeType") != "image/png"
        # VISTA visual evidence only comes from the user's live editor stage —
        # cached/offscreen artifacts never project as canonical pixels.
        or rendered.get("source") != "editor_live"
    ):
        return None
    slide_id = str(preview.get("slideId") or "").strip()
    revision = rendered.get("revision")
    if not slide_id or revision is None:
        return None
    from tv_app.application.services.data.slide_preview_render_service import (
        get_slide_preview_render_service,
    )

    png = get_slide_preview_render_service().read_rendered_png(
        slide_id=slide_id,
        revision=revision,
    )
    if not png or len(png) > _MCP_IMAGE_MAX_BYTES:
        return None
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return ImageContent(
        type="image",
        data=base64.b64encode(png).decode("ascii"),
        mime_type="image/png",
    )


def _ok_result(data: dict, *, images: list[Any] | None = None) -> CallToolResult:
    payload = {"status": "success", "data": data}
    return mcp_tool_result(payload, is_error=False, images=images)


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


def tool_execute(
    entity: str,
    action: str,
    operations: list | None = None,
    phase: str | None = None,
    target: dict | None = None,
    proposal_handle: str | None = None,
    consent_artifact: str | None = None,
    target_echo: str | None = None,
    idempotency_key: str | None = None,
    catalog_version: str | None = None,
) -> CallToolResult:
    """Semantic execute — closed facade over PREPARE→COMMIT.

    ``phase=prepare``: ``entity="presentation"`` +
    ``action="apply_mutation"`` + ``operations[]`` (typed ops,
    ``{op, args?, as?}``) + optional ``target`` → sealed proposal;
    emits ``consentChallenge`` when the plan policy is ``confirm``.

    ``phase=commit``: exact ``proposal_handle`` + ``idempotency_key`` +
    ``consent_artifact`` approved via the trusted channel
    (``/vista/consent/...``) + ``target_echo`` for confirm plans —
    operations[] is never re-sent (plan substitution → PLAN_MISMATCH)
    and there is no confirmation boolean on this surface: only the
    artifact proves human consent.
    """
    try:
        user, auth = _authed_context()
        return _ok_result(
            _dispatch.semantic_execute(
                user=user,
                entity=entity,
                action=action,
                phase=phase,
                target=target,
                operations=operations,
                proposal_handle=proposal_handle,
                consent_artifact=consent_artifact,
                target_echo=target_echo,
                idempotency_key=idempotency_key,
                catalog_version=catalog_version,
                authorization=auth,
                transport="mcp",
            )
        )
    except Exception as e:
        return handle_tool_error(e, tool="execute", label="mcp tool")


def tool_delete(
    entity: str,
    phase: str | None = None,
    target: dict | None = None,
    proposal_handle: str | None = None,
    consent_artifact: str | None = None,
    target_echo: str | None = None,
    idempotency_key: str | None = None,
    catalog_version: str | None = None,
) -> CallToolResult:
    """Semantic delete — governed destructive ops (block|section|slide).

    ``phase=prepare``: ``entity`` + ``target`` (playlistId + entity id;
    ``deleteSlides`` optional for section) → sealed proposal +
    ``consentChallenge``. ``phase=commit``: ``proposal_handle`` +
    ``idempotency_key`` + approved ``consent_artifact`` +
    ``target_echo`` — no confirmation boolean exists on this surface.
    """
    try:
        user, auth = _authed_context()
        return _ok_result(
            _dispatch.semantic_delete(
                user=user,
                entity=entity,
                phase=phase,
                target=target,
                proposal_handle=proposal_handle,
                consent_artifact=consent_artifact,
                target_echo=target_echo,
                idempotency_key=idempotency_key,
                catalog_version=catalog_version,
                authorization=auth,
                transport="mcp",
            )
        )
    except Exception as e:
        return handle_tool_error(e, tool="delete", label="mcp tool")


# ---------------------------------------------------------------------------
# SEMANTIC_TOOLS_V1 — six-verb semantic surface (coexists with the 12 above).
# Same adapter discipline: context rebuild + delegation to the same dispatch.
# ---------------------------------------------------------------------------


def tool_get_context(action: str = "context") -> CallToolResult:
    """DISCOVERY — specialist context + effective capabilities.

    action=context: assistant identity, principal, effectiveCapabilities
    (derived from real AuthZ, never the catalog), confirmation model.
    action=catalog: the full canonical capability catalog.
    """
    try:
        user, _ = _authed_context()
        return _ok_result(
            _dispatch.semantic_get_context(user=user, action=action, transport="mcp")
        )
    except Exception as e:
        return handle_tool_error(e, tool="get_context", label="mcp tool")


def tool_read(
    entity: str,
    action: str,
    ref: str | None = None,
    filters: dict | None = None,
    pagination: dict | None = None,
) -> CallToolResult:
    """READ — closed (entity, action) vocabulary over canonical handlers.

    Entities: playlist (list|get|context), playlist_history (history),
    data_route (search), data_model (inspect), product_guide (guide).
    Unknown entity/action or undeclared filter key fails typed.
    """
    try:
        user, auth = _authed_context()
        out = _dispatch.semantic_read(
            user=user,
            entity=entity,
            action=action,
            ref=ref,
            filters=filters if isinstance(filters, dict) else None,
            pagination=pagination if isinstance(pagination, dict) else None,
            authorization=auth,
        )
        images: list[Any] | None = None
        if isinstance(out, dict):
            img = _canonical_stage_image(out)
            if img is not None:
                images = [img]
        return _ok_result(out, images=images)
    except Exception as e:
        return handle_tool_error(e, tool="read", label="mcp tool")


def tool_analyze(
    analysis: str,
    subject_refs: dict | None = None,
    parameters: dict | None = None,
) -> CallToolResult:
    """ANALYSIS — closed analysis vocabulary; never persists.

    Analyses: data_block_preview, data_model_preview,
    intent_materialization (NL intent → typed ops candidates).
    Response carries evidenceClass (preview|calculation).
    """
    try:
        user, auth = _authed_context()
        return _ok_result(
            _dispatch.semantic_analyze(
                user=user,
                analysis=analysis,
                subject_refs=subject_refs if isinstance(subject_refs, dict) else None,
                parameters=parameters if isinstance(parameters, dict) else None,
                authorization=auth,
            )
        )
    except Exception as e:
        return handle_tool_error(e, tool="analyze", label="mcp tool")


def tool_knowledge(
    action: str,
    topic: str | None = None,
    section: str | None = None,
    query: str | None = None,
    limit: int = 20,
) -> CallToolResult:
    """READ — canonical product-guide registry (GUIDANCE_NOT_DOMAIN_TRUTH).

    action=get: one guide by topic (+optional section); omit topic for the
    index. action=search: bounded deterministic index projection filtered
    by query.
    """
    try:
        user, _ = _authed_context()
        return _ok_result(
            _dispatch.semantic_knowledge(
                user=user,
                action=action,
                topic=topic,
                section=section,
                query=query,
                limit=limit,
            )
        )
    except Exception as e:
        return handle_tool_error(e, tool="knowledge", label="mcp tool")


def list_tool_names() -> list[str]:
    return [t.name for t in _iter_registered_tools()]


def _iter_registered_tools() -> list[_Tool]:
    from .server import create_mcp_server

    mcp = create_mcp_server()
    return list(mcp._tool_manager.list_tools())
