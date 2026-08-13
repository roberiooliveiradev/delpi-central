from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from commercial_app.application.services.user_profile_storage import (
    UserProfileStorage,
    UserProfileStorageError,
)
from commercial_app.domain.ports.portal_access_port import PortalAccessPort
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.ports.user_profile_repository_port import UserProfileRepositoryPort
from commercial_app.infrastructure.gateways.core_api_portal_access import (
    CoreApiPortalAccessPort,
)


@dataclass(frozen=True)
class DirectoryUserSummary:
    id: str
    name: str
    email: str


@dataclass(frozen=True)
class UserPhotoFile:
    path: Path
    file_name: str
    content_type: str


class ManageUserProfileUseCase:
    def __init__(
        self,
        *,
        repository: UserProfileRepositoryPort,
        storage: UserProfileStorage,
        portfolio_repository: SellerPortfolioRepositoryPort | None = None,
        portal_access: PortalAccessPort | None = None,
        directory_gateway: CoreApiPortalAccessPort | None = None,
    ) -> None:
        self._repo = repository
        self._storage = storage
        self._portfolios = portfolio_repository
        self._portal_access = portal_access
        self._directory = directory_gateway

    def _assert_can_view(self, *, target_user_id: str) -> None:
        # Qualquer usuário autenticado com permissão commercial de leitura (rota).
        _ = target_user_id

    def _assert_can_edit(
        self,
        *,
        actor_user_id: str,
        target_user_id: str,
        actor_is_portfolio_manager: bool,
    ) -> None:
        actor = (actor_user_id or "").strip()
        target = (target_user_id or "").strip()
        if actor and actor == target:
            return
        if actor_is_portfolio_manager:
            return
        raise PermissionError("Sem permissão para editar este perfil.")

    def _directory_user(self, user_id: str) -> DirectoryUserSummary:
        uid = user_id.strip()
        if self._directory is not None:
            items = self._directory.lookup_directory_users([uid])
            hit = items.get(uid)
            if hit:
                return DirectoryUserSummary(
                    id=str(hit.get("id") or uid),
                    name=str(hit.get("name") or uid),
                    email=str(hit.get("email") or ""),
                )
        return DirectoryUserSummary(id=uid, name=uid, email="")

    def _portfolio_summaries(self, user_id: str) -> list[dict[str, Any]]:
        if self._portfolios is None:
            return []
        portfolios = self._portfolios.list_by_user_id(user_id, active_only=True)
        return [
            {
                "id": str(item.id),
                "name": item.display_name,
                "active": bool(item.active),
                "user_id": item.user_id,
            }
            for item in portfolios
        ]

    def get_profile(self, *, user_id: str) -> dict[str, Any]:
        target = (user_id or "").strip()
        if not target:
            raise ValueError("Informe o usuário.")
        self._assert_can_view(target_user_id=target)
        directory = self._directory_user(target)
        profile = self._repo.get(target)
        payload = {
            "user_id": target,
            "name": directory.name,
            "email": directory.email,
            "job_title": profile.job_title if profile else None,
            "has_photo": bool(profile and profile.photo_storage_key),
            "photo_url": (
                f"/users/{target}/profile/photo"
                if profile and profile.photo_storage_key
                else None
            ),
            "portfolios": self._portfolio_summaries(target),
            "updated_at": (
                profile.updated_at.isoformat() if profile and profile.updated_at else None
            ),
        }
        return payload

    def update_job_title(
        self,
        *,
        actor_user_id: str,
        user_id: str,
        job_title: str | None,
        actor_is_portfolio_manager: bool = False,
    ) -> dict[str, Any]:
        target = (user_id or "").strip()
        self._assert_can_edit(
            actor_user_id=actor_user_id,
            target_user_id=target,
            actor_is_portfolio_manager=actor_is_portfolio_manager,
        )
        self._repo.upsert_job_title(user_id=target, job_title=job_title)
        return self.get_profile(user_id=target)

    def upload_photo(
        self,
        *,
        actor_user_id: str,
        user_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        actor_is_portfolio_manager: bool = False,
    ) -> dict[str, Any]:
        target = (user_id or "").strip()
        self._assert_can_edit(
            actor_user_id=actor_user_id,
            target_user_id=target,
            actor_is_portfolio_manager=actor_is_portfolio_manager,
        )
        existing = self._repo.get(target)
        try:
            stored = self._storage.save(
                user_id=target,
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except UserProfileStorageError as exc:
            raise ValueError(str(exc)) from exc
        if existing and existing.photo_storage_key and existing.photo_storage_key != stored.storage_key:
            self._storage.delete(existing.photo_storage_key)
        self._repo.upsert_photo(
            user_id=target,
            storage_key=stored.storage_key,
            file_name=stored.file_name,
            content_type=stored.content_type,
            byte_size=stored.byte_size,
        )
        return self.get_profile(user_id=target)

    def delete_photo(
        self,
        *,
        actor_user_id: str,
        user_id: str,
        actor_is_portfolio_manager: bool = False,
    ) -> dict[str, Any]:
        target = (user_id or "").strip()
        self._assert_can_edit(
            actor_user_id=actor_user_id,
            target_user_id=target,
            actor_is_portfolio_manager=actor_is_portfolio_manager,
        )
        existing = self._repo.get(target)
        if existing and existing.photo_storage_key:
            self._storage.delete(existing.photo_storage_key)
            self._repo.clear_photo(user_id=target)
        return self.get_profile(user_id=target)

    def get_photo_file(self, *, user_id: str) -> UserPhotoFile:
        target = (user_id or "").strip()
        profile = self._repo.get(target)
        if profile is None or not profile.photo_storage_key:
            raise LookupError("Foto não encontrada.")
        path = self._storage.resolve_path(profile.photo_storage_key)
        if not path.is_file():
            raise LookupError("Arquivo de foto não encontrado.")
        return UserPhotoFile(
            path=path,
            file_name=profile.photo_file_name or path.name,
            content_type=profile.photo_content_type or "application/octet-stream",
        )
