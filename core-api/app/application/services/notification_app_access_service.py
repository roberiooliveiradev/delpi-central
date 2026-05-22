# app/application/services/notification_app_access_service.py

from __future__ import annotations

from uuid import UUID

from app.application.services.app_authorization_service import AppAuthorizationService
from app.application.unit_of_work import UnitOfWork
from app.domain.services.permission_resolver import PermissionResolver

# sourceApp lógico (integrações) → id do plugin no portal
_SOURCE_APP_PLUGIN_ALIASES: dict[str, str] = {
    "controle_mp": "controle-mp",
    "transformometro": "transformometro",
}


def resolve_notification_app_id(
    uow: UnitOfWork,
    *,
    source_app: str | None,
    action_target: str | None,
    metadata: dict | None,
) -> str | None:
    """
    Identifica o plugin/app do portal associado à notificação.
    Retorna None quando não há vínculo com app (notificações globais do sistema).
    """
    apps = uow.app_queries.list_active_apps_with_routes()
    if not apps:
        return None

    app_ids = {app.id for app in apps}

    candidates: list[str] = []

    for raw in (
        source_app,
        (metadata or {}).get("source") if isinstance(metadata, dict) else None,
        (metadata or {}).get("sourceApp") if isinstance(metadata, dict) else None,
    ):
        if not raw or not isinstance(raw, str):
            continue
        key = raw.strip().lower()
        if not key:
            continue
        candidates.append(key)
        candidates.append(key.replace("_", "-"))
        mapped = _SOURCE_APP_PLUGIN_ALIASES.get(key)
        if mapped:
            candidates.append(mapped)

    for candidate in candidates:
        if candidate in app_ids:
            return candidate

    if action_target and isinstance(action_target, str):
        path = action_target.strip().rstrip("/") or "/"
        for app in apps:
            base = (app.base_path or "/").rstrip("/") or "/"
            if path == base or path.startswith(f"{base}/"):
                return app.id

    return None


def filter_user_ids_with_app_access(
    uow: UnitOfWork,
    user_ids: list[str],
    *,
    source_app: str | None,
    action_target: str | None,
    metadata: dict | None,
) -> list[str]:
    """
    Remove destinatários que não possuem permissão para abrir o app de origem
    (mesma regra de GET /me/apps).
    """
    app_id = resolve_notification_app_id(
        uow,
        source_app=source_app,
        action_target=action_target,
        metadata=metadata,
    )
    if not app_id:
        return user_ids

    apps = uow.app_queries.list_active_apps_with_routes()
    target_app = next((app for app in apps if app.id == app_id), None)
    if target_app is None:
        return []

    auth_service = AppAuthorizationService()
    resolver = PermissionResolver(uow.permission_queries, uow.cache)

    allowed: list[str] = []

    for raw_user_id in user_ids:
        try:
            user_uuid = UUID(str(raw_user_id).strip())
        except (TypeError, ValueError):
            continue

        user = uow.users.get_by_id(user_uuid)
        if not user or not user.active:
            continue

        permissions = resolver.resolve(user.id, bool(user.is_superadmin))
        authorized_ids = auth_service.filter_app_ids(
            [target_app],
            permissions,
            bool(user.is_superadmin),
        )

        if app_id in authorized_ids:
            allowed.append(str(user.id))

    return allowed
