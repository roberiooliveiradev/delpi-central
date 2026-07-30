from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

from app.application.use_cases.lookup_directory_users_use_case import (
    LookupDirectoryUsersUseCase,
)


def test_lookup_masks_email_by_default():
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    uow = MagicMock()
    uow.users.get_by_ids.return_value = [
        SimpleNamespace(id=user_id, name="Ana", email="ana.silva@delpi.com.br", active=True)
    ]

    items = LookupDirectoryUsersUseCase(uow).execute(user_ids=[str(user_id)])

    assert items == [
        {
            "id": str(user_id),
            "name": "Ana",
            "email": "a***@delpi.com.br",
        }
    ]


def test_lookup_reveals_email_when_requested():
    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    uow = MagicMock()
    uow.users.get_by_ids.return_value = [
        SimpleNamespace(id=user_id, name="Ana", email="ana.silva@delpi.com.br", active=True)
    ]

    items = LookupDirectoryUsersUseCase(uow).execute(
        user_ids=[str(user_id)],
        mask_email=False,
    )

    assert items[0]["email"] == "ana.silva@delpi.com.br"
