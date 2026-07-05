from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from tv_app.application.services.branch_policy_service import validate_native_branch
from tv_app.application.services.slide_preset_service import (
    SlidePresetNotFoundError,
    resolve_preset_slide,
)

from tv_app.application.services.external_url_validator_service import validate_external_url
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_READ, TV_WRITE, assert_permission
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    PlaylistNotFoundError,
    PlaylistRepository,
    SlideNotFoundError,
)
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/playlists/{playlist_id}/slides", tags=["Slides"])
_repo = PlaylistRepository()


class CreateSlideBody(BaseModel):
    slideType: str = Field(pattern="^(native|external)$")
    title: str = Field(min_length=1, max_length=200)
    durationSec: int | None = Field(default=None, ge=5, le=600)
    sortOrder: int | None = None
    nativeScreenKey: str | None = None
    nativeConfig: dict | None = None
    externalUrl: str | None = None
    externalSandbox: str | None = None

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
    durationSec: int | None = Field(default=None, ge=5, le=600)
    sortOrder: int | None = None
    nativeConfig: dict | None = None
    externalUrl: str | None = None
    externalSandbox: str | None = None
    isActive: bool | None = None

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
    items: list[ReorderItem]


class FromPresetBody(BaseModel):
    presetKey: str = Field(min_length=1, max_length=120)
    branch: str | None = Field(default=None, max_length=20)


def _ensure_playlist(playlist_id: UUID) -> bool:
    return _repo.get_by_id(playlist_id) is not None


@router.post("")
def create_slide(request: Request, playlist_id: UUID, body: CreateSlideBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    if not _ensure_playlist(playlist_id):
        return fail("Programação não encontrada.", 404)
    try:
        if body.slideType == "native" and body.nativeConfig:
            validate_native_branch(body.nativeConfig, user=user)
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
            "nativeConfig": body.nativeConfig,
            "externalUrl": body.externalUrl,
            "externalSandbox": body.externalSandbox,
        },
    )
    return ok(slide, message="Tela adicionada.", status_code=201)


@router.post("/from-preset")
def create_slide_from_preset(request: Request, playlist_id: UUID, body: FromPresetBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    if not _ensure_playlist(playlist_id):
        return fail("Programação não encontrada.", 404)
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
    slide = _repo.add_slide(playlist_id, preset_payload)
    return ok(slide, message="Tela importada do catálogo.", status_code=201)


@router.post("/reorder")
def reorder_slides(request: Request, playlist_id: UUID, body: ReorderBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    if not _ensure_playlist(playlist_id):
        return fail("Programação não encontrada.", 404)
    slides = _repo.reorder_slides(
        playlist_id,
        [{"id": str(item.id), "sortOrder": item.sortOrder} for item in body.items],
    )
    return ok({"slides": slides}, message="Ordem atualizada.")


@router.patch("/{slide_id}")
def update_slide(request: Request, playlist_id: UUID, slide_id: UUID, body: UpdateSlideBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    if not _ensure_playlist(playlist_id):
        return fail("Programação não encontrada.", 404)
    try:
        if body.nativeConfig is not None:
            validate_native_branch(body.nativeConfig, user=user)
    except ValueError as exc:
        return fail(str(exc), 422)
    try:
        slide = _repo.update_slide(
            slide_id,
            body.model_dump(exclude_unset=True),
        )
    except SlideNotFoundError:
        return fail("Tela não encontrada.", 404)
    return ok(slide, message="Tela atualizada.")


@router.delete("/{slide_id}")
def delete_slide(request: Request, playlist_id: UUID, slide_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    if not _ensure_playlist(playlist_id):
        return fail("Programação não encontrada.", 404)
    try:
        _repo.delete_slide(slide_id)
    except SlideNotFoundError:
        return fail("Tela não encontrada.", 404)
    return ok(message="Tela removida.")


@router.post("/{slide_id}/duplicate")
def duplicate_slide(request: Request, playlist_id: UUID, slide_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    if not _ensure_playlist(playlist_id):
        return fail("Programação não encontrada.", 404)
    try:
        existing = _repo.get_slide(slide_id)
    except SlideNotFoundError:
        return fail("Tela não encontrada.", 404)
    if existing["playlistId"] != str(playlist_id):
        return fail("Tela não pertence a esta programação.", 404)
    try:
        slide = _repo.duplicate_slide(slide_id)
    except SlideNotFoundError:
        return fail("Tela não encontrada.", 404)
    return ok(slide, message="Tela duplicada.", status_code=201)
