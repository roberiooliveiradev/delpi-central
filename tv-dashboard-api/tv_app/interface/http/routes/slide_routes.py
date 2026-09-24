from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from tv_app.application.services.comunicado_data_enrichment_service import ComunicadoDataEnrichmentService
from tv_app.application.services.playlist_access_service import PlaylistAccessService
from tv_app.application.services.presentation_change_notifier import notify_presentation_changed
from tv_app.application.services.presentation_transition_catalog import TRANSITION_STYLE_PATTERN
from tv_app.application.services.tv_presentation_write_service import (
    PresentationWriteError,
    TvPresentationWriteService,
)

from tv_app.application.services.external_url_validator_service import validate_external_url
from tv_app.core.responses import fail, ok
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistRepository,
    SlideNotFoundError,
)
from tv_app.interface.http.playlist_access_http import is_access_error, require_playlist_access
from tv_app.interface.http.playlist_revision_http import (
    parse_if_match_revision,
    revision_response_headers,
    with_revision,
)

router = APIRouter(prefix="/playlists/{playlist_id}/slides", tags=["Slides"])
_repo = PlaylistRepository()
_writes = TvPresentationWriteService(repo=_repo)
_access = PlaylistAccessService()


class CreateSlideBody(BaseModel):
    slideType: str = Field(pattern="^(native|external)$")
    title: str = Field(min_length=1, max_length=200)
    durationSec: int | None = Field(default=None)
    sortOrder: int | None = None
    nativeScreenKey: str | None = None
    nativeConfig: dict | None = None
    externalUrl: str | None = None
    externalSandbox: str | None = None
    transitionStyle: str | None = Field(default=None, pattern=TRANSITION_STYLE_PATTERN)
    sectionId: UUID | None = None

    @field_validator("durationSec")
    @classmethod
    def validate_duration_sec(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 5 or value > 600:
            raise ValueError("Duração deve estar entre 5 e 600 segundos.")
        return value

    @field_validator("externalUrl")
    @classmethod
    def validate_external_url_field(cls, value: str | None, info):
        slide_type = info.data.get("slideType")
        if slide_type != "external":
            return value
        if not value or not value.strip():
            raise ValueError("URL externa é obrigatória.")
        validate_external_url(value)
        return value

    @field_validator("nativeScreenKey")
    @classmethod
    def validate_native_key(cls, value: str | None, info):
        if info.data.get("slideType") == "native" and not value:
            raise ValueError("Tela nativa é obrigatória.")
        return value


class UpdateSlideBody(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    durationSec: int | None = Field(default=None)
    sortOrder: int | None = None
    nativeConfig: dict | None = None
    externalUrl: str | None = None
    externalSandbox: str | None = None
    isActive: bool | None = None
    transitionStyle: str | None = Field(default=None, pattern=TRANSITION_STYLE_PATTERN)
    sectionId: UUID | None = None

    @field_validator("durationSec")
    @classmethod
    def validate_duration_sec(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 5 or value > 600:
            raise ValueError("Duração deve estar entre 5 e 600 segundos.")
        return value

    @field_validator("externalUrl")
    @classmethod
    def validate_external_url_field(cls, value: str | None):
        if value:
            validate_external_url(value)
        return value


class ReorderItem(BaseModel):
    id: UUID
    sortOrder: int


class ReorderBody(BaseModel):
    items: list[ReorderItem] = Field(min_length=1)


class FromPresetBody(BaseModel):
    presetKey: str = Field(min_length=1, max_length=120)
    branch: str | None = Field(default=None, max_length=20)


class PreviewDataBlockBody(BaseModel):
    blockId: str = Field(min_length=1, max_length=120)
    nativeConfig: dict


class PresentationMutationBody(BaseModel):
    """Editor ack path — TvPresentationPatchV1 ops committed server-side."""

    ops: list[dict[str, Any]] = Field(min_length=1, max_length=80)


def _actor_id(user: Any) -> str | None:
    return _access.actor_id(user)


def _ok_with_revision(data: Any, *, playlist_id: UUID, message: str, status_code: int = 200):
    revision = _writes.get_revision(playlist_id)
    response = ok(with_revision(data, revision), message=message, status_code=status_code)
    for key, value in revision_response_headers(revision).items():
        response.headers[key] = value
    return response


def _map_write_error(exc: PresentationWriteError):
    return fail(exc.message, exc.status_code, data=exc.details or None)


@router.post("")
def create_slide(request: Request, playlist_id: UUID, body: CreateSlideBody):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    try:
        slide = _writes.add_slide(
            playlist_id,
            {
                "slideType": body.slideType,
                "title": body.title,
                "durationSec": body.durationSec,
                "sortOrder": body.sortOrder,
                "nativeScreenKey": body.nativeScreenKey,
                "nativeConfig": body.nativeConfig,
                "externalUrl": body.externalUrl,
                "externalSandbox": body.externalSandbox,
                "transitionStyle": body.transitionStyle,
                "sectionId": body.sectionId,
            },
            actor_user_id=actor,
            user=user,
            expected_revision=parse_if_match_revision(request),
            reason="slide_created",
        )
    except PresentationWriteError as exc:
        return _map_write_error(exc)
    return _ok_with_revision(
        slide, playlist_id=playlist_id, message="Tela adicionada.", status_code=201
    )


@router.post("/from-preset")
def create_slide_from_preset(request: Request, playlist_id: UUID, body: FromPresetBody):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    try:
        slide = _writes.add_slide_from_preset(
            playlist_id,
            preset_key=body.presetKey,
            branch=body.branch,
            actor_user_id=actor,
            user=user,
            expected_revision=parse_if_match_revision(request),
        )
    except PresentationWriteError as exc:
        return _map_write_error(exc)
    return _ok_with_revision(
        slide, playlist_id=playlist_id, message="Tela importada do catálogo.", status_code=201
    )


@router.post("/reorder")
def reorder_slides(request: Request, playlist_id: UUID, body: ReorderBody):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    try:
        slides = _writes.reorder_slides(
            playlist_id,
            [{"id": str(item.id), "sortOrder": item.sortOrder} for item in body.items],
            actor_user_id=actor,
            expected_revision=parse_if_match_revision(request),
        )
    except PresentationWriteError as exc:
        return _map_write_error(exc)
    return _ok_with_revision(
        {"slides": slides}, playlist_id=playlist_id, message="Ordem atualizada."
    )


@router.patch("/{slide_id}")
def update_slide(request: Request, playlist_id: UUID, slide_id: UUID, body: UpdateSlideBody):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    try:
        slide = _writes.update_slide(
            playlist_id,
            slide_id,
            body.model_dump(exclude_unset=True),
            actor_user_id=actor,
            user=user,
            expected_revision=parse_if_match_revision(request),
        )
    except PresentationWriteError as exc:
        return _map_write_error(exc)
    return _ok_with_revision(slide, playlist_id=playlist_id, message="Tela atualizada.")


@router.post("/{slide_id}/preview-data-block")
def preview_data_block(
    request: Request,
    playlist_id: UUID,
    slide_id: UUID,
    body: PreviewDataBlockBody,
):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    try:
        _writes.get_slide(slide_id, playlist_id=playlist_id)
    except PresentationWriteError as exc:
        return _map_write_error(exc)
    auth = request.headers.get("Authorization")
    try:
        cfg = _writes.prepare_native_config(body.nativeConfig, user=user)
    except ValueError as exc:
        return fail(str(exc), 422)
    blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else []
    target = next(
        (block for block in blocks if isinstance(block, dict) and str(block.get("id")) == body.blockId),
        None,
    )
    if not isinstance(target, dict):
        return fail("Bloco não encontrado.", 404)
    enriched = ComunicadoDataEnrichmentService().enrich_blocks(
        [target],
        cfg=cfg,
        authorization=auth,
        user=user,
    )
    return ok({"block": enriched[0] if enriched else target})


@router.post("/{slide_id}/presentation-mutations")
def apply_presentation_mutations(
    request: Request,
    playlist_id: UUID,
    slide_id: UUID,
    body: PresentationMutationBody,
):
    """Commit typed PresentationMutation ops and persist canonical nativeConfig.

    TV-DASHBOARD-PRESENTATION-001: editor geometry/style/create flush through
    this path so the backend is the sole persistent authority.
    """
    from tv_app.application.services.data.presentation_mutation.patch_service import (
        PresentationPatchError,
    )
    from tv_app.application.services.data.presentation_mutation_commit_service import (
        PresentationMutationCommitService,
    )

    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    auth = request.headers.get("Authorization")
    try:
        result = PresentationMutationCommitService(writes=_writes).commit(
            playlist_id=playlist_id,
            slide_id=slide_id,
            ops=body.ops,
            user=user,
            actor_user_id=actor,
            authorization=auth,
            expected_revision=parse_if_match_revision(request),
        )
    except PresentationPatchError as exc:
        return fail(str(exc), 422, data=getattr(exc, "details", None) or None)
    except PresentationWriteError as exc:
        return _map_write_error(exc)
    slide = result.get("slide")
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="presentation_mutation",
        slide_id=str(slide_id),
    )
    return _ok_with_revision(
        {
            "slide": slide,
            "nativeConfig": result.get("nativeConfig"),
            "appliedOps": result.get("appliedOps") or [],
            "fingerprint": result.get("fingerprint"),
            "sideEffectHints": result.get("sideEffectHints") or [],
            "persisted": True,
            "executionMode": result.get("executionMode"),
        },
        playlist_id=playlist_id,
        message=str(result.get("message") or "Mutação aplicada."),
    )


@router.delete("/{slide_id}")
def delete_slide(request: Request, playlist_id: UUID, slide_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    try:
        _writes.delete_slide(
            playlist_id,
            slide_id,
            actor_user_id=actor,
            expected_revision=parse_if_match_revision(request),
        )
    except PresentationWriteError as exc:
        return _map_write_error(exc)
    return _ok_with_revision(None, playlist_id=playlist_id, message="Tela removida.")


@router.post("/{slide_id}/duplicate")
def duplicate_slide(request: Request, playlist_id: UUID, slide_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    try:
        slide = _repo.duplicate_slide(
            playlist_id,
            slide_id,
            actor_user_id=actor,
            reason="slide_duplicated",
        )
    except SlideNotFoundError:
        return fail("Tela não encontrada.", 404)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="slide_duplicated",
    )
    return ok(slide, message="Tela duplicada.", status_code=201)
