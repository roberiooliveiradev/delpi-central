from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from commercial_app.application.services.user_profile_storage import UserProfileStorage
from commercial_app.application.use_cases.manage_user_profile import ManageUserProfileUseCase
from commercial_app.domain.entities.seller_portfolio import SellerPortfolio
from commercial_app.domain.entities.user_profile import CommercialUserProfile


class InMemoryUserProfileRepo:
    def __init__(self) -> None:
        self.items: dict[str, CommercialUserProfile] = {}

    def get(self, user_id: str) -> CommercialUserProfile | None:
        return self.items.get(user_id)

    def upsert_job_title(self, *, user_id: str, job_title: str | None) -> CommercialUserProfile:
        now = datetime.now(timezone.utc)
        current = self.items.get(user_id)
        profile = CommercialUserProfile(
            user_id=user_id,
            job_title=job_title,
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
