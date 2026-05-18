# app/application/use_cases/notify_user_use_case.py

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.dto.dispatch_notifications_response import DispatchNotificationsResponse
from app.application.use_cases.dispatch_notifications_use_case import DispatchNotificationsUseCase
from app.application.unit_of_work import UnitOfWork


class NotifyUserUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self._dispatch = DispatchNotificationsUseCase(uow)

    def execute(
        self,
        user_id: str,
        title: str | None,
        message: str,
        type: str = "info",
    ) -> DispatchNotificationsResponse:
        return self._dispatch.execute(
            DispatchNotificationsRequest(
                title=title,
                message=message,
                type=type,
                category="system",
                presentation="text",
                html_content=None,
                action_type=None,
                action_label=None,
                action_target=None,
                icon=None,
                metadata=None,
                expires_at=None,
                broadcast=False,
                user_ids=[user_id],
                emails=[],
                role_ids=[],
                group_ids=[],
                source_app="core-api",
            )
        )
