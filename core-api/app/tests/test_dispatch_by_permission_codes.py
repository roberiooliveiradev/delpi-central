from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.use_cases.dispatch_notifications_use_case import DispatchNotificationsUseCase
from app.domain.ports.user_repository_port import UserDTO


def test_dispatch_resolves_permission_codes_and_exclusions():
    approver_id = str(uuid4())
    requester_id = str(uuid4())
    permission_code = "central-agendamento.approve.filial-es"

    uow = MagicMock()
    uow.notifications.create.return_value = uuid4()
    uow.notification_preferences.filter_user_ids_accepting_category.side_effect = (
        lambda user_ids, _category: user_ids
    )
    uow.rbac_queries.list_user_ids_by_permission_code.return_value = [
        approver_id,
        requester_id,
    ]

    def get_by_id(user_id):
        return UserDTO(
            id=user_id,
            email=f"{user_id}@test.com",
            name="User",
            active=True,
            is_superadmin=False,
            last_login_at=None,
        )

    uow.users.get_by_id.side_effect = get_by_id

    with patch(
        "app.application.use_cases.dispatch_notifications_use_case.filter_user_ids_with_app_access",
        side_effect=lambda _uow, user_ids, **_kwargs: user_ids,
    ):
        result = DispatchNotificationsUseCase(uow).execute(
            DispatchNotificationsRequest(
                title="Hi",
                message="Body",
                type="warning",
                category="central_agendamento",
                presentation="text",
                html_content=None,
                action_type="portal_route",
                action_label="Abrir",
                action_target="/apps/central-agendamento/filial-es",
                icon=None,
                metadata=None,
                expires_at=None,
                broadcast=False,
                user_ids=[],
                emails=[],
                role_ids=[],
                group_ids=[],
                permission_codes=[permission_code],
                excluded_user_ids=[requester_id],
                source_app="central-agendamento",
            )
        )

    assert result.created_count == 1
    uow.rbac_queries.list_user_ids_by_permission_code.assert_called_once_with(
        permission_code
    )
