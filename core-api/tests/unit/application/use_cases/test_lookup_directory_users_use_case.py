from unittest.mock import MagicMock
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
