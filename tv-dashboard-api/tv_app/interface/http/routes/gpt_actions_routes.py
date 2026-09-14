"""HTTP surface for OpenAI Custom GPT Actions (TV Dashboard)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from tv_app.application.gpt_actions import GPT_ACTIONS_BASE_PATH, GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi,
    resolve_gpt_actions_server_url,
)
from tv_app.config import settings
from tv_app.core.responses import ok
from tv_app.core.serialize import json_safe
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix=GPT_ACTIONS_BASE_PATH, tags=["TV Dashboard GPT Actions"])
logger = logging.getLogger(__name__)
_dispatch = GptActionsDispatchService()


class SuggestBody(BaseModel):
    message: str = Field(min_length=1)
    hostContext: dict[str, Any] | None = None


class PreviewChangeBody(BaseModel):
    target: dict[str, Any] | None = None
    ops: list[dict[str, Any]] = Field(default_factory=list)
    catalogVersion: str | None = None


class CommitChangeBody(BaseModel):
    target: dict[str, Any] | None = None
    ops: list[dict[str, Any]] = Field(default_factory=list)
    catalogVersion: str
    expectedRevision: int | None = None
    planDigest: str


class DataPreviewBody(BaseModel):
    block: dict[str, Any]
    nativeConfig: dict[str, Any]
    playlistId: str | None = None
    playlistDefaults: dict[str, Any] | None = None
    forceRefresh: bool = False
    targetStepName: str | None = None
    previewOptions: dict[str, Any] | None = None


def _correlation_id(request: Request) -> str:
    raw = (
        request.headers.get("x-correlation-id")
        or request.headers.get("X-Correlation-Id")
        or ""
    ).strip()
    return raw or str(uuid.uuid4())


def gpt_fail(
    *,
    code: str,
    message: str,
    status_code: int,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                "retryable": bool(retryable),
                "details": json_safe(details or {}),
            },
            "meta": {"correlationId": correlation_id or str(uuid.uuid4())},
        },
    )


def _handle(exc: Exception, *, correlation_id: str):
    if isinstance(exc, GptActionsError):
        return gpt_fail(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            retryable=exc.retryable,
            details=exc.details,
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
def get_playlist_context(request: Request, playlist_id: str):
    cid = _correlation_id(request)
    try:
        data = _dispatch.get_playlist_context(
            user=resolve_user(request),
            playlist_id=playlist_id,
        )
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)


@router.get("/data-routes")
def search_data_routes(
    request: Request,
    query: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
):
    cid = _correlation_id(request)
    try:
        data = _dispatch.search_data_routes(
            user=resolve_user(request),
            query=query,
            limit=limit,
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
def preview_change(request: Request, body: PreviewChangeBody):
    cid = _correlation_id(request)
    try:
        data = _dispatch.preview_change(
            user=resolve_user(request),
            target=body.target,
            ops=body.ops,
            catalog_version=body.catalogVersion,
            authorization=request.headers.get("Authorization"),
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
            target=body.target,
            ops=body.ops,
            catalog_version=body.catalogVersion,
            expected_revision=body.expectedRevision,
            plan_digest=body.planDigest,
            idempotency_key=idempotency_key or "",
            authorization=request.headers.get("Authorization"),
        )
        return ok(data, message="Commit verificado.")
    except Exception as exc:  # noqa: BLE001
        return _handle(exc, correlation_id=cid)
