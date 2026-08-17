from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tm_app.application.security import transformometro_permissions as perms
from tm_app.application.services.user_signature_service import UserSignatureService


def _user(*, permissions: list[str] | None = None, is_superadmin: bool = False, user_id: str = "u1"):
    return SimpleNamespace(id=user_id, permissions=permissions or [], is_superadmin=is_superadmin, name="Ana")


def _service() -> UserSignatureService:
    repo = MagicMock()
    repo.get_by_user.return_value = None
    repo.upsert_profile.side_effect = lambda **kw: {
        "user_id": kw["user_id"],
        "display_name": kw["display_name"],
        "signature_path": None,
        "updated_at": "2026-01-01",
    }
    repo.update_signature_path.side_effect = lambda **kw: {
        "user_id": kw["user_id"],
        "display_name": kw["display_name"],
        "signature_path": kw["signature_path"],
        "updated_at": "2026-01-01",
    }
    storage = MagicMock()
    storage.exists.return_value = True
    storage.save_png.return_value = "/tmp/sig.png"
    storage.read.return_value = b"\x89PNG"
    return UserSignatureService(repo=repo, storage=storage)


@pytest.mark.parametrize(
    "permission",
    [
        perms.TRANSFORMOMETRO_ATAS_VIEW,
        perms.TRANSFORMOMETRO_ATAS_MANAGE,
        perms.TRANSFORMOMETRO_ATAS_SIGN,
        perms.TRANSFORMOMETRO_MEETING_MINUTES_VIEW,
        perms.TRANSFORMOMETRO_MEETING_MINUTES_MANAGE,
        perms.TRANSFORMOMETRO_MEETING_MINUTES_SIGN,
    ],
)
def test_profile_allows_any_atas_permission(permission: str) -> None:
    service = _service()
    user = _user(permissions=[permission])
    assert service.get_me(user)["user_id"] == "u1"
    assert service.update_display_name(user, "Ana Silva")["display_name"] == "Ana Silva"
    assert service.save_image(user, b"\x89PNG\r\n")["has_signature"] is True


def test_profile_allows_superadmin_without_atas_permission() -> None:
    service = _service()
    user = _user(permissions=["outro.app.x"], is_superadmin=True)
    assert service.get_me(user)["user_id"] == "u1"
    assert service.save_image(user, b"\x89PNG\r\n")["has_signature"] is True


def test_profile_denies_without_atas_permission() -> None:
    service = _service()
    user = _user(permissions=["outro.app.x"], is_superadmin=False)
    with pytest.raises(PermissionError, match="assinatura pessoal"):
        service.get_me(user)


def test_profile_denies_empty_permissions_without_superadmin() -> None:
    service = _service()
    user = _user(permissions=[], is_superadmin=False)
    with pytest.raises(PermissionError, match="assinatura pessoal"):
        service.save_image(user, b"\x89PNG\r\n")
