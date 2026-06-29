from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.directory_user_eligibility_service import (
    DirectoryUserEligibilityService,
)
from app.application.use_cases.search_directory_users_use_case import (
    SearchDirectoryUsersUseCase,
)
from app.domain.ports.app_query_port import AppDTO, RouteDTO
from app.domain.ports.user_repository_port import UserDTO


def _user(user_id, name="User", email="user@delpi.com", *, active=True, superadmin=False):
    return UserDTO(
        id=user_id,
        email=email,
        name=name,
        active=active,
        is_superadmin=superadmin,
        last_login_at=None,
    )


def test_search_directory_users_browse_lists_without_query():
    user_id = uuid4()
    users = [_user(user_id, name="Ana", email="ana@delpi.com")]

    uow = MagicMock()
    uow.users.list_paginated.return_value = (users, 1)

    result = SearchDirectoryUsersUseCase(uow).execute(query="", browse=True)

    assert len(result) == 1
    uow.users.list_paginated.assert_called_once()
    assert uow.users.list_paginated.call_args.kwargs["q"] is None


def test_search_directory_users_excludes_current_user():
    current_id = uuid4()
    other_id = uuid4()
    users = [
        _user(current_id, name="Eu", email="me@delpi.com"),
        _user(other_id, name="Outro", email="outro@delpi.com"),
    ]

    uow = MagicMock()
    uow.users.list_paginated.return_value = (users, 2)

    result = SearchDirectoryUsersUseCase(uow).execute(
        query="delpi",
        exclude_user_id=str(current_id),
    )

    assert len(result) == 1
    assert result[0]["id"] == str(other_id)


def test_search_directory_users_filters_by_app_access():
    current_id = uuid4()
    allowed_id = uuid4()
    denied_id = uuid4()

    pac_app = AppDTO(
        id="quality-action-plans",
        name="PAC",
        base_path="/apps/quality-action-plans",
        icon=None,
        type="microfrontend",
        entry_url=None,
        render_mode="federated",
        routes=[
            RouteDTO(
                path="/apps/quality-action-plans",
                permission_code="quality-action-plans.read",
                label="PAC",
                icon=None,
                show_in_menu=True,
                order=1,
                entry=None,
            )
        ],
    )

    users = [
        _user(allowed_id, name="Com PAC", email="com@delpi.com"),
        _user(denied_id, name="Sem PAC", email="sem@delpi.com"),
    ]

    uow = MagicMock()
    uow.users.list_paginated.return_value = (users, 2)
    uow.app_queries.list_active_apps_with_routes.return_value = [pac_app]
    uow.cache = None

    def resolve_permissions(user_id, is_superadmin):
        if user_id == allowed_id:
            return ["quality-action-plans.read"]
        return ["dashboard-quality.view"]

    uow.permission_queries.list_direct_role_permissions.side_effect = (
        lambda uid: resolve_permissions(uid, False)
    )
    uow.permission_queries.list_group_role_permissions.return_value = []
    uow.permission_queries.list_user_overrides.return_value = []

    result = SearchDirectoryUsersUseCase(uow).execute(
        query="delpi",
        app_id="quality-action-plans",
        exclude_user_id=str(current_id),
    )

    assert len(result) == 1
    assert result[0]["id"] == str(allowed_id)


def test_search_directory_users_can_return_full_email_for_integrations():
    user_id = uuid4()
    users = [_user(user_id, name="Ana", email="ana@delpi.com")]

    uow = MagicMock()
    uow.users.list_paginated.return_value = (users, 1)

    result = SearchDirectoryUsersUseCase(uow).execute(
        query="ana",
        browse=False,
        mask_email=False,
    )

    assert result[0]["email"] == "ana@delpi.com"


def test_directory_user_eligibility_matches_permission_code():
    user_id = uuid4()
    user = _user(user_id)

    uow = MagicMock()
    uow.cache = None
    uow.permission_queries.list_direct_role_permissions.return_value = [
        "quality-action-plans.read"
    ]
    uow.permission_queries.list_group_role_permissions.return_value = []
    uow.permission_queries.list_user_overrides.return_value = []

    service = DirectoryUserEligibilityService(uow)

    assert service.matches(user, permission_code="quality-action-plans.read") is True
    assert service.matches(user, permission_code="quality-action-plans.admin") is False
