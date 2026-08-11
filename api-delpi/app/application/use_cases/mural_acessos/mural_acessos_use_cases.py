"""Casos de uso — Mural de Acessos."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.services.mural_acessos.mural_acessos_image_storage import (
    MuralAcessosImageStorage,
    MuralAcessosStorageError,
)
from app.application.services.mural_acessos.mural_acessos_qr_service import (
    build_public_menu_path,
    build_public_menu_url,
    render_public_menu_qr_png,
)
from app.domain.services.mural_acessos.exceptions import (
    MuralAcessosNotFoundError,
    MuralAcessosValidationError,
)
from app.domain.services.mural_acessos.link_url import (
    normalize_description,
    normalize_link_url,
    normalize_public_token,
    normalize_subtitle,
    normalize_title,
)
from app.infrastructure.persistence.plugins.repositories.mural_acessos.postgres_mural_acessos_repository import (
    PostgresMuralAcessosRepository,
)


class ActorContext:
    def __init__(self, user_id: str | None, user_name: str | None) -> None:
        self.user_id = user_id
        self.user_name = user_name


def _public_image_path(link_id: str) -> str:
    return f"/apps/api-delpi/public/mural-acessos/links/{link_id}/image"


def _admin_image_path(link_id: str) -> str:
    return f"/apps/api-delpi/mural-acessos/links/{link_id}/image"


def _present_hub(row: dict[str, Any]) -> dict[str, Any]:
    token = str(row["publicToken"])
    hub_id = str(row["id"])
    payload = {
        "id": hub_id,
        "title": row["title"],
        "subtitle": row["subtitle"],
        "publicToken": token,
        "publicPath": build_public_menu_path(token),
        "publicUrl": build_public_menu_url(token),
        "qrUrl": f"/apps/api-delpi/mural-acessos/hubs/{hub_id}/qr.png",
    }
    if "linkCount" in row:
        payload["linkCount"] = int(row["linkCount"] or 0)
    return payload


def _present_admin_link(row: dict[str, Any]) -> dict[str, Any]:
    link_id = row["id"]
    return {
        "id": link_id,
        "hubId": row.get("hubId"),
        "title": row["title"],
        "url": row["url"],
        "description": row["description"],
        "orderIndex": row["orderIndex"],
        "active": row["active"],
        "hasImage": row["hasImage"],
        "imageUrl": _admin_image_path(link_id) if row["hasImage"] else None,
        "createdAt": row["createdAt"],
        "updatedAt": row["updatedAt"],
        "createdByName": row.get("createdByName"),
        "updatedByName": row.get("updatedByName"),
    }


def _present_public_link(row: dict[str, Any]) -> dict[str, Any]:
    link_id = row["id"]
    return {
        "id": link_id,
        "title": row["title"],
        "url": row["url"],
        "description": row["description"],
        "orderIndex": row["orderIndex"],
        "hasImage": row["hasImage"],
        "imageUrl": _public_image_path(link_id) if row["hasImage"] else None,
    }


def _require_hub(
    repository: PostgresMuralAcessosRepository, hub_id: str
) -> dict[str, Any]:
    hub = repository.get_hub(hub_id)
    if not hub:
        raise MuralAcessosNotFoundError("Mural não encontrado.")
    return hub


class ListHubsUseCase:
    def __init__(self, repository: PostgresMuralAcessosRepository) -> None:
        self._repository = repository

    def execute(self) -> list[dict[str, Any]]:
        return [_present_hub(row) for row in self._repository.list_hubs()]


class CreateHubUseCase:
    def __init__(self, repository: PostgresMuralAcessosRepository) -> None:
        self._repository = repository

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = normalize_title(payload.get("title"))
        subtitle = normalize_subtitle(payload.get("subtitle"))
        raw_token = payload.get("publicToken") or title
        token = normalize_public_token(str(raw_token) if raw_token is not None else "")
        created = self._repository.create_hub(
            title=title,
            subtitle=subtitle,
            public_token=token,
        )
        return _present_hub(created)


class GetHubUseCase:
    def __init__(self, repository: PostgresMuralAcessosRepository) -> None:
        self._repository = repository

    def execute(self, hub_id: str) -> dict[str, Any]:
        return _present_hub(_require_hub(self._repository, hub_id))


class UpdateHubUseCase:
    def __init__(self, repository: PostgresMuralAcessosRepository) -> None:
        self._repository = repository

    def execute(self, hub_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        _require_hub(self._repository, hub_id)
        updated = self._repository.update_hub(
            hub_id=hub_id,
            title=normalize_title(payload.get("title")),
            subtitle=normalize_subtitle(payload.get("subtitle")),
            public_token=normalize_public_token(payload.get("publicToken")),
        )
        if not updated:
            raise MuralAcessosNotFoundError("Mural não encontrado.")
        return _present_hub(updated)


class DeleteHubUseCase:
    def __init__(
        self,
        repository: PostgresMuralAcessosRepository,
        storage: MuralAcessosImageStorage,
    ) -> None:
        self._repository = repository
        self._storage = storage

    def execute(self, hub_id: str) -> dict[str, Any]:
        _require_hub(self._repository, hub_id)
        links = self._repository.list_links(hub_id=hub_id)
        deleted = self._repository.delete_hub(hub_id=hub_id)
        if not deleted:
            raise MuralAcessosNotFoundError("Mural não encontrado.")
        for row in links:
            self._storage.delete_file(
                link_id=row["id"],
                stored_name=row.get("imageStoredName"),
            )
        return {"id": hub_id, "deleted": True}


class RenderHubQrUseCase:
    def __init__(self, repository: PostgresMuralAcessosRepository) -> None:
        self._repository = repository

    def execute(self, hub_id: str) -> bytes:
        hub = _require_hub(self._repository, hub_id)
        return render_public_menu_qr_png(str(hub["publicToken"]))


class ListLinksUseCase:
    def __init__(self, repository: PostgresMuralAcessosRepository) -> None:
        self._repository = repository

    def execute(self, hub_id: str) -> list[dict[str, Any]]:
        _require_hub(self._repository, hub_id)
        return [
            _present_admin_link(row)
            for row in self._repository.list_links(hub_id=hub_id)
        ]


class CreateLinkUseCase:
    def __init__(self, repository: PostgresMuralAcessosRepository) -> None:
        self._repository = repository

    def execute(
        self, hub_id: str, payload: dict[str, Any], actor: ActorContext
    ) -> dict[str, Any]:
        _require_hub(self._repository, hub_id)
        created = self._repository.create_link(
            hub_id=hub_id,
            title=normalize_title(payload.get("title")),
            url=normalize_link_url(payload.get("url")),
            description=normalize_description(payload.get("description")),
            active=bool(payload.get("active", True)),
            actor_id=actor.user_id,
            actor_name=actor.user_name,
        )
        return _present_admin_link(created)


class UpdateLinkUseCase:
    def __init__(self, repository: PostgresMuralAcessosRepository) -> None:
        self._repository = repository

    def execute(
        self, link_id: str, payload: dict[str, Any], actor: ActorContext
    ) -> dict[str, Any]:
        updated = self._repository.update_link(
            link_id=link_id,
            title=normalize_title(payload.get("title")),
            url=normalize_link_url(payload.get("url")),
            description=normalize_description(payload.get("description")),
            active=bool(payload.get("active", True)),
            actor_id=actor.user_id,
            actor_name=actor.user_name,
        )
        if not updated:
            raise MuralAcessosNotFoundError("Acesso não encontrado.")
        return _present_admin_link(updated)


class DeleteLinkUseCase:
    def __init__(
        self,
        repository: PostgresMuralAcessosRepository,
        storage: MuralAcessosImageStorage,
    ) -> None:
        self._repository = repository
        self._storage = storage

    def execute(self, link_id: str) -> dict[str, Any]:
        deleted = self._repository.delete_link(link_id=link_id)
        if not deleted:
            raise MuralAcessosNotFoundError("Acesso não encontrado.")
        self._storage.delete_file(
            link_id=link_id,
            stored_name=deleted.get("imageStoredName"),
        )
        return {"id": link_id, "deleted": True}


class ReorderLinksUseCase:
    def __init__(self, repository: PostgresMuralAcessosRepository) -> None:
        self._repository = repository

    def execute(self, hub_id: str, ordered_ids: list[str]) -> list[dict[str, Any]]:
        _require_hub(self._repository, hub_id)
        existing = {
            row["id"] for row in self._repository.list_links(hub_id=hub_id)
        }
        unique_ids: list[str] = []
        seen: set[str] = set()
        for raw in ordered_ids:
            try:
                link_id = str(UUID(str(raw)))
            except ValueError as exc:
                raise MuralAcessosValidationError("Identificador inválido.") from exc
            if link_id in seen:
                continue
            if link_id not in existing:
                raise MuralAcessosValidationError("Acesso inexistente na ordenação.")
            seen.add(link_id)
            unique_ids.append(link_id)
        if set(unique_ids) != existing:
            raise MuralAcessosValidationError(
                "A ordenação deve incluir todos os acessos cadastrados."
            )
        return [
            _present_admin_link(row)
            for row in self._repository.reorder_links(
                hub_id=hub_id, ordered_ids=unique_ids
            )
        ]


class UploadLinkImageUseCase:
    def __init__(
        self,
        repository: PostgresMuralAcessosRepository,
        storage: MuralAcessosImageStorage,
    ) -> None:
        self._repository = repository
        self._storage = storage

    def execute(
        self,
        *,
        link_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        actor: ActorContext,
    ) -> dict[str, Any]:
        current = self._repository.get_link(link_id)
        if not current:
            raise MuralAcessosNotFoundError("Acesso não encontrado.")
        try:
            saved = self._storage.save(
                link_id=link_id,
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except MuralAcessosStorageError as exc:
            raise MuralAcessosValidationError(str(exc)) from exc

        previous_name = current.get("imageStoredName")
        updated = self._repository.set_link_image(
            link_id=link_id,
            stored_name=str(saved["stored_name"]),
            mime_type=str(saved["mime_type"]),
            size_bytes=int(saved["size_bytes"]),
            actor_id=actor.user_id,
            actor_name=actor.user_name,
        )
        if previous_name and previous_name != saved["stored_name"]:
            self._storage.delete_file(link_id=link_id, stored_name=str(previous_name))
        if not updated:
            raise MuralAcessosNotFoundError("Acesso não encontrado.")
        return _present_admin_link(updated)


class DeleteLinkImageUseCase:
    def __init__(
        self,
        repository: PostgresMuralAcessosRepository,
        storage: MuralAcessosImageStorage,
    ) -> None:
        self._repository = repository
        self._storage = storage

    def execute(self, link_id: str, actor: ActorContext) -> dict[str, Any]:
        current = self._repository.get_link(link_id)
        if not current:
            raise MuralAcessosNotFoundError("Acesso não encontrado.")
        self._storage.delete_file(
            link_id=link_id,
            stored_name=current.get("imageStoredName"),
        )
        updated = self._repository.clear_link_image(
            link_id=link_id,
            actor_id=actor.user_id,
            actor_name=actor.user_name,
        )
        if not updated:
            raise MuralAcessosNotFoundError("Acesso não encontrado.")
        return _present_admin_link(updated)


class ResolveLinkImageUseCase:
    def __init__(
        self,
        repository: PostgresMuralAcessosRepository,
        storage: MuralAcessosImageStorage,
    ) -> None:
        self._repository = repository
        self._storage = storage

    def execute(self, link_id: str, *, public_only: bool = False) -> tuple[Any, str]:
        row = self._repository.get_link(link_id)
        if not row or not row.get("imageStoredName"):
            raise MuralAcessosNotFoundError("Imagem não encontrada.")
        if public_only and not row.get("active"):
            raise MuralAcessosNotFoundError("Imagem não encontrada.")
        try:
            path = self._storage.resolve_file(
                link_id=link_id,
                stored_name=str(row["imageStoredName"]),
            )
        except MuralAcessosStorageError as exc:
            raise MuralAcessosNotFoundError(str(exc)) from exc
        mime = str(row.get("imageMimeType") or "application/octet-stream")
        return path, mime


class ListPublicMenuUseCase:
    def __init__(self, repository: PostgresMuralAcessosRepository) -> None:
        self._repository = repository

    def execute(self, public_token: str) -> dict[str, Any]:
        try:
            token = normalize_public_token(public_token)
        except MuralAcessosValidationError as exc:
            raise MuralAcessosNotFoundError("Mural não encontrado.") from exc
        hub = self._repository.get_hub_by_token(token)
        if not hub:
            raise MuralAcessosNotFoundError("Mural não encontrado.")
        items = [
            _present_public_link(row)
            for row in self._repository.list_links(hub_id=hub["id"], active_only=True)
        ]
        return {
            "id": hub["id"],
            "title": hub["title"],
            "subtitle": hub["subtitle"],
            "publicToken": hub["publicToken"],
            "items": items,
        }
