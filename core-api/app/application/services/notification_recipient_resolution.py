# app/application/services/notification_recipient_resolution.py

from uuid import UUID

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.use_cases.dispatch_notifications_use_case import (
    DispatchNotificationsValidationError,
)
from app.application.unit_of_work import UnitOfWork


def resolve_notification_recipient_ids(
    uow: UnitOfWork,
    request: DispatchNotificationsRequest,
) -> list[str]:
    if request.broadcast:
        resolved = _list_active_user_ids(uow)
    else:
        resolved_set: set[str] = set()

        for raw_user_id in request.user_ids:
            user_id = _normalize_user_id(raw_user_id)
            user = uow.users.get_by_id(UUID(user_id))
            if not user or not user.active:
                raise DispatchNotificationsValidationError(
                    f"user not found or inactive: {raw_user_id}"
                )
            resolved_set.add(user_id)

        for email in request.emails:
            normalized_email = (email or "").strip().lower()
            if not normalized_email:
                continue

            user = uow.users.get_by_email(normalized_email)
            if not user or not user.active:
                raise DispatchNotificationsValidationError(
                    f"user not found or inactive for email: {normalized_email}"
                )
            resolved_set.add(str(user.id))

        for raw_role_id in request.role_ids:
            role_id = _normalize_user_id(raw_role_id)
            resolved_set.update(uow.rbac_queries.list_user_ids_by_role(UUID(role_id)))
            resolved_set.update(
                uow.rbac_queries.list_user_ids_by_group_role(UUID(role_id))
            )

        for raw_group_id in request.group_ids:
            group_id = _normalize_user_id(raw_group_id)
            resolved_set.update(uow.rbac_queries.list_user_ids_by_group(UUID(group_id)))

        resolved = _filter_active_user_ids(uow, resolved_set)

    excluded = {_normalize_user_id(item) for item in request.excluded_user_ids if item}
    if excluded:
        resolved = [user_id for user_id in resolved if user_id not in excluded]

    return sorted(resolved)


def resolve_notification_recipient_users(
    uow: UnitOfWork,
    request: DispatchNotificationsRequest,
) -> list[dict]:
    user_ids = resolve_notification_recipient_ids(uow, request)
    items: list[dict] = []

    for user_id in user_ids:
        user = uow.users.get_by_id(UUID(user_id))
        if not user or not user.active:
            continue
        items.append(
            {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
            }
        )

    return items


def _list_active_user_ids(uow: UnitOfWork) -> list[str]:
    return sorted(
        str(user.id) for user in uow.users.list_all() if user.active
    )


def _filter_active_user_ids(uow: UnitOfWork, user_ids: set[str]) -> list[str]:
    active: list[str] = []
    for user_id in user_ids:
        user = uow.users.get_by_id(UUID(user_id))
        if user and user.active:
            active.append(user_id)
    return sorted(active)


def _normalize_user_id(raw_user_id: str) -> str:
    return str(UUID(str(raw_user_id).strip()))
