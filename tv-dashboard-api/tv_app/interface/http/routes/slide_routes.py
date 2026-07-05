from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator, model_validator

from tv_app.application.services.branch_policy_service import validate_native_branch

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

    @model_validator(mode="after")
    def validate_branch_policy(self):
        if self.slideType == "native" and self.nativeConfig:
            validate_native_branch(self.nativeConfig)
        return self


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

    @model_validator(mode="after")
    def validate_branch_policy(self):
        if self.nativeConfig:
            validate_native_branch(self.nativeConfig)
        return self


class ReorderItem(BaseModel):
    id: UUID
    sortOrder: int


class ReorderBody(BaseModel):
    items: list[ReorderItem]


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
