from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.search_directory_users_use_case import (
    SearchDirectoryUsersUseCase,
)
from app.domain.ports.user_repository_port import UserDTO


def test_search_directory_users_excludes_current_user():
    current_id = uuid4()
    other_id = uuid4()
    users = [
        UserDTO(
            id=current_id,
            email="me@delpi.com",
            name="Eu",
            active=True,
            is_superadmin=False,
            last_login_at=None,
        ),
        UserDTO(
            id=other_id,
            email="outro@delpi.com",
            name="Outro",
            active=True,
            is_superadmin=False,
            last_login_at=None,
        ),
    ]

    uow = MagicMock()
    uow.users.list_paginated.return_value = (users, 2)

    result = SearchDirectoryUsersUseCase(uow).execute(
        current_user_id=str(current_id),
        query="delpi",
    )

    assert len(result) == 1
    assert result[0]["id"] == str(other_id)
