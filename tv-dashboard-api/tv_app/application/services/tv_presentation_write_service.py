"""Canonical presentation write boundary shared by UI CRUD and GPT Actions.

Does not know FastAPI Request, OpenAI, GPT Builder, or HTTP paths.
AuthZ remains at the caller; this service owns sanitize/validate + persist + notify.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.application.errors.playlist_persistence import (
    MainSectionProtectedError,
    PlaylistNotFoundError,
    SectionNotFoundError,
    SlideNotFoundError,
)
from tv_app.application.ports import PresentationRepositoryPort
from tv_app.application.services.branch_policy_service import validate_native_branch
from tv_app.application.services.comunicado_config_validation_service import (
    sanitize_and_hydrate_comunicado_config,
    validate_comunicado_native_config,
)
from tv_app.application.services.presentation_change_notifier import notify_presentation_changed
from tv_app.application.services.slide_preset_service import (
    SlidePresetNotFoundError,
    resolve_preset_slide,
)


class PresentationWriteError(Exception):
    """Domain/validation failure for presentation writes."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "INVALID_CHANGE",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class RevisionConflictError(PresentationWriteError):
    def __init__(
        self,
        *,
        expected_revision: int,
        current_revision: int,
    ) -> None:
        super().__init__(
            "A programação foi alterada por outro editor. Recarregue e tente de novo.",
            status_code=409,
            code="REVISION_CONFLICT",
            details={
                "expectedRevision": int(expected_revision),
                "currentRevision": int(current_revision),
            },
        )
        self.expected_revision = int(expected_revision)
        self.current_revision = int(current_revision)


class TvPresentationWriteService:
    """Application owner for playlist/slide/section persistence (UI + GPT)."""

    def __init__(self, repo: PresentationRepositoryPort) -> None:
        self._repo = repo

    @property
    def repo(self) -> PresentationRepositoryPort:
        return self._repo

    def get_revision(self, playlist_id: UUID) -> int:
        return self._repo.get_revision(playlist_id)

    def assert_expected_revision(
        self,
        playlist_id: UUID,
        expected_revision: int | None,
    ) -> int:
        current = self._repo.get_revision(playlist_id)
        if expected_revision is None:
            return current
        if current != int(expected_revision):
            raise RevisionConflictError(
                expected_revision=int(expected_revision),
                current_revision=current,
            )
        return current

    def prepare_native_config(
        self,
        native_config: dict | None,
        *,
        user: Any,
    ) -> dict | None:
        if native_config is None:
            return None
        cleaned = sanitize_and_hydrate_comunicado_config(native_config)
        validate_comunicado_native_config(cleaned, user=user)
        return cleaned

    def create_playlist(
        self,
        *,
        name: str,
        description: str | None,
        actor_user_id: str,
    ) -> dict[str, Any]:
        from tv_app.application.services.presentation_change_notifier import (
            notify_playlist_library_changed,
        )

        playlist = self._repo.create(
            name=name,
            description=description,
            created_by=actor_user_id,
        )
        pid = str(playlist.get("id") or "").strip()
        if actor_user_id and pid:
            notify_playlist_library_changed(
                user_ids=[actor_user_id],
                reason="created",
                playlist_id=pid,
            )
        return playlist

    def add_slide(
        self,
        playlist_id: UUID,
        payload: dict[str, Any],
        *,
        actor_user_id: str,
        user: Any,
        expected_revision: int | None = None,
        reason: str = "slide_created",
        notify: bool = True,
    ) -> dict[str, Any]:
        self.assert_expected_revision(playlist_id, expected_revision)
        body = dict(payload)
        if body.get("slideType") == "native" and body.get("nativeConfig") is not None:
            try:
                body["nativeConfig"] = self.prepare_native_config(
                    body["nativeConfig"], user=user
                )
            except ValueError as exc:
                raise PresentationWriteError(str(exc), status_code=422) from exc
        slide = self._repo.add_slide(
            playlist_id,
            body,
            actor_user_id=actor_user_id,
            reason=reason,
        )
        if notify:
            notify_presentation_changed(
                playlist_id=str(playlist_id),
                reason=reason,
                slide_id=str(slide.get("id") or ""),
            )
        return slide

    def add_slide_from_preset(
        self,
        playlist_id: UUID,
        *,
        preset_key: str,
        branch: str | None,
        actor_user_id: str,
        user: Any,
        expected_revision: int | None = None,
        notify: bool = True,
    ) -> dict[str, Any]:
        self.assert_expected_revision(playlist_id, expected_revision)
        try:
            preset_payload = resolve_preset_slide(preset_key)
        except SlidePresetNotFoundError as exc:
            raise PresentationWriteError(
                "Preset de tela não encontrado.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            ) from exc
        except ValueError as exc:
            raise PresentationWriteError(str(exc), status_code=422) from exc
        if branch and str(branch).strip() and preset_payload.get("slideType") == "native":
            native_config = dict(preset_payload.get("nativeConfig") or {})
            native_config["branch"] = str(branch).strip()
            preset_payload["nativeConfig"] = native_config
        if preset_payload.get("slideType") == "native":
            try:
                validate_native_branch(preset_payload.get("nativeConfig"), user=user)
            except ValueError as exc:
                raise PresentationWriteError(str(exc), status_code=422) from exc
        slide = self._repo.add_slide(
            playlist_id,
            preset_payload,
            actor_user_id=actor_user_id,
            reason="slide_imported",
        )
        if notify:
            notify_presentation_changed(
                playlist_id=str(playlist_id),
                reason="slide_imported",
                slide_id=str(slide.get("id") or ""),
            )
        return slide

    def update_slide(
        self,
        playlist_id: UUID,
        slide_id: UUID,
        payload: dict[str, Any],
        *,
        actor_user_id: str,
        user: Any,
        expected_revision: int | None = None,
        reason: str = "slide_updated",
        notify: bool = True,
    ) -> dict[str, Any]:
        self.assert_expected_revision(playlist_id, expected_revision)
        body = dict(payload)
        if body.get("nativeConfig") is not None:
            try:
                body["nativeConfig"] = self.prepare_native_config(
                    body["nativeConfig"], user=user
                )
            except ValueError as exc:
                raise PresentationWriteError(str(exc), status_code=422) from exc
        try:
            slide = self._repo.update_slide(
                playlist_id,
                slide_id,
                body,
                actor_user_id=actor_user_id,
                reason=reason,
            )
        except SlideNotFoundError as exc:
            raise PresentationWriteError(
                "Tela não encontrada.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            ) from exc
        if notify:
            notify_presentation_changed(
                playlist_id=str(playlist_id),
                reason=reason,
                slide_id=str(slide_id),
            )
        return slide

    def delete_slide(
        self,
        playlist_id: UUID,
        slide_id: UUID,
        *,
        actor_user_id: str,
        expected_revision: int | None = None,
        notify: bool = True,
    ) -> None:
        self.assert_expected_revision(playlist_id, expected_revision)
        try:
            self._repo.delete_slide(
                playlist_id,
                slide_id,
                actor_user_id=actor_user_id,
                reason="slide_deleted",
            )
        except SlideNotFoundError as exc:
            raise PresentationWriteError(
                "Tela não encontrada.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            ) from exc
        if notify:
            notify_presentation_changed(
                playlist_id=str(playlist_id),
                reason="slide_deleted",
                slide_id=str(slide_id),
            )

    def reorder_slides(
        self,
        playlist_id: UUID,
        items: list[dict[str, Any]],
        *,
        actor_user_id: str,
        expected_revision: int | None = None,
        notify: bool = True,
    ) -> list[dict[str, Any]]:
        self.assert_expected_revision(playlist_id, expected_revision)
        slides = self._repo.reorder_slides(
            playlist_id,
            items,
            actor_user_id=actor_user_id,
            reason="slides_reordered",
        )
        if notify:
            notify_presentation_changed(
                playlist_id=str(playlist_id),
                reason="slides_reordered",
            )
        return slides

    def add_section(
        self,
        playlist_id: UUID,
        payload: dict[str, Any],
        *,
        actor_user_id: str,
        expected_revision: int | None = None,
        notify: bool = True,
    ) -> dict[str, Any]:
        self.assert_expected_revision(playlist_id, expected_revision)
        try:
            section = self._repo.add_section(
                playlist_id,
                payload,
                actor_user_id=actor_user_id,
            )
        except PlaylistNotFoundError as exc:
            raise PresentationWriteError(
                "Programação não encontrada.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            ) from exc
        if notify:
            notify_presentation_changed(
                playlist_id=str(playlist_id),
                reason="section_created",
            )
        return section

    def update_section(
        self,
        playlist_id: UUID,
        section_id: UUID,
        payload: dict[str, Any],
        *,
        actor_user_id: str,
        expected_revision: int | None = None,
        notify: bool = True,
    ) -> dict[str, Any]:
        self.assert_expected_revision(playlist_id, expected_revision)
        try:
            section = self._repo.update_section(
                playlist_id,
                section_id,
                payload,
                actor_user_id=actor_user_id,
            )
        except PlaylistNotFoundError as exc:
            raise PresentationWriteError(
                "Programação não encontrada.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            ) from exc
        except SectionNotFoundError as exc:
            raise PresentationWriteError(
                "Seção não encontrada.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            ) from exc
        if notify:
            notify_presentation_changed(
                playlist_id=str(playlist_id),
                reason="section_updated",
            )
        return section

    def delete_section(
        self,
        playlist_id: UUID,
        section_id: UUID,
        *,
        actor_user_id: str,
        delete_slides: bool = False,
        expected_revision: int | None = None,
        notify: bool = True,
    ) -> None:
        self.assert_expected_revision(playlist_id, expected_revision)
        try:
            self._repo.delete_section(
                playlist_id,
                section_id,
                actor_user_id=actor_user_id,
                delete_slides=delete_slides,
            )
        except PlaylistNotFoundError as exc:
            raise PresentationWriteError(
                "Programação não encontrada.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            ) from exc
        except SectionNotFoundError as exc:
            raise PresentationWriteError(
                "Seção não encontrada.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            ) from exc
        except MainSectionProtectedError as exc:
            raise PresentationWriteError(
                "A seção principal não pode ser excluída.",
                status_code=409,
                code="INVALID_CHANGE",
            ) from exc
        if notify:
            notify_presentation_changed(
                playlist_id=str(playlist_id),
                reason="section_deleted",
            )

    def reorder_sections(
        self,
        playlist_id: UUID,
        items: list[dict[str, Any]],
        *,
        actor_user_id: str,
        expected_revision: int | None = None,
        notify: bool = True,
    ) -> list[dict[str, Any]]:
        self.assert_expected_revision(playlist_id, expected_revision)
        try:
            sections = self._repo.reorder_sections(
                playlist_id,
                items,
                actor_user_id=actor_user_id,
            )
        except PlaylistNotFoundError as exc:
            raise PresentationWriteError(
                "Programação não encontrada.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            ) from exc
        if notify:
            notify_presentation_changed(
                playlist_id=str(playlist_id),
                reason="sections_reordered",
            )
        return sections

    def get_slide(self, slide_id: UUID, *, playlist_id: UUID) -> dict[str, Any]:
        try:
            return self._repo.get_slide(slide_id, playlist_id=playlist_id)
        except SlideNotFoundError as exc:
            raise PresentationWriteError(
                "Tela não encontrada.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            ) from exc

    def get_playlist(self, playlist_id: UUID) -> dict[str, Any]:
        row = self._repo.get_by_id(playlist_id)
        if not row:
            raise PresentationWriteError(
                "Programação não encontrada.",
                status_code=404,
                code="RESOURCE_NOT_FOUND",
            )
        return row

    def list_slides(self, playlist_id: UUID) -> list[dict[str, Any]]:
        return self._repo.list_slides(playlist_id)

    def list_sections(self, playlist_id: UUID) -> list[dict[str, Any]]:
        return self._repo.list_sections(playlist_id)
