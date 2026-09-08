from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from commercial_app.application.services.user_profile_storage import UserProfileStorage
from commercial_app.application.use_cases.manage_commercial_groups import (
    ManageCommercialGroupsUseCase,
)
from commercial_app.application.use_cases.manage_user_profile import ManageUserProfileUseCase
from commercial_app.domain.entities.commercial_group import (
    CommercialGroup,
    CommercialGroupMember,
)
from commercial_app.domain.entities.seller_portfolio import SellerPortfolio
from commercial_app.domain.entities.user_profile import CommercialUserProfile


class FakeGroupsRepo:
    def __init__(self, groups: list[CommercialGroup]) -> None:
        self._groups = groups

    def list_groups_by_user_id(self, user_id: str) -> list[CommercialGroup]:
        uid = user_id.strip()
        return [
            CommercialGroup(
                id=group.id,
                kind=group.kind,
                name=group.name,
                active=group.active,
                sort_order=group.sort_order,
                members=(),
            )
            for group in self._groups
            if any(member.user_id == uid for member in group.members)
        ]

    def list_groups(self, *, active_only: bool = False) -> list[CommercialGroup]:
        return list(self._groups)

    def get_by_id(self, group_id: str) -> CommercialGroup | None:
        return next((item for item in self._groups if item.id == group_id), None)

    def get_by_kind(self, kind: str) -> CommercialGroup | None:
        return next((item for item in self._groups if item.kind == kind), None)

    def create_group(self, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def replace_members(self, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def add_member(self, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def remove_member(self, **kwargs):  # pragma: no cover
        raise NotImplementedError

    def list_member_user_ids_by_group_id(self, group_id: str) -> list[str]:
        group = self.get_by_id(group_id)
        return [member.user_id for member in group.members] if group else []

    def list_memberships_by_user_ids(self, user_ids):
        return []


def test_user_profile_includes_groups(tmp_path: Path) -> None:
    repo = InMemoryUserProfileRepo()
    storage = UserProfileStorage(base_dir=str(tmp_path))
    groups = ManageCommercialGroupsUseCase(
        FakeGroupsRepo(  # type: ignore[arg-type]
            [
                CommercialGroup(
                    id="g1",
                    kind="sellers",
                    name="Vendedores",
                    active=True,
                    sort_order=1,
                    members=(CommercialGroupMember(user_id="u1"),),
                ),
                CommercialGroup(
                    id="g2",
                    kind="billing",
                    name="Faturamento",
                    active=True,
                    sort_order=2,
                    members=(CommercialGroupMember(user_id="u2"),),
                ),
            ]
        )
    )
    uc = ManageUserProfileUseCase(
        repository=repo,
        storage=storage,
        portfolio_repository=FakePortfolioRepo(),  # type: ignore[arg-type]
        groups=groups,
    )
    payload = uc.get_profile(user_id="u1")
    assert [item["kind"] for item in payload["groups"]] == ["sellers"]
    assert payload["groups"][0]["name"] == "Vendedores"
    assert "members" not in payload["groups"][0]

    empty = uc.get_profile(user_id="u3")
    assert empty["groups"] == []



class InMemoryUserProfileRepo:
    def __init__(self) -> None:
        self.items: dict[str, CommercialUserProfile] = {}

    def get(self, user_id: str) -> CommercialUserProfile | None:
        return self.items.get(user_id)

    def upsert_profile_fields(
        self,
        *,
        user_id: str,
        job_title: str | None,
        phone_e164: str | None,
        mobile_e164: str | None,
        whatsapp_e164: str | None,
    ) -> CommercialUserProfile:
        now = datetime.now(timezone.utc)
        current = self.items.get(user_id)
        profile = CommercialUserProfile(
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
        user_id: str,
        storage_key: str,
        file_name: str,
        content_type: str,
        byte_size: int,
    ) -> CommercialUserProfile:
        now = datetime.now(timezone.utc)
        current = self.items.get(user_id)
        profile = CommercialUserProfile(
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

    def clear_photo(self, *, user_id: str) -> CommercialUserProfile | None:
        current = self.items.get(user_id)
        if current is None:
            return None
        now = datetime.now(timezone.utc)
        profile = CommercialUserProfile(
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
            updated_at=now,
        )
        self.items[user_id] = profile
        return profile


class FakePortfolioRepo:
    def list_by_user_id(self, user_id: str, *, active_only: bool = True) -> list[SellerPortfolio]:
        from commercial_app.domain.entities.seller_portfolio import (
            SellerCustomerAssignment,
            SellerPortfolioMember,
        )

        return [
            SellerPortfolio(
                id="p1",
                user_id=user_id,
                display_name="Carteira Sul",
                active=True,
                customers=(
                    SellerCustomerAssignment(
                        customer_code="0001",
                        customer_store="01",
                        customer_name="Acme",
                    ),
                ),
                members=(SellerPortfolioMember(user_id=user_id, role="owner"),),
            )
        ]


def test_user_profile_self_edit_and_photo(tmp_path: Path) -> None:
    repo = InMemoryUserProfileRepo()
    storage = UserProfileStorage(base_dir=str(tmp_path))
    uc = ManageUserProfileUseCase(
        repository=repo,
        storage=storage,
        portfolio_repository=FakePortfolioRepo(),  # type: ignore[arg-type]
    )
    payload = uc.update_job_title(
        actor_user_id="u1",
        user_id="u1",
        job_title="Consultor",
    )
    assert payload["job_title"] == "Consultor"
    assert payload["portfolios"][0]["name"] == "Carteira Sul"
    assert payload["portfolios"][0]["role"] == "owner"
    assert payload["portfolios"][0]["customer_count"] == 1
    assert payload["portfolios"][0]["member_count"] == 1

    contacts = uc.update_profile(
        actor_user_id="u1",
        user_id="u1",
        job_title="Consultor",
        phone_e164="+551133334444",
        mobile_e164="+5511999887766",
        whatsapp_e164="+5511999887766",
    )
    assert contacts["phone_e164"] == "+551133334444"
    assert contacts["mobile_e164"] == "+5511999887766"
    assert contacts["whatsapp_e164"] == "+5511999887766"

    with pytest.raises(ValueError):
        uc.update_profile(
            actor_user_id="u1",
            user_id="u1",
            job_title="Consultor",
            phone_e164="119999",
        )

    with pytest.raises(PermissionError):
        uc.update_job_title(
            actor_user_id="u2",
            user_id="u1",
            job_title="Hack",
        )

    with pytest.raises(PermissionError):
        uc.update_job_title(
            actor_user_id="manager",
            user_id="u1",
            job_title="Manager override",
        )

    photo = uc.upload_photo(
        actor_user_id="u1",
        user_id="u1",
        original_name="me.png",
        content=b"\x89PNG\r\n\x1a\n" + b"0" * 20,
        mime_type="image/png",
    )
    assert photo["has_photo"] is True
    file_info = uc.get_photo_file(user_id="u1")
    assert file_info.path.is_file()

    with pytest.raises(PermissionError):
        uc.delete_photo(actor_user_id="manager", user_id="u1")

    cleared = uc.delete_photo(actor_user_id="u1", user_id="u1")
    assert cleared["has_photo"] is False


class FakePersonProfileGateway:
    def __init__(self) -> None:
        self.profiles: dict[str, dict] = {}
        self.photos: dict[str, tuple[bytes, str, str]] = {}
        self.mirrored_profiles: list[dict] = []
        self.mirrored_photos: list[dict] = []
        self.deleted_photos: list[str] = []
        self.fail_mirror = False

    def lookup_directory_users(self, user_ids):
        return {}

    def get_person_profile(self, user_id: str):
        return self.profiles.get(user_id)

    def get_person_profile_photo(self, user_id: str):
        return self.photos.get(user_id)

    def mirror_person_profile(self, **kwargs):
        if self.fail_mirror:
            raise RuntimeError("Não foi possível sincronizar o perfil com o Portal.")
        self.mirrored_profiles.append(kwargs)

    def mirror_person_profile_photo(self, **kwargs):
        if self.fail_mirror:
            raise RuntimeError("Não foi possível sincronizar a foto com o Portal.")
        self.mirrored_photos.append(kwargs)

    def mirror_delete_person_profile_photo(self, **kwargs):
        if self.fail_mirror:
            raise RuntimeError(
                "Não foi possível sincronizar a remoção da foto com o Portal."
            )
        self.deleted_photos.append(kwargs.get("authorization") or "")


def test_user_profile_core_precedence_over_commercial(tmp_path: Path) -> None:
    repo = InMemoryUserProfileRepo()
    storage = UserProfileStorage(base_dir=str(tmp_path))
    gateway = FakePersonProfileGateway()
    repo.upsert_profile_fields(
        user_id="u1",
        job_title="Local Title",
        phone_e164="+551100000000",
        mobile_e164=None,
        whatsapp_e164=None,
    )
    gateway.profiles["u1"] = {
        "user_id": "u1",
        "job_title": "Core Title",
        "phone_e164": None,
        "mobile_e164": "+5511999999999",
        "whatsapp_e164": None,
        "has_photo": True,
    }
    gateway.photos["u1"] = (b"core-bytes", "image/png", "core.png")
    uc = ManageUserProfileUseCase(
        repository=repo,
        storage=storage,
        directory_gateway=gateway,  # type: ignore[arg-type]
    )
    payload = uc.get_profile(user_id="u1")
    assert payload["job_title"] == "Core Title"
    assert payload["phone_e164"] == "+551100000000"
    assert payload["mobile_e164"] == "+5511999999999"
    assert payload["has_photo"] is True
    photo = uc.get_photo_file(user_id="u1")
    assert photo.content == b"core-bytes"


def test_user_profile_fallback_when_core_empty(tmp_path: Path) -> None:
    repo = InMemoryUserProfileRepo()
    storage = UserProfileStorage(base_dir=str(tmp_path))
    gateway = FakePersonProfileGateway()
    repo.upsert_profile_fields(
        user_id="u1",
        job_title="Local Only",
        phone_e164="+551122223333",
        mobile_e164=None,
        whatsapp_e164=None,
    )
    gateway.profiles["u1"] = {
        "user_id": "u1",
        "job_title": None,
        "phone_e164": None,
        "mobile_e164": None,
        "whatsapp_e164": None,
        "has_photo": False,
    }
    uc = ManageUserProfileUseCase(
        repository=repo,
        storage=storage,
        directory_gateway=gateway,  # type: ignore[arg-type]
    )
    payload = uc.get_profile(user_id="u1")
    assert payload["job_title"] == "Local Only"
    assert payload["phone_e164"] == "+551122223333"


def test_user_profile_fallback_when_core_down(tmp_path: Path) -> None:
    repo = InMemoryUserProfileRepo()
    storage = UserProfileStorage(base_dir=str(tmp_path))

    class DownGateway(FakePersonProfileGateway):
        def get_person_profile(self, user_id: str):
            return None

    repo.upsert_profile_fields(
        user_id="u1",
        job_title="Local",
        phone_e164=None,
        mobile_e164=None,
        whatsapp_e164=None,
    )
    uc = ManageUserProfileUseCase(
        repository=repo,
        storage=storage,
        directory_gateway=DownGateway(),  # type: ignore[arg-type]
    )
    payload = uc.get_profile(user_id="u1")
    assert payload["job_title"] == "Local"


def test_user_profile_dual_write_mirrors_core(tmp_path: Path) -> None:
    repo = InMemoryUserProfileRepo()
    storage = UserProfileStorage(base_dir=str(tmp_path))
    gateway = FakePersonProfileGateway()
    uc = ManageUserProfileUseCase(
        repository=repo,
        storage=storage,
        directory_gateway=gateway,  # type: ignore[arg-type]
    )
    uc.update_profile(
        actor_user_id="u1",
        user_id="u1",
        job_title="Synced",
        phone_e164="+551133334444",
        authorization="Bearer user-token",
    )
    assert len(gateway.mirrored_profiles) == 1
    assert gateway.mirrored_profiles[0]["job_title"] == "Synced"
    assert gateway.mirrored_profiles[0]["authorization"] == "Bearer user-token"

    uc.upload_photo(
        actor_user_id="u1",
        user_id="u1",
        original_name="me.png",
        content=b"\x89PNG\r\n\x1a\n" + b"0" * 20,
        mime_type="image/png",
        authorization="Bearer user-token",
    )
    assert len(gateway.mirrored_photos) == 1

    uc.delete_photo(
        actor_user_id="u1",
        user_id="u1",
        authorization="Bearer user-token",
    )
    assert len(gateway.deleted_photos) == 1


def test_user_profile_dual_write_failure_is_not_silent(tmp_path: Path) -> None:
    repo = InMemoryUserProfileRepo()
    storage = UserProfileStorage(base_dir=str(tmp_path))
    gateway = FakePersonProfileGateway()
    gateway.fail_mirror = True
    uc = ManageUserProfileUseCase(
        repository=repo,
        storage=storage,
        directory_gateway=gateway,  # type: ignore[arg-type]
    )
    with pytest.raises(RuntimeError, match="Portal"):
        uc.update_profile(
            actor_user_id="u1",
            user_id="u1",
            job_title="X",
            authorization="Bearer t",
        )
    assert repo.get("u1") is not None
    assert repo.get("u1").job_title == "X"
