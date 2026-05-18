# app/tests/test_dispatch_by_role_group.py

from unittest.mock import MagicMock
from uuid import uuid4

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.use_cases.dispatch_notifications_use_case import DispatchNotificationsUseCase
from app.domain.ports.user_repository_port import UserDTO


def test_dispatch_resolves_role_and_group_ids():
    role_id = str(uuid4())
    group_id = str(uuid4())
    user_from_role = str(uuid4())
    user_from_group = str(uuid4())

    uow = MagicMock()
    uow.notifications.create.return_value = uuid4()
    uow.notification_preferences.filter_user_ids_accepting_category.side_effect = (
        lambda user_ids, _category: user_ids
    )
    uow.rbac_queries.list_user_ids_by_role.return_value = [user_from_role]
    uow.rbac_queries.list_user_ids_by_group_role.return_value = []
    uow.rbac_queries.list_user_ids_by_group.return_value = [user_from_group]

    active_user = UserDTO(
        id=uuid4(),
        email="a@test.com",
        name="A",
        active=True,
        is_superadmin=False,
        last_login_at=None,
    )

    def get_by_id(user_id):
        uid = str(user_id)
        if uid in {user_from_role, user_from_group}:
            return UserDTO(
                id=user_id,
                email=f"{uid}@test.com",
                name="User",
                active=True,
                is_superadmin=False,
                last_login_at=None,
            )
        return active_user

    uow.users.get_by_id.side_effect = get_by_id

    result = DispatchNotificationsUseCase(uow).execute(
        DispatchNotificationsRequest(
            title="Hi",
            message="Body",
            type="info",
            category="announcement",
            presentation="text",
            html_content=None,
            action_type=None,
            action_label=None,
            action_target=None,
            icon=None,
            metadata=None,
            expires_at=None,
            broadcast=False,
            user_ids=[],
            emails=[],
            role_ids=[role_id],
            group_ids=[group_id],
        )
    )

    assert result.created_count == 2
    assert uow.notifications.create.call_count == 2
