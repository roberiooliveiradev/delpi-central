from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from tv_app.application.services.playlist_access_service import PlaylistAccessService
from tv_app.application.services.presentation_change_notifier import notify_presentation_changed
from tv_app.core.responses import fail, ok
from tv_app.infrastructure.persistence.repositories.playlist_repository import (
    MainSectionProtectedError,
    PlaylistNotFoundError,
    PlaylistRepository,
    SectionNotFoundError,
)
from tv_app.interface.http.playlist_access_http import is_access_error, require_playlist_access
from tv_app.interface.http.playlist_revision_http import (
    assert_playlist_revision_or_conflict,
    parse_if_match_revision,
    revision_response_headers,
    with_revision,
)

router = APIRouter(prefix="/playlists/{playlist_id}/sections", tags=["Sections"])
_repo = PlaylistRepository()
_access = PlaylistAccessService()


class CreateSectionBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sortOrder: int | None = None
    isCollapsed: bool | None = None
    isActive: bool | None = None
    isMain: bool | None = None
    defaultDurationSec: int | None = Field(default=None, ge=5, le=600)
    transitionStyle: str | None = Field(default=None, pattern="^(fade|slide|none)$")
    masterConfig: dict[str, Any] | None = None


class UpdateSectionBody(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sortOrder: int | None = None
    isCollapsed: bool | None = None
    isActive: bool | None = None
    defaultDurationSec: int | None = Field(default=None, ge=5, le=600)
    transitionStyle: str | None = Field(default=None, pattern="^(fade|slide|none)$")
    masterConfig: dict[str, Any] | None = None


class ReorderItem(BaseModel):
    id: UUID
    sortOrder: int


class ReorderBody(BaseModel):
    items: list[ReorderItem] = Field(min_length=1)


def _actor_id(user: Any) -> str | None:
    return _access.actor_id(user)


def _ok_with_revision(data: Any, *, playlist_id: UUID, message: str = "OK", status_code: int = 200):
    revision = _repo.get_revision(playlist_id)
    response = ok(with_revision(data, revision), message=message, status_code=status_code)
    for key, value in revision_response_headers(revision).items():
        response.headers[key] = value
    return response


def _guard_revision(request: Request, playlist_id: UUID):
    conflict = assert_playlist_revision_or_conflict(
        _repo, playlist_id, expected=parse_if_match_revision(request)
    )
    if not isinstance(conflict, int):
        return conflict
    return None


@router.get("")
def list_sections(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="read")
    if is_access_error(guarded):
        return guarded
    try:
        items = _repo.list_sections(playlist_id)
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", status_code=404)
    return ok({"items": items})


@router.post("/ensure-main")
def ensure_main_section(request: Request, playlist_id: UUID):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    blocked = _guard_revision(request, playlist_id)
    if blocked is not None:
        return blocked
    try:
        section = _repo.ensure_main_section(
            playlist_id,
            actor_user_id=_actor_id(user) or "unknown",
        )
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", status_code=404)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="section_main_ensured",
    )
    return _ok_with_revision(section, playlist_id=playlist_id)


@router.post("")
def create_section(request: Request, playlist_id: UUID, body: CreateSectionBody):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    blocked = _guard_revision(request, playlist_id)
    if blocked is not None:
        return blocked
    payload = body.model_dump(exclude_none=True)
    try:
        section = _repo.add_section(
            playlist_id,
            payload,
            actor_user_id=_actor_id(user) or "unknown",
        )
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", status_code=404)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="section_created",
    )
    return _ok_with_revision(section, playlist_id=playlist_id, status_code=201)


@router.patch("/{section_id}")
def update_section(
    request: Request,
    playlist_id: UUID,
    section_id: UUID,
    body: UpdateSectionBody,
):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    blocked = _guard_revision(request, playlist_id)
    if blocked is not None:
        return blocked
    payload = body.model_dump(exclude_unset=True)
    try:
        section = _repo.update_section(
            playlist_id,
            section_id,
            payload,
            actor_user_id=_actor_id(user) or "unknown",
        )
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", status_code=404)
    except SectionNotFoundError:
        return fail("Seção não encontrada.", status_code=404)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="section_updated",
    )
    return _ok_with_revision(section, playlist_id=playlist_id)


@router.delete("/{section_id}")
def delete_section(
    request: Request,
    playlist_id: UUID,
    section_id: UUID,
    deleteSlides: bool = Query(default=False),
):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    blocked = _guard_revision(request, playlist_id)
    if blocked is not None:
        return blocked
    try:
        _repo.delete_section(
            playlist_id,
            section_id,
            actor_user_id=_actor_id(user) or "unknown",
            delete_slides=deleteSlides,
        )
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", status_code=404)
    except SectionNotFoundError:
        return fail("Seção não encontrada.", status_code=404)
    except MainSectionProtectedError:
        return fail("A seção principal não pode ser excluída.", status_code=409)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="section_deleted",
    )
    return _ok_with_revision({"deleted": True}, playlist_id=playlist_id)


@router.post("/reorder")
def reorder_sections(request: Request, playlist_id: UUID, body: ReorderBody):
    guarded = require_playlist_access(request, playlist_id, need="edit")
    if is_access_error(guarded):
        return guarded
    user, _ = guarded
    blocked = _guard_revision(request, playlist_id)
    if blocked is not None:
        return blocked
    items = [{"id": str(item.id), "sortOrder": item.sortOrder} for item in body.items]
    try:
        sections = _repo.reorder_sections(
            playlist_id,
            items,
            actor_user_id=_actor_id(user) or "unknown",
        )
    except PlaylistNotFoundError:
        return fail("Programação não encontrada.", status_code=404)
    notify_presentation_changed(
        playlist_id=str(playlist_id),
        reason="sections_reordered",
    )
    return _ok_with_revision({"items": sections}, playlist_id=playlist_id)
