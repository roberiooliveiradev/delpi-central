from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from tv_app.application.services.comunicado_config_validation_service import (
    sanitize_and_hydrate_comunicado_config,
    validate_comunicado_native_config,
)
from tv_app.application.services.comunicado_data_enrichment_service import ComunicadoDataEnrichmentService
from tv_app.application.services.branch_policy_service import validate_native_branch
from tv_app.application.services.playlist_access_service import PlaylistAccessService
from tv_app.application.services.presentation_change_notifier import notify_presentation_changed
from tv_app.application.services.presentation_transition_catalog import TRANSITION_STYLE_PATTERN
from tv_app.application.services.slide_preset_service import (
    SlidePresetNotFoundError,
    resolve_preset_slide,
)

from tv_app.application.services.external_url_validator_service import validate_external_url
from tv_app.core.responses import fail, ok
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistNotFoundError,
    PlaylistRepository,
    SlideNotFoundError,
)
from tv_app.interface.http.playlist_access_http import is_access_error, require_playlist_access
from tv_app.interface.http.playlist_revision_http import (
    assert_playlist_revision_or_conflict,
    parse_if_match_revision,
    revision_response_headers,
    with_revision,
)

router = APIRouter(prefix="/playlists/{playlist_id}/slides", tags=["Slides"])
_repo = PlaylistRepository()
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


def _prepare_native_config(
    native_config: dict | None,
    *,
    user: Any,
) -> dict | None:
    if native_config is None:
        return None
    cleaned = sanitize_and_hydrate_comunicado_config(native_config)
    validate_comunicado_native_config(cleaned, user=user)
    return cleaned


def _actor_id(user: Any) -> str | None:
    return _access.actor_id(user)


def _ok_with_revision(data: Any, *, playlist_id: UUID, message: str, status_code: int = 200):
    revision = _repo.get_revision(playlist_id)
    response = ok(with_revision(data, revision), message=message, status_code=status_code)
    for key, value in revision_response_headers(revision).items():
        response.headers[key] = value
    return response


@router.post("")
def create_slide(request: Request, playlist_id: UUID, body: CreateSlideBody):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    conflict = assert_playlist_revision_or_conflict(
        _repo, playlist_id, expected=parse_if_match_revision(request)
    )
    if not isinstance(conflict, int):
        return conflict
    native_config = body.nativeConfig
    try:
        if body.slideType == "native" and native_config is not None:
            native_config = _prepare_native_config(native_config, user=user)
    except ValueError as exc:
        return fail(str(exc), 422)
    slide = _repo.add_slide(
        playlist_id,
        {
            "slideType": body.slideType,
            "title": body.title,
            "durationSec": body.durationSec,
            "sortOrder": body.sortOrder,
            "nativeScreenKey": body.nativeScreenKey,
            "nativeConfig": native_config,
            "externalUrl": body.externalUrl,
            "externalSandbox": body.externalSandbox,
            "transitionStyle": body.transitionStyle,
            "sectionId": body.sectionId,
        },
        actor_user_id=actor,
        reason="slide_created",
    )
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="slide_created",
        slide_id=str(slide.get("id") or ""),
    )
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
    conflict = assert_playlist_revision_or_conflict(
        _repo, playlist_id, expected=parse_if_match_revision(request)
    )
    if not isinstance(conflict, int):
        return conflict
    try:
        preset_payload = resolve_preset_slide(body.presetKey)
    except SlidePresetNotFoundError:
        return fail("Preset de tela não encontrado.", 404)
    except ValueError as exc:
        return fail(str(exc), 422)
    if body.branch and body.branch.strip() and preset_payload.get("slideType") == "native":
        native_config = dict(preset_payload.get("nativeConfig") or {})
        native_config["branch"] = body.branch.strip()
        preset_payload["nativeConfig"] = native_config
    if preset_payload.get("slideType") == "native":
        try:
            validate_native_branch(preset_payload.get("nativeConfig"), user=user)
        except ValueError as exc:
            return fail(str(exc), 422)
    slide = _repo.add_slide(
        playlist_id,
        preset_payload,
        actor_user_id=actor,
        reason="slide_imported",
    )
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="slide_imported",
        slide_id=str(slide.get("id") or ""),
    )
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
    conflict = assert_playlist_revision_or_conflict(
        _repo, playlist_id, expected=parse_if_match_revision(request)
    )
    if not isinstance(conflict, int):
        return conflict
    slides = _repo.reorder_slides(
        playlist_id,
        [{"id": str(item.id), "sortOrder": item.sortOrder} for item in body.items],
        actor_user_id=actor,
        reason="slides_reordered",
    )
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="slides_reordered",
    )
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
    conflict = assert_playlist_revision_or_conflict(
        _repo, playlist_id, expected=parse_if_match_revision(request)
    )
    if not isinstance(conflict, int):
        return conflict
    payload = body.model_dump(exclude_unset=True)
    try:
        if payload.get("nativeConfig") is not None:
            payload["nativeConfig"] = _prepare_native_config(payload["nativeConfig"], user=user)
    except ValueError as exc:
        return fail(str(exc), 422)
    try:
        slide = _repo.update_slide(
            playlist_id,
            slide_id,
            payload,
            actor_user_id=actor,
            reason="slide_updated",
        )
    except SlideNotFoundError:
        return fail("Tela não encontrada.", 404)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="slide_updated",
        slide_id=str(slide_id),
    )
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
        _repo.get_slide(slide_id, playlist_id=playlist_id)
    except SlideNotFoundError:
        return fail("Tela não encontrada.", 404)
    auth = request.headers.get("Authorization")
    try:
        cfg = _prepare_native_config(body.nativeConfig, user=user)
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


@router.delete("/{slide_id}")
def delete_slide(request: Request, playlist_id: UUID, slide_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    actor = _actor_id(user)
    if not actor:
        return fail("Usuário não identificado.", 401)
    conflict = assert_playlist_revision_or_conflict(
        _repo, playlist_id, expected=parse_if_match_revision(request)
    )
    if not isinstance(conflict, int):
        return conflict
    try:
        _repo.delete_slide(
            playlist_id,
            slide_id,
            actor_user_id=actor,
            reason="slide_deleted",
        )
    except SlideNotFoundError:
        return fail("Tela não encontrada.", 404)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="slide_deleted",
        slide_id=str(slide_id),
    )
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
