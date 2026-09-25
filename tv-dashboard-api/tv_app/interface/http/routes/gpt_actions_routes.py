"""HTTP surface for OpenAI Custom GPT Actions (TV Dashboard)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, Query, Request
from pydantic import BaseModel, Field

from tv_app.application.gpt_actions import GPT_ACTIONS_BASE_PATH, GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID
from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi,
    resolve_gpt_actions_server_url,
)
from tv_app.application.services.tv_presentation_write_service import TvPresentationWriteService
from tv_app.config import settings
from tv_app.core.responses import ok
from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
    PostgresIdempotencyRepository,
)
from tv_app.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository
from tv_app.interface.http.auth_http import resolve_user
from tv_app.interface.http.gpt_actions_response import (
    correlation_id_from_request,
    gpt_fail,
)

router = APIRouter(prefix=GPT_ACTIONS_BASE_PATH, tags=["TV Dashboard GPT Actions"])
logger = logging.getLogger(__name__)

_repo = PlaylistRepository()
_writes = TvPresentationWriteService(repo=_repo)
_idempotency = PostgresIdempotencyRepository()
_commit = TvGptCommitService(writes=_writes, idempotency=_idempotency)
_dispatch = GptActionsDispatchService(repo=_repo, writes=_writes, commit=_commit)


class SuggestBody(BaseModel):
    message: str = Field(min_length=1)
    hostContext: dict[str, Any] | None = None


class PreviewChangeBody(BaseModel):
    target: dict[str, Any] | None = None
    ops: list[dict[str, Any]] = Field(default_factory=list)
    catalogVersion: str | None = None
    commit_now: bool = False
    confirmation: dict[str, Any] | bool | None = None
    idempotency_key: str | None = None


class CommitChangeBody(BaseModel):
    proposal_handle: str = Field(min_length=1)
    confirmation: dict[str, Any] | bool
    idempotency_key: str | None = None


class DataPreviewBody(BaseModel):
    operationId: str | None = None
    params: dict[str, Any] | None = None
    block: dict[str, Any] | None = None
    nativeConfig: dict[str, Any] | None = None
    playlistId: str | None = None
    playlistDefaults: dict[str, Any] | None = None
    forceRefresh: bool = False
    targetStepName: str | None = None
    previewOptions: dict[str, Any] | None = None


def _correlation_id(request: Request) -> str:
    return correlation_id_from_request(request)


def _handle(exc: Exception, *, correlation_id: str):
    if isinstance(exc, GptActionsError):
        from tv_app.application.gpt_actions.response_compact import (
            project_mutation_actions_payload,
            strip_heavy_mutation_blobs,
        )

        details = exc.details
        if isinstance(details, dict):
            details = project_mutation_actions_payload(details)
        elif details is not None:
            details = strip_heavy_mutation_blobs(details)
        return gpt_fail(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            retryable=exc.retryable,
            details=details if isinstance(details, dict) else None,
            correlation_id=correlation_id,
        )
    if isinstance(exc, PermissionError):
        return gpt_fail(
            code="PERMISSION_DENIED",
            message=str(exc) or "Permissão negada.",
            status_code=403,
            correlation_id=correlation_id,
        )
    if isinstance(exc, LookupError):
        return gpt_fail(
            code="RESOURCE_NOT_FOUND",
            message=str(exc) or "Recurso não encontrado.",
            status_code=404,
            correlation_id=correlation_id,
        )
    if isinstance(exc, ValueError):
        return gpt_fail(
            code="INVALID_CHANGE",
            message=str(exc),
            status_code=422,
            correlation_id=correlation_id,
        )
    logger.exception("gpt_actions_unhandled")
    return gpt_fail(
        code="UPSTREAM_FAILURE",
        message="Erro interno ao processar Action.",
        status_code=500,
        retryable=True,
        correlation_id=correlation_id,
    )


@router.get(
    "/openapi.json",
    operation_id=GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID,
    summary="Public OpenAPI schema for Custom GPT import",
)
def get_openapi_schema():
    server_url = resolve_gpt_actions_server_url(
        public_base_url=settings.PUBLIC_BASE_URL,
        root_path=settings.TV_DASHBOARD_API_ROOT_PATH,
    )
    return build_gpt_actions_openapi(server_url=server_url)


@router.get("/catalog")
def get_catalog(request: Request):
    cid = _correlation_id(request)
    try:
        data = _dispatch.get_catalog(user=resolve_user(request))
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)


@router.get("/playlists")
def list_playlists(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    cid = _correlation_id(request)
    try:
        data = _dispatch.list_playlists(
            user=resolve_user(request),
            limit=limit,
            offset=offset,
        )
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)


@router.get("/playlists/{playlist_id}")
def get_playlist_context(
    request: Request,
    playlist_id: str,
    includePreview: bool = Query(
        default=False,
        description="When true, include slidePreview (signed PNG URL) for one slide.",
    ),
    slideId: str | None = Query(
        default=None,
        description="Slide UUID to expand as focusedSlide (and for includePreview). Defaults to editorFocus.slideId or the first slide.",
    ),
    scope: str | None = Query(
        default="full",
        description=(
            "full: nativeConfig + digests. editorFocus: dataSources + blockIndex "
            "without nativeConfig (auto-downgrade uses the same)."
        ),
    ),
    objectQuery: str | None = Query(
        default=None,
        description="Optional filter for objectMatches[] from persisted blockIndex.",
    ),
    objectTypes: str | None = Query(
        default=None,
        description="Optional comma-separated block types filter for blockIndex/objectMatches.",
    ),
    blockCursor: str | None = Query(
        default=None,
        description="Pagination cursor (absolute offset) for blockIndex.items.",
    ),
    blockLimit: int | None = Query(
        default=None,
        description="Max blockIndex.items in this page (server-capped).",
    ),
):
    cid = _correlation_id(request)
    try:
        data = _dispatch.get_playlist_context(
            user=resolve_user(request),
            playlist_id=playlist_id,
            include_preview=bool(includePreview),
            preview_slide_id=slideId,
            scope=scope,
            object_query=objectQuery,
            object_types=objectTypes,
            block_cursor=blockCursor,
            block_limit=blockLimit,
        )
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)


@router.get("/slide-previews/{token}")
def get_slide_preview_png(request: Request, token: str):
    """Serve schematic PNG. Signed token = AuthZ (short TTL); Bearer optional."""
    from fastapi.responses import Response

    cid = _correlation_id(request)
    try:
        user = None
        auth = (request.headers.get("authorization") or "").strip()
        if auth.lower().startswith("bearer "):
            user = resolve_user(request)
        png, _meta = _dispatch.get_slide_preview_png(user=user, token=token)
        return Response(
            content=png,
            media_type="image/png",
            headers={
                "Cache-Control": "private, max-age=60",
                "X-Correlation-Id": cid,
            },
        )
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)


@router.get("/data-routes")
def search_data_routes(
    request: Request,
    query: str = Query(..., min_length=1, description="Business intent NL query (required)"),
    limit: int = Query(default=8, ge=1, le=20),
    category: str | None = Query(default=None, description="Optional catalog category filter"),
):
    cid = _correlation_id(request)
    try:
        data = _dispatch.search_data_routes(
            user=resolve_user(request),
            query=query,
            limit=limit,
            category=category,
        )
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)


@router.post("/data-preview")
def preview_data_block(request: Request, body: DataPreviewBody):
    cid = _correlation_id(request)
    try:
        data = _dispatch.preview_data_block(
            user=resolve_user(request),
            body=body.model_dump(),
            authorization=request.headers.get("Authorization"),
        )
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)


@router.post("/changes/suggest")
def suggest_change(request: Request, body: SuggestBody):
    cid = _correlation_id(request)
    try:
        data = _dispatch.suggest_change(
            user=resolve_user(request),
            message=body.message,
            host_context=body.hostContext,
            authorization=request.headers.get("Authorization"),
        )
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)


@router.post("/changes/preview")
def preview_change(
    request: Request,
    body: PreviewChangeBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    cid = _correlation_id(request)
    try:
        data = _dispatch.preview_change(
            user=resolve_user(request),
            target=body.target,
            ops=body.ops,
            catalog_version=body.catalogVersion,
            authorization=request.headers.get("Authorization"),
            commit_now=bool(body.commit_now),
            confirmation=body.confirmation,
            idempotency_key=(idempotency_key or body.idempotency_key or ""),
        )
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)


@router.post("/changes/commit")
def commit_change(
    request: Request,
    body: CommitChangeBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    cid = _correlation_id(request)
    try:
        data = _dispatch.commit_change(
            user=resolve_user(request),
            proposal_handle=body.proposal_handle,
            confirmation=body.confirmation,
            idempotency_key=(idempotency_key or body.idempotency_key or ""),
            authorization=request.headers.get("Authorization"),
        )
        return ok(data, message="Commit verificado.")
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)
