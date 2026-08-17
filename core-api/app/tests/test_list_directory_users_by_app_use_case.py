# app/tests/test_list_directory_users_by_app_use_case.py
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.application.use_cases.list_directory_users_by_app_use_case import (
    ListDirectoryUsersByAppUseCase,
)


def _user(name: str, *, active: bool = True):
    return SimpleNamespace(
        id=uuid4(),
        name=name,
        email=f"{name.lower().replace(' ', '.')}@delpi.com",
        active=active,
    )


def test_list_by_app_pages_matching_users_beyond_typeahead_cap():
    users = [_user(name) for name in ("Ana", "Bruno", "Carla", "Diego", "Elena")]
    matching_ids = {users[0].id, users[2].id, users[4].id}  # Ana, Carla, Elena

    uow = MagicMock()

    def matches(user, *, app_id=None, permission_code=None):
        _ = app_id, permission_code
        return user.id in matching_ids

    with patch.object(ListDirectoryUsersByAppUseCase, "SCAN_PAGE_SIZE", 2):
        uow.users.list_paginated.side_effect = [
            (users[0:2], 5),
            (users[2:4], 5),
            (users[4:5], 5),
        ]
        with patch(
            "app.application.use_cases.list_directory_users_by_app_use_case.DirectoryUserEligibilityService"
        ) as svc_cls:
            svc_cls.return_value.matches.side_effect = matches
            page1 = ListDirectoryUsersByAppUseCase(uow).execute(
                app_id="commercial",
                page=1,
                page_size=2,
                mask_email=False,
            )

    assert page1["total"] == 3
    assert page1["hasMore"] is True
    assert [item["name"] for item in page1["items"]] == ["Ana", "Carla"]
    assert uow.users.list_paginated.call_count == 3

    with patch.object(ListDirectoryUsersByAppUseCase, "SCAN_PAGE_SIZE", 2):
        uow.users.list_paginated.reset_mock()
        uow.users.list_paginated.side_effect = [
            (users[0:2], 5),
            (users[2:4], 5),
            (users[4:5], 5),
        ]
        with patch(
            "app.application.use_cases.list_directory_users_by_app_use_case.DirectoryUserEligibilityService"
        ) as svc_cls:
            svc_cls.return_value.matches.side_effect = matches
            page2 = ListDirectoryUsersByAppUseCase(uow).execute(
                app_id="commercial",
                page=2,
                page_size=2,
                mask_email=False,
            )

    assert [item["name"] for item in page2["items"]] == ["Elena"]
    assert page2["hasMore"] is False


def test_list_by_app_requires_app_id():
    with pytest.raises(ValueError, match="app is required"):
        ListDirectoryUsersByAppUseCase(MagicMock()).execute(app_id="  ")
