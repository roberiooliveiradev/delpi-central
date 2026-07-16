from __future__ import annotations

from pathlib import Path
from typing import Any

from cipa_app.application.security import cipa_permissions as perms
from cipa_app.application.services.storage_services import (
    CipaStorageError,
    UserSignatureStorageService,
)
from cipa_app.infrastructure.persistence.repositories.user_signature_repository import (
    UserSignatureRepository,
)


class UserSignatureService:
    def __init__(self) -> None:
        self.repo = UserSignatureRepository()
        self.storage = UserSignatureStorageService()

    def _user_id(self, user) -> str:
        user_id = str(getattr(user, "id", None) or getattr(user, "sub", None) or "")
        if not user_id:
            raise PermissionError("Usuário não identificado.")
        return user_id

    def _assert_sign(self, user) -> None:
        perms.assert_global_action(user, "sign")

    def _to_payload(self, row: dict[str, Any] | None, *, user_id: str) -> dict[str, Any]:
        if not row:
            return {
                "user_id": user_id,
                "display_name": "",
                "has_signature": False,
                "updated_at": None,
            }
        path = row.get("signature_path")
        has_file = bool(path and Path(str(path)).is_file()) or self.storage.exists(user_id)
        return {
            "user_id": str(row.get("user_id") or user_id),
            "display_name": str(row.get("display_name") or ""),
            "has_signature": has_file,
            "updated_at": row.get("updated_at"),
        }

    def get_me(self, user) -> dict[str, Any]:
        self._assert_sign(user)
        user_id = self._user_id(user)
        return self._to_payload(self.repo.get_by_user(user_id), user_id=user_id)

    def update_display_name(self, user, display_name: str) -> dict[str, Any]:
        self._assert_sign(user)
        user_id = self._user_id(user)
        name = (display_name or "").strip()
        if not name:
            raise ValueError("Informe o nome para assinatura.")
        if len(name) > 200:
            raise ValueError("Nome para assinatura excede 200 caracteres.")
        row = self.repo.upsert_profile(user_id=user_id, display_name=name)
        return self._to_payload(row, user_id=user_id)

    def save_image(self, user, raw: bytes) -> dict[str, Any]:
        self._assert_sign(user)
        user_id = self._user_id(user)
        try:
            path = self.storage.save_png(user_id=user_id, raw=raw)
        except CipaStorageError as exc:
            raise ValueError(str(exc)) from exc

        existing = self.repo.get_by_user(user_id)
        display_name = str((existing or {}).get("display_name") or "").strip()
        if not display_name:
            display_name = (
                str(getattr(user, "name", None) or getattr(user, "preferred_username", None) or "")
                .strip()
                or "Signatário"
            )
        row = self.repo.update_signature_path(
            user_id=user_id,
            signature_path=path,
            display_name=display_name,
        )
        return self._to_payload(row, user_id=user_id)

    def read_image(self, user) -> bytes:
        self._assert_sign(user)
        user_id = self._user_id(user)
        try:
            return self.storage.read(user_id)
        except CipaStorageError as exc:
            raise LookupError(str(exc)) from exc
