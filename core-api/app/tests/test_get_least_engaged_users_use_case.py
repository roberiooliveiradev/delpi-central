# app/tests/test_get_least_engaged_users_use_case.py

from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.application.use_cases.admin.get_least_engaged_users_use_case import (
    GetLeastEngagedUsersUseCase,
)
from app.domain.ports.app_query_port import AppDTO, RouteDTO


def test_execute_enriches_candidates_with_available_apps():
    user_id = uuid4()
    uow = MagicMock()

    use_case = GetLeastEngagedUsersUseCase(uow)
    use_case.usage_repo = MagicMock()
    use_case.usage_repo.list_least_engaged_users.return_value = [
        {
            "id": user_id,
            "name": "Usuário Teste",
            "email": "teste@delpi.com.br",
            "is_superadmin": False,
            "apps_used": 0,
            "total_opens": 0,
            "last_app_usage_at": None,
            "last_login_at": None,
        }
    ]

    uow.app_queries.list_active_apps_with_routes.return_value = [
        AppDTO(
            id="dashboard-rh",
            name="Portal RH",
            base_path="/portal-rh",
            icon=None,
            type="iframe",
            entry_url="http://example",
            render_mode="embedded",
            routes=[
                RouteDTO(
                    path="/portal-rh",
                    label="RH",
                    icon=None,
                    permission_code="portal-rh.access",
                    show_in_menu=True,
                    order=1,
                    entry=None,
                )
            ],
        ),
        AppDTO(
            id="api-delpi",
            name="API DELPI",
            base_path="/apps/api-delpi",
            icon=None,
            type="backend-only",
            entry_url=None,
            render_mode=None,
            routes=[],
        ),
    ]
    uow.permission_queries = MagicMock()
    uow.cache = None
    uow.user_roles = MagicMock()
    uow.user_roles.list_role_ids.return_value = []
    uow.user_groups = MagicMock()
    uow.user_groups.list_group_ids.return_value = []
    uow.group_roles = MagicMock()
    uow.roles = MagicMock()
    uow.roles.list_all.return_value = []

    with patch(
        "app.application.use_cases.admin.get_least_engaged_users_use_case.PermissionResolver"
    ) as resolver_cls:
        resolver_cls.return_value.resolve.return_value = ["portal-rh.access"]

        result = use_case.execute(history_days=30, limit=5)

    assert result["periodDays"] == 30
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["email"] == "teste@delpi.com.br"
    assert item["appsUsedInPeriod"] == 0
    assert item["availableAppsCount"] == 1
    assert item["availableApps"] == [{"id": "dashboard-rh", "name": "Portal RH"}]
    assert item["availableGroupsCount"] == 0
    assert item["availableGroups"] == []
    assert item["availableRolesCount"] == 0
    assert item["availableRoles"] == []


def test_execute_includes_direct_roles_and_groups():
    user_id = uuid4()
    role_id = uuid4()
    group_id = uuid4()
    uow = MagicMock()

    use_case = GetLeastEngagedUsersUseCase(uow)
    use_case.usage_repo = MagicMock()
    use_case.usage_repo.list_least_engaged_users.return_value = [
        {
            "id": user_id,
            "name": "Usuário Teste",
            "email": "teste@delpi.com.br",
            "is_superadmin": False,
            "apps_used": 1,
            "total_opens": 2,
            "last_app_usage_at": None,
            "last_login_at": None,
        }
    ]

    uow.app_queries.list_active_apps_with_routes.return_value = []
    uow.permission_queries = MagicMock()
    uow.cache = None
    uow.user_roles = MagicMock()
    uow.user_roles.list_role_ids.return_value = [role_id]
    uow.user_groups = MagicMock()
    uow.user_groups.list_group_ids.return_value = [group_id]
    uow.group_roles = MagicMock()
    uow.group_roles.list_role_ids.return_value = []
    uow.roles = MagicMock()
    uow.roles.get.side_effect = lambda rid: MagicMock(
        id=rid,
        name="Papel RH" if rid == role_id else "Papel Grupo",
    )
    uow.groups = MagicMock()
    uow.groups.get.return_value = MagicMock(id=group_id, name="Engenharia")
    uow.roles.list_all.return_value = []

    with patch(
        "app.application.use_cases.admin.get_least_engaged_users_use_case.PermissionResolver"
    ) as resolver_cls:
        resolver_cls.return_value.resolve.return_value = []

        result = use_case.execute(history_days=30, limit=5)

    item = result["items"][0]
    assert item["availableRoles"] == [{"id": str(role_id), "name": "Papel RH"}]
    assert item["availableGroups"] == [{"id": str(group_id), "name": "Engenharia"}]
