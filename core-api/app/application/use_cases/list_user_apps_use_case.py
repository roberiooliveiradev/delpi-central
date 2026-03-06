# app/application/use_cases/list_user_apps_use_case.py

from typing import List, Dict, Any

from app.domain.ports.app_query_port import AppQueryPort
from app.application.services.app_authorization_service import (
    AppAuthorizationService,
)


class ListUserAppsUseCase:
    """
    Caso de uso responsável por listar aplicações disponíveis
    para o usuário atual, já com rotas autorizadas embutidas.
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

        authorized_apps = self._auth_service.filter_apps(
            apps=apps,
            permissions=permissions,
            is_superadmin=is_superadmin,
        )

        result: List[Dict[str, Any]] = []

        for app in authorized_apps:
            result.append(
                {
                    "id": app.id,
                    "name": app.name,
                    "basePath": app.base_path,
                    "icon": app.icon,
                    "type": app.type,
                    "entryUrl": app.entry_url,
                    "renderMode": app.render_mode,
                    "routes": [
                        {
                            "app": app.id,
                            "app_name": app.name,
                            "app_icon": app.icon,
                            "path": r.path,
                            "permission": r.permission_code,
                            "label": r.label,
                            "icon": r.icon,
                            "showInMenu": r.show_in_menu,
                            "order": r.order,
                            "entry": r.entry,
                        }
                        for r in app.routes
                    ],
                }
            )

        return result