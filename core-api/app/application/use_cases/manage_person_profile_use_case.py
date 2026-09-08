from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from app.application.services.core_user_avatar_storage import (
    CoreUserAvatarStorage,
    CoreUserAvatarStorageError,
)
from app.domain.ports.person_profile_repository_port import PersonProfileRepositoryPort


@dataclass(frozen=True)
class PersonPhotoFile:
    path: Path
    file_name: str
    content_type: str


class ManagePersonProfileUseCase:
    def __init__(
        self,
        *,
        repository: PersonProfileRepositoryPort,
        storage: CoreUserAvatarStorage | None = None,
    ) -> None:
        self._repo = repository
        self._storage = storage or CoreUserAvatarStorage()

    @staticmethod
    def _assert_self(*, actor_user_id: UUID, target_user_id: UUID) -> None:
        if actor_user_id != target_user_id:
            raise PermissionError("Sem permissão para editar este perfil.")

    @staticmethod
    def _empty_payload(user_id: UUID) -> dict[str, Any]:
        return {
            "user_id": str(user_id),
            "job_title": None,
            "phone_e164": None,
            "mobile_e164": None,
            "whatsapp_e164": None,
            "has_photo": False,
            "photo_url": None,
            "updated_at": None,
        }

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

    @staticmethod
    def _validate_job_title(job_title: str | None) -> str | None:
        title = (job_title or "").strip() or None
        if title is not None and len(title) > 200:
            raise ValueError("Cargo deve ter no máximo 200 caracteres.")
        return title

    def get_profile(self, *, user_id: UUID) -> dict[str, Any]:
        profile = self._repo.get(user_id)
        if profile is None:
            return self._empty_payload(user_id)
        return profile.to_api_dict()

    def update_profile(
        self,
        *,
        actor_user_id: UUID,
        user_id: UUID,
        job_title: str | None,
        phone_e164: str | None = None,
        mobile_e164: str | None = None,
        whatsapp_e164: str | None = None,
    ) -> dict[str, Any]:
        self._assert_self(actor_user_id=actor_user_id, target_user_id=user_id)
        self._repo.upsert_profile_fields(
            user_id=user_id,
            job_title=self._validate_job_title(job_title),
            phone_e164=self._validate_phone(phone_e164),
            mobile_e164=self._validate_phone(mobile_e164),
            whatsapp_e164=self._validate_phone(whatsapp_e164),
        )
        return self.get_profile(user_id=user_id)

    def upload_photo(
        self,
        *,
        actor_user_id: UUID,
        user_id: UUID,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]:
        self._assert_self(actor_user_id=actor_user_id, target_user_id=user_id)
        existing = self._repo.get(user_id)
        try:
            stored = self._storage.save(
                user_id=str(user_id),
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except CoreUserAvatarStorageError as exc:
            raise ValueError(str(exc)) from exc
        if (
            existing
            and existing.photo_storage_key
            and existing.photo_storage_key != stored.storage_key
        ):
            self._storage.delete(existing.photo_storage_key)
        self._repo.upsert_photo(
            user_id=user_id,
            storage_key=stored.storage_key,
            file_name=stored.file_name,
            content_type=stored.content_type,
            byte_size=stored.byte_size,
        )
        return self.get_profile(user_id=user_id)

    def delete_photo(
        self,
        *,
        actor_user_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any]:
        self._assert_self(actor_user_id=actor_user_id, target_user_id=user_id)
        existing = self._repo.get(user_id)
        if existing and existing.photo_storage_key:
            self._storage.delete(existing.photo_storage_key)
            self._repo.clear_photo(user_id=user_id)
        return self.get_profile(user_id=user_id)

    def get_photo_file(self, *, user_id: UUID) -> PersonPhotoFile:
        profile = self._repo.get(user_id)
        if profile is None or not profile.photo_storage_key:
            raise LookupError("Foto não encontrada.")
        path = self._storage.resolve_path(profile.photo_storage_key)
        if not path.is_file():
            raise LookupError("Arquivo de foto não encontrado.")
        return PersonPhotoFile(
            path=path,
            file_name=profile.photo_file_name or path.name,
            content_type=profile.photo_content_type or "application/octet-stream",
        )

    def purge_for_user(self, *, user_id: UUID) -> bool:
        """Remove metadados e arquivo (LGPD anonymize)."""
        existing = self._repo.get(user_id)
        if existing is None:
            return False
        if existing.photo_storage_key:
            self._storage.delete(existing.photo_storage_key)
        self._repo.delete(user_id)
        return True
