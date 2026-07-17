from types import SimpleNamespace
from unittest.mock import patch

import pytest

from cipa_app.application.security import cipa_permissions as perms
from cipa_app.application.services.storage_services import (
    CipaStorageError,
    UserSignatureStorageService,
)
from cipa_app.application.use_cases.user_signature_service import UserSignatureService


PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


def _user(*, user_id: str, permissions: list[str]):
    return SimpleNamespace(
        id=user_id,
        sub=user_id,
        name="Fulano",
        permissions=permissions,
        is_superadmin=False,
    )


def test_assert_global_action_requires_sign():
    user = _user(user_id=USER_A, permissions=["cipa.view"])
    with pytest.raises(PermissionError):
        perms.assert_global_action(user, "sign")


def test_assert_global_action_allows_sign():
    user = _user(user_id=USER_A, permissions=["cipa.sign"])
    perms.assert_global_action(user, "sign")


def test_user_signature_storage_rejects_non_png(tmp_path):
    storage = UserSignatureStorageService(base_dir=str(tmp_path), max_bytes=1024)
    with pytest.raises(CipaStorageError):
        storage.save_png(user_id=USER_A, raw=b"not-png")


def test_user_signature_storage_accepts_and_reads(tmp_path):
    storage = UserSignatureStorageService(base_dir=str(tmp_path), max_bytes=1024)
    path = storage.save_png(user_id=USER_A, raw=PNG)
    assert path.endswith(f"{USER_A}.png")
    assert storage.exists(USER_A)
    assert storage.read(USER_A) == PNG


def test_user_signature_storage_rejects_oversized(tmp_path):
    storage = UserSignatureStorageService(base_dir=str(tmp_path), max_bytes=10)
    with pytest.raises(CipaStorageError):
        storage.save_png(user_id=USER_A, raw=PNG)


def test_get_me_forbidden_without_sign():
    svc = UserSignatureService()
    user = _user(user_id=USER_A, permissions=["cipa.view"])
    with pytest.raises(PermissionError):
        svc.get_me(user)


def test_update_display_name_persists():
    svc = UserSignatureService()
    user = _user(user_id=USER_A, permissions=["cipa.sign"])
    row = {
        "user_id": USER_A,
        "display_name": "Maria Silva",
        "signature_path": None,
        "updated_at": "2026-07-16T12:00:00+00:00",
    }
    with patch.object(svc.repo, "upsert_profile", return_value=row) as upsert:
        payload = svc.update_display_name(user, "  Maria Silva  ")
    upsert.assert_called_once_with(user_id=USER_A, display_name="Maria Silva")
    assert payload["display_name"] == "Maria Silva"
    assert payload["has_signature"] is False


def test_update_display_name_rejects_empty():
    svc = UserSignatureService()
    user = _user(user_id=USER_A, permissions=["cipa.sign"])
    with pytest.raises(ValueError):
        svc.update_display_name(user, "   ")


def test_save_and_read_image_isolates_by_token_user(tmp_path):
    svc = UserSignatureService()
    svc.storage = UserSignatureStorageService(base_dir=str(tmp_path), max_bytes=1024)
    user_a = _user(user_id=USER_A, permissions=["cipa.sign"])
    user_b = _user(user_id=USER_B, permissions=["cipa.sign"])

    with patch.object(
        svc.repo,
        "get_by_user",
        return_value={"display_name": "A", "signature_path": None},
    ):
        with patch.object(
            svc.repo,
            "update_signature_path",
            side_effect=lambda **kwargs: {
                "user_id": kwargs["user_id"],
                "display_name": "A",
                "signature_path": kwargs["signature_path"],
                "updated_at": "2026-07-16T12:00:00+00:00",
            },
        ):
            payload = svc.save_image(user_a, PNG)

    assert payload["has_signature"] is True
    assert svc.read_image(user_a) == PNG

    with pytest.raises(LookupError):
        svc.read_image(user_b)


def test_save_image_rejects_non_png():
    svc = UserSignatureService()
    user = _user(user_id=USER_A, permissions=["cipa.sign"])
    with patch.object(
        svc.storage,
        "save_png",
        side_effect=CipaStorageError("Formato de assinatura inválido. Envie uma imagem PNG."),
    ):
        with pytest.raises(ValueError, match="PNG"):
            svc.save_image(user, b"jpeg")
