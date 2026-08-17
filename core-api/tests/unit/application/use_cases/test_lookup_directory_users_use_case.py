from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.application.use_cases.lookup_directory_users_use_case import (
    LookupDirectoryUsersUseCase,
)
from app.domain.ports.user_repository_port import UserDTO


def test_lookup_directory_users_returns_active_profiles():
    user_id = uuid4()
    uow = MagicMock()
    uow.users.get_by_ids.return_value = [
        UserDTO(
            id=user_id,
            email="user@delpi.com",
            name="Usuário",
            active=True,
            is_superadmin=False,
            last_login_at=None,
        )
    ]

    result = LookupDirectoryUsersUseCase(uow).execute(user_ids=[str(user_id)])

    assert len(result) == 1
    assert result[0]["email"] == "u***@delpi.com"
    assert "has_app_access" not in result[0]


def test_lookup_directory_users_includes_has_app_access_when_app_set():
    user_id = uuid4()
    uow = MagicMock()
    user = UserDTO(
        id=user_id,
        email="user@delpi.com",
        name="Usuário",
        active=True,
        is_superadmin=False,
        last_login_at=None,
    )
    uow.users.get_by_ids.return_value = [user]

    with patch(
        "app.application.use_cases.lookup_directory_users_use_case.DirectoryUserEligibilityService"
    ) as eligibility_cls:
        eligibility = eligibility_cls.return_value
        eligibility.matches.return_value = False
        result = LookupDirectoryUsersUseCase(uow).execute(
            user_ids=[str(user_id)],
            app_id="commercial",
        )

    assert len(result) == 1
    assert result[0]["has_app_access"] is False
    eligibility.matches.assert_called_once_with(user, app_id="commercial")
