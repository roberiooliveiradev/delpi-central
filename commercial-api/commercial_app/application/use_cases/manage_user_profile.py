from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from commercial_app.application.services.user_profile_storage import (
    UserProfileStorage,
    UserProfileStorageError,
)
from commercial_app.application.use_cases.manage_commercial_groups import (
    ManageCommercialGroupsUseCase,
    group_summary_to_dict,
)
from commercial_app.domain.ports.portal_access_port import PortalAccessPort
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.ports.user_profile_repository_port import UserProfileRepositoryPort
from commercial_app.domain.services.portfolio_membership_summary_service import (
    portfolio_profile_summary_dict,
)
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
    path: Path | None
    file_name: str
    content_type: str
    content: bytes | None = None


class ManageUserProfileUseCase:
    def __init__(
        self,
        *,
        repository: UserProfileRepositoryPort,
        storage: UserProfileStorage,
        portfolio_repository: SellerPortfolioRepositoryPort | None = None,
        portal_access: PortalAccessPort | None = None,
        directory_gateway: CoreApiPortalAccessPort | None = None,
        groups: ManageCommercialGroupsUseCase | None = None,
    ) -> None:
        self._repo = repository
        self._storage = storage
        self._portfolios = portfolio_repository
        self._portal_access = portal_access
        self._directory = directory_gateway
        self._groups = groups

    def _assert_can_view(self, *, target_user_id: str) -> None:
        # Qualquer usuário autenticado com permissão commercial de leitura (rota).
        _ = target_user_id

    def _assert_can_edit(
        self,
        *,
        actor_user_id: str,
        target_user_id: str,
    ) -> None:
        actor = (actor_user_id or "").strip()
        target = (target_user_id or "").strip()
        if actor and actor == target:
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
        uid = (user_id or "").strip()
        portfolios = self._portfolios.list_by_user_id(uid, active_only=True)
        return [
            portfolio_profile_summary_dict(item, viewer_user_id=uid)
            for item in portfolios
        ]

    def _group_summaries(self, user_id: str) -> list[dict[str, Any]]:
        if self._groups is None:
            return []
        uid = (user_id or "").strip()
        if not uid:
            return []
        return [
            group_summary_to_dict(group)
            for group in self._groups.list_groups_by_user_id(uid)
        ]

    def _core_person_profile(self, user_id: str) -> dict[str, Any] | None:
        if self._directory is None:
            return None
        return self._directory.get_person_profile(user_id)

    @staticmethod
    def _nonempty(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return True

    def _merge_field(self, core: dict[str, Any] | None, local: Any, key: str) -> Any:
        if core is not None and self._nonempty(core.get(key)):
            return core.get(key)
        return local

    def get_profile(self, *, user_id: str) -> dict[str, Any]:
        target = (user_id or "").strip()
        if not target:
            raise ValueError("Informe o usuário.")
        self._assert_can_view(target_user_id=target)
        directory = self._directory_user(target)
        profile = self._repo.get(target)
        core = self._core_person_profile(target)

        job_title = self._merge_field(
            core, profile.job_title if profile else None, "job_title"
        )
        phone_e164 = self._merge_field(
            core, profile.phone_e164 if profile else None, "phone_e164"
        )
        mobile_e164 = self._merge_field(
            core, profile.mobile_e164 if profile else None, "mobile_e164"
        )
        whatsapp_e164 = self._merge_field(
            core, profile.whatsapp_e164 if profile else None, "whatsapp_e164"
        )

        local_has_photo = bool(profile and profile.photo_storage_key)
        core_has_photo = bool(core and core.get("has_photo"))
        has_photo = core_has_photo or local_has_photo

        payload = {
            "user_id": target,
            "name": directory.name,
            "email": directory.email,
            "job_title": job_title,
            "phone_e164": phone_e164,
            "mobile_e164": mobile_e164,
            "whatsapp_e164": whatsapp_e164,
            "has_photo": has_photo,
            "photo_url": (f"/users/{target}/profile/photo" if has_photo else None),
            "portfolios": self._portfolio_summaries(target),
            "groups": self._group_summaries(target),
            "updated_at": (
                profile.updated_at.isoformat() if profile and profile.updated_at else None
            ),
        }
        return payload

    @staticmethod
    def _validate_phone(phone_e164: str | None) -> str | None:
        phone = (phone_e164 or "").strip() or None
        if phone is None:
            return None
        digits = phone[1:] if phone.startswith("+") else ""
        if not digits.isdigit() or not 8 <= len(digits) <= 16:
            raise ValueError(
                "Telefone deve estar no formato E.164: + seguido de 8 a 16 dígitos."
            )
        return phone

    def _require_authorization(self, authorization: str | None) -> str:
        token = (authorization or "").strip()
        if not token:
            raise ValueError(
                "Authorization obrigatória para sincronizar o perfil com o Portal."
            )
        return token

    def _mirror_profile_fields(
        self,
        *,
        authorization: str | None,
        job_title: str | None,
        phone_e164: str | None,
        mobile_e164: str | None,
        whatsapp_e164: str | None,
    ) -> None:
        if self._directory is None:
            return
        self._directory.mirror_person_profile(
            authorization=self._require_authorization(authorization),
            job_title=job_title,
            phone_e164=phone_e164,
            mobile_e164=mobile_e164,
            whatsapp_e164=whatsapp_e164,
        )

    def update_profile(
        self,
        *,
        actor_user_id: str,
        user_id: str,
        job_title: str | None,
        phone_e164: str | None = None,
        mobile_e164: str | None = None,
        whatsapp_e164: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        target = (user_id or "").strip()
        self._assert_can_edit(
            actor_user_id=actor_user_id,
            target_user_id=target,
        )
        validated_phone = self._validate_phone(phone_e164)
        validated_mobile = self._validate_phone(mobile_e164)
        validated_whatsapp = self._validate_phone(whatsapp_e164)
        self._repo.upsert_profile_fields(
            user_id=target,
            job_title=job_title,
            phone_e164=validated_phone,
            mobile_e164=validated_mobile,
            whatsapp_e164=validated_whatsapp,
        )
        self._mirror_profile_fields(
            authorization=authorization,
            job_title=job_title,
            phone_e164=validated_phone,
            mobile_e164=validated_mobile,
            whatsapp_e164=validated_whatsapp,
        )
        return self.get_profile(user_id=target)

    def update_job_title(
        self,
        *,
        actor_user_id: str,
        user_id: str,
        job_title: str | None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        """Compat: atualiza só o cargo preservando contatos existentes."""
        target = (user_id or "").strip()
        current = self._repo.get(target)
        return self.update_profile(
            actor_user_id=actor_user_id,
            user_id=target,
            job_title=job_title,
            phone_e164=current.phone_e164 if current else None,
            mobile_e164=current.mobile_e164 if current else None,
            whatsapp_e164=current.whatsapp_e164 if current else None,
            authorization=authorization,
        )

    def upload_photo(
        self,
        *,
        actor_user_id: str,
        user_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        target = (user_id or "").strip()
        self._assert_can_edit(
            actor_user_id=actor_user_id,
            target_user_id=target,
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
        if self._directory is not None:
            self._directory.mirror_person_profile_photo(
                authorization=self._require_authorization(authorization),
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        return self.get_profile(user_id=target)

    def delete_photo(
        self,
        *,
        actor_user_id: str,
        user_id: str,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        target = (user_id or "").strip()
        self._assert_can_edit(
            actor_user_id=actor_user_id,
            target_user_id=target,
        )
        existing = self._repo.get(target)
        if existing and existing.photo_storage_key:
            self._storage.delete(existing.photo_storage_key)
            self._repo.clear_photo(user_id=target)
        if self._directory is not None:
            self._directory.mirror_delete_person_profile_photo(
                authorization=self._require_authorization(authorization),
            )
        return self.get_profile(user_id=target)

    def get_photo_file(self, *, user_id: str) -> UserPhotoFile:
        target = (user_id or "").strip()
        core = self._core_person_profile(target)
        if core and core.get("has_photo") and self._directory is not None:
            downloaded = self._directory.get_person_profile_photo(target)
            if downloaded is not None:
                content, content_type, file_name = downloaded
                return UserPhotoFile(
                    path=None,
                    file_name=file_name,
                    content_type=content_type,
                    content=content,
                )
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
