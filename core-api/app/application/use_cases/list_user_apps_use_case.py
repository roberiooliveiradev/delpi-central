# app/application/use_cases/list_user_apps_use_case.py

from typing import List, Dict

from app.domain.ports.app_query_port import AppQueryPort
from app.application.services.app_authorization_service import (
    AppAuthorizationService,
)


class ListUserAppsUseCase:
    """
    Caso de uso responsável por listar aplicações disponíveis
    para o usuário atual.
    """

    def __init__(self, app_query: AppQueryPort):
        self.app_query = app_query
        self._auth_service = AppAuthorizationService()

    def execute(
        self,
        permissions: list[str],
        is_superadmin: bool,
    ) -> List[Dict]:

        apps = self.app_query.list_active_apps_with_routes()

        authorized_apps = self._auth_service.filter_apps(
            apps=apps,
            permissions=permissions,
            is_superadmin=is_superadmin,
        )

        result: List[Dict] = []

        for app in authorized_apps:
            result.append({
                "id": app.id,
                "name": app.name,
                "basePath": app.base_path,
                "icon": app.icon,
                "type": app.type,
                "entryUrl": app.entry_url,
                "renderMode": app.render_mode,
                "routes": [
                    {
                        "path": r.path,
                        "label": r.label,
                        "icon": r.icon,
                        "showInMenu": r.show_in_menu,
                        "order": r.order,
                    }
                    for r in app.routes
                ],
            })

        return result