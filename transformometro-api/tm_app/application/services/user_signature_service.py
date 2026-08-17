from __future__ import annotations

from pathlib import Path
from typing import Any

from tm_app.application.security import transformometro_permissions as perms
from tm_app.application.services.meeting_minutes_storage import TmAtaStorageError, UserSignatureStorageService
from tm_app.infrastructure.persistence.repositories.user_signature_repository import UserSignatureRepository

_PROFILE_PERMISSIONS: frozenset[str] = frozenset(perms.MEETING_MINUTES_PROFILE_PERMISSIONS)


class UserSignatureService:
    def __init__(self, repo: UserSignatureRepository | None = None, storage: UserSignatureStorageService | None = None) -> None:
        self.repo, self.storage = repo or UserSignatureRepository(), storage or UserSignatureStorageService()

    @staticmethod
    def _user_id(user: Any) -> str:
        value = str(getattr(user, "id", None) or getattr(user, "sub", None) or "")
        if not value:
            raise PermissionError("Usuário não identificado.")
        return value

    @staticmethod
    def _has_profile_permission(user: Any) -> bool:
        if getattr(user, "is_superadmin", False):
            return True
        permissions = set(getattr(user, "permissions", None) or getattr(user, "roles", None) or [])
        return bool(permissions & _PROFILE_PERMISSIONS)

    def _assert_profile_access(self, user: Any) -> None:
        if not self._has_profile_permission(user):
            raise PermissionError("Sem permissão para gerenciar a assinatura pessoal.")

    def _payload(self, row: dict[str, Any] | None, user_id: str) -> dict[str, Any]:
        if not row:
            return {"user_id": user_id, "display_name": "", "has_signature": False, "updated_at": None}
        path = row.get("signature_path")
        return {
            "user_id": str(row.get("user_id") or user_id),
            "display_name": str(row.get("display_name") or ""),
            "has_signature": bool(path and Path(str(path)).is_file()) or self.storage.exists(user_id),
            "updated_at": row.get("updated_at"),
        }

    def get_me(self, user: Any) -> dict[str, Any]:
        self._assert_profile_access(user)
        user_id = self._user_id(user)
        return self._payload(self.repo.get_by_user(user_id), user_id)

    def update_display_name(self, user: Any, display_name: str) -> dict[str, Any]:
        self._assert_profile_access(user)
        user_id = self._user_id(user)
        name = (display_name or "").strip()
        if not name:
            raise ValueError("Informe o nome para assinatura.")
        if len(name) > 200:
            raise ValueError("Nome para assinatura excede 200 caracteres.")
        return self._payload(self.repo.upsert_profile(user_id=user_id, display_name=name), user_id)

    def save_image(self, user: Any, raw: bytes) -> dict[str, Any]:
        self._assert_profile_access(user)
        user_id = self._user_id(user)
        try:
            path = self.storage.save_png(user_id=user_id, raw=raw)
        except TmAtaStorageError as exc:
            raise ValueError(str(exc)) from exc
        existing = self.repo.get_by_user(user_id) or {}
        name = str(
            existing.get("display_name")
            or getattr(user, "name", None)
            or getattr(user, "preferred_username", None)
            or "Signatário"
        ).strip()
        return self._payload(
            self.repo.update_signature_path(user_id=user_id, signature_path=path, display_name=name),
            user_id,
        )

    def read_image(self, user: Any) -> bytes:
        self._assert_profile_access(user)
        try:
            return self.storage.read(self._user_id(user))
        except TmAtaStorageError as exc:
            raise LookupError(str(exc)) from exc
