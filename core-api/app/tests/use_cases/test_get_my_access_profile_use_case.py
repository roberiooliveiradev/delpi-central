from uuid import uuid4
from unittest.mock import MagicMock

from app.application.use_cases.get_my_access_profile_use_case import (
    GetMyAccessProfileUseCase,
)


def test_execute_merges_direct_and_group_roles():
    user_id = uuid4()
    role_id = uuid4()
    group_id = uuid4()

    role = MagicMock()
    role.id = role_id
    role.name = "Chat Full"
    role.description = "Chat completo"

    group = MagicMock()
    group.id = group_id
    group.name = "Equipe Chat"
    group.description = None

    permission = MagicMock()
    permission.code = "minha-delpi.chat.access"
    permission.name = "Acessar chat"
    permission.description = "Usar o chat"
    permission.module = "minha-delpi"

    uow = MagicMock()
    uow.user_roles.list_role_ids.return_value = [role_id]
    uow.user_groups.list_group_ids.return_value = [group_id]
    uow.group_roles.list_role_ids.return_value = [role_id]
    uow.roles.get.return_value = role
    uow.groups.get.return_value = group
    uow.permission_queries.list_permissions_by_role_id.return_value = [permission]
    uow.app_queries.list_active_apps_with_routes.return_value = []
    uow.cache = None
    uow.permission_queries.list_all_permission_codes.return_value = []
    uow.permission_queries.list_direct_role_permissions.return_value = [
        "minha-delpi.chat.access"
    ]
    uow.permission_queries.list_group_role_permissions.return_value = []
    uow.permission_queries.list_user_overrides.return_value = []

    result = GetMyAccessProfileUseCase(uow).execute(user_id, is_superadmin=False)

    assert len(result["roles"]) == 1
    assert result["roles"][0]["name"] == "Chat Full"
    assert len(result["roles"][0]["permissions"]) == 1
    assert result["roles"][0]["permissions"][0]["code"] == "minha-delpi.chat.access"
    assert len(result["roles"][0]["sources"]) == 2
    assert result["groups"][0]["name"] == "Equipe Chat"
