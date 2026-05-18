# app/domain/notifications/notification_recipient_vars.py

from __future__ import annotations

from app.domain.notifications.notification_templates import NotificationTemplateSpec
from app.domain.ports.user_repository_port import UserDTO


def resolve_user_display_name(user: UserDTO) -> str:
    name = (user.name or "").strip()
    if name:
        return name.split()[0]

    email = (user.email or "").strip().lower()
    if "@" in email:
        local = email.split("@", 1)[0].replace(".", " ")
        token = local.split()[0] if local.split() else local
        if token:
            return token[:1].upper() + token[1:]

    return "colaborador"


def resolve_user_full_name(user: UserDTO) -> str:
    name = (user.name or "").strip()
    if name:
        return name
    return resolve_user_display_name(user)


def build_recipient_template_vars(
    user: UserDTO,
    spec: NotificationTemplateSpec | None = None,
    *,
    include_keys: frozenset[str] | set[str] | None = None,
) -> dict[str, str]:
    keys = include_keys
    if keys is None and spec is not None:
        keys = set(spec.recipient_vars)
    if not keys:
        keys = {"userName", "userFullName", "userEmail"}

    result: dict[str, str] = {}

    if "userName" in keys:
        result["userName"] = resolve_user_display_name(user)
    if "userFullName" in keys:
        result["userFullName"] = resolve_user_full_name(user)
    if "userEmail" in keys:
        result["userEmail"] = (user.email or "").strip().lower()

    return result


def template_requires_per_recipient_render(spec: NotificationTemplateSpec | None) -> bool:
    return bool(spec and spec.recipient_vars)
