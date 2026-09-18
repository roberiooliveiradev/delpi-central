# app/application/use_cases/list_user_apps_use_case.py

from typing import List, Dict, Any

from app.domain.ports.app_query_port import AppQueryPort
from app.application.services.app_authorization_service import (
    AppAuthorizationService,
)


def _serialize_routes(app) -> list[dict[str, Any]]:
    return [
        {
            "app": app.id,
            "app_name": app.name,
            "app_icon": app.icon,
            "path": route.path,
            "permission": route.permission_code,
            "label": route.label,
            "icon": route.icon,
            "showInMenu": route.show_in_menu,
            "order": route.order,
            "entry": route.entry,
            "openInNewTab": route.open_in_new_tab,
        }
        for route in app.routes
    ]


class ListUserAppsUseCase:
    """
    Lista apps que o usuário pode abrir.

    ``routes`` fica só com o que ele pode abrir (menu e chat).
    ``authorizationRoutes`` é o catálogo da app, para o guard negar
    a rota mais específica. Sem isso, o prefixo autorizado libera
    ``/administration``.
    """

    def __init__(self, app_query: AppQueryPort):
        self.app_query = app_query
        self._auth_service = AppAuthorizationService()

    def execute(
        self,
        permissions: list[str],
        is_superadmin: bool,
    ) -> List[Dict[str, Any]]:

        apps = self.app_query.list_active_apps_with_routes()
        catalog_by_id = {app.id: app for app in apps}

        authorized_apps = self._auth_service.filter_apps(
            apps=apps,
            permissions=permissions,
            is_superadmin=is_superadmin,
        )

        result: List[Dict[str, Any]] = []

        for app in authorized_apps:
            catalog = catalog_by_id.get(app.id, app)
            result.append(
                {
                    "id": app.id,
                    "name": app.name,
                    "basePath": app.base_path,
                    "icon": app.icon,
                    "type": app.type,
                    "entryUrl": app.entry_url,
                    "renderMode": app.render_mode,
                    "routes": _serialize_routes(app),
                    "authorizationRoutes": _serialize_routes(catalog),
                }
            )

        return result