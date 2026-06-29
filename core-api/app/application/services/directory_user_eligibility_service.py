from __future__ import annotations

from app.application.services.app_authorization_service import AppAuthorizationService
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.user_repository_port import UserDTO
from app.domain.services.permission_resolver import PermissionResolver


class DirectoryUserEligibilityService:
    """Filtra usuários do diretório por permissão ou acesso a app (mesma regra de /me/apps)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._resolver = PermissionResolver(uow.permission_queries, uow.cache)
        self._auth = AppAuthorizationService()

    def matches(
        self,
        user: UserDTO,
        *,
        app_id: str | None = None,
        permission_code: str | None = None,
    ) -> bool:
        if not user.active:
            return False

        is_superadmin = bool(user.is_superadmin)
        permissions = self._resolver.resolve(user.id, is_superadmin)

        if permission_code and permission_code not in permissions and not is_superadmin:
            return False

        if app_id:
            apps = self._uow.app_queries.list_active_apps_with_routes()
            target_app = next((app for app in apps if app.id == app_id), None)
            if target_app is None:
                return False
            authorized_ids = self._auth.filter_app_ids(
                [target_app],
                permissions,
                is_superadmin,
            )
            if app_id not in authorized_ids:
                return False

        return True
