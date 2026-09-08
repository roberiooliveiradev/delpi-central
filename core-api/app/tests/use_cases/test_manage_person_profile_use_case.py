from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.application.services.core_user_avatar_storage import CoreUserAvatarStorage
from app.application.use_cases.manage_person_profile_use_case import ManagePersonProfileUseCase
from app.domain.entities.person_profile import PersonProfile


class InMemoryPersonProfileRepo:
    def __init__(self) -> None:
        self.items: dict[UUID, PersonProfile] = {}

    def get(self, user_id: UUID) -> PersonProfile | None:
        return self.items.get(user_id)

    def upsert_profile_fields(
        self,
        *,
        user_id: UUID,
        job_title: str | None,
        phone_e164: str | None,
        mobile_e164: str | None,
        whatsapp_e164: str | None,
    ) -> PersonProfile:
        now = datetime.now(timezone.utc)
        current = self.items.get(user_id)
        profile = PersonProfile(
            user_id=user_id,
            job_title=job_title,
            phone_e164=phone_e164,
            mobile_e164=mobile_e164,
            whatsapp_e164=whatsapp_e164,
            photo_storage_key=current.photo_storage_key if current else None,
            photo_file_name=current.photo_file_name if current else None,
            photo_content_type=current.photo_content_type if current else None,
            photo_byte_size=current.photo_byte_size if current else None,
            created_at=current.created_at if current else now,
            updated_at=now,
        )
        self.items[user_id] = profile
        return profile

    def upsert_photo(
        self,
        *,
        user_id: UUID,
        storage_key: str,
        file_name: str,
        content_type: str,
        byte_size: int,
    ) -> PersonProfile:
        now = datetime.now(timezone.utc)
        current = self.items.get(user_id)
        profile = PersonProfile(
            user_id=user_id,
            job_title=current.job_title if current else None,
            phone_e164=current.phone_e164 if current else None,
            mobile_e164=current.mobile_e164 if current else None,
            whatsapp_e164=current.whatsapp_e164 if current else None,
            photo_storage_key=storage_key,
            photo_file_name=file_name,
            photo_content_type=content_type,
            photo_byte_size=byte_size,
            created_at=current.created_at if current else now,
            updated_at=now,
        )
        self.items[user_id] = profile
        return profile

    def clear_photo(self, *, user_id: UUID) -> PersonProfile | None:
        current = self.items.get(user_id)
        if current is None:
            return None
        profile = PersonProfile(
            user_id=user_id,
            job_title=current.job_title,
            phone_e164=current.phone_e164,
            mobile_e164=current.mobile_e164,
            whatsapp_e164=current.whatsapp_e164,
            photo_storage_key=None,
            photo_file_name=None,
            photo_content_type=None,
            photo_byte_size=None,
            created_at=current.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        self.items[user_id] = profile
        return profile

    def delete(self, user_id: UUID) -> None:
        self.items.pop(user_id, None)


def _uc(tmp_path: Path) -> tuple[ManagePersonProfileUseCase, InMemoryPersonProfileRepo]:
    repo = InMemoryPersonProfileRepo()
    storage = CoreUserAvatarStorage(base_dir=str(tmp_path))
    return ManagePersonProfileUseCase(repository=repo, storage=storage), repo


def test_update_profile_self_positive(tmp_path: Path) -> None:
    uc, _ = _uc(tmp_path)
    user_id = uuid4()
    payload = uc.update_profile(
        actor_user_id=user_id,
        user_id=user_id,
        job_title="Analista",
        phone_e164="+5511999999999",
        mobile_e164="+5511888888888",
        whatsapp_e164="+5511888888888",
    )
    assert payload["job_title"] == "Analista"
    assert payload["phone_e164"] == "+5511999999999"
    assert payload["whatsapp_e164"] == "+5511888888888"
    assert payload["has_photo"] is False


def test_update_profile_other_user_forbidden(tmp_path: Path) -> None:
    uc, _ = _uc(tmp_path)
    with pytest.raises(PermissionError):
        uc.update_profile(
            actor_user_id=uuid4(),
            user_id=uuid4(),
            job_title="X",
        )


def test_clear_fields_sibling(tmp_path: Path) -> None:
    uc, _ = _uc(tmp_path)
    user_id = uuid4()
    uc.update_profile(
        actor_user_id=user_id,
        user_id=user_id,
        job_title="Cargo",
        phone_e164="+5511333333333",
        mobile_e164=None,
        whatsapp_e164=None,
    )
    cleared = uc.update_profile(
        actor_user_id=user_id,
        user_id=user_id,
        job_title="",
        phone_e164=None,
        mobile_e164=None,
        whatsapp_e164=None,
    )
    assert cleared["job_title"] is None
    assert cleared["phone_e164"] is None


def test_invalid_phone_rejected(tmp_path: Path) -> None:
    uc, _ = _uc(tmp_path)
    user_id = uuid4()
    with pytest.raises(ValueError, match="E.164"):
        uc.update_profile(
            actor_user_id=user_id,
            user_id=user_id,
            job_title=None,
            phone_e164="119999",
        )


def test_photo_upload_and_delete(tmp_path: Path) -> None:
    uc, _ = _uc(tmp_path)
    user_id = uuid4()
    uploaded = uc.upload_photo(
        actor_user_id=user_id,
        user_id=user_id,
        original_name="me.png",
        content=b"\x89PNG\r\n\x1a\n" + b"0" * 32,
        mime_type="image/png",
    )
    assert uploaded["has_photo"] is True
    assert uploaded["photo_url"] == "/me/person-profile/photo"
    photo = uc.get_photo_file(user_id=user_id)
    assert photo.path.is_file()
    deleted = uc.delete_photo(actor_user_id=user_id, user_id=user_id)
    assert deleted["has_photo"] is False


def test_storage_rejects_oversize(tmp_path: Path) -> None:
    storage = CoreUserAvatarStorage(base_dir=str(tmp_path))
    with pytest.raises(Exception, match="2 MB"):
        storage.validate_upload(mime_type="image/png", size_bytes=3 * 1024 * 1024)


def test_purge_removes_photo_file(tmp_path: Path) -> None:
    uc, repo = _uc(tmp_path)
    user_id = uuid4()
    uc.upload_photo(
        actor_user_id=user_id,
        user_id=user_id,
        original_name="me.jpg",
        content=b"jpeg-bytes",
        mime_type="image/jpeg",
    )
    key = repo.get(user_id).photo_storage_key
    assert key
    path = CoreUserAvatarStorage(base_dir=str(tmp_path)).resolve_path(key)
    assert path.is_file()
    assert uc.purge_for_user(user_id=user_id) is True
    assert repo.get(user_id) is None
    assert not path.exists()
