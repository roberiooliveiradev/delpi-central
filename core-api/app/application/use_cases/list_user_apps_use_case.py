# app/application/use_cases/list_user_apps_use_case.py


from typing import List, Dict

from app.domain.ports.app_query_port import AppQueryPort
from app.domain.services.permission_resolver import PermissionResolver


class ListUserAppsUseCase:

    def __init__(
        self,
        app_query: AppQueryPort,
        permission_resolver: PermissionResolver,
    ):
        self.app_query = app_query
        self.permission_resolver = permission_resolver

    def execute(self, user_id, is_superadmin: bool) -> List[Dict]:

        permissions = self.permission_resolver.resolve(
            user_id=user_id,
            is_superadmin=is_superadmin,
        )

        apps = self.app_query.list_active_apps_with_routes()

        result = []

        for app in apps:

            filtered_routes = []

            for route in app.routes:

                # rota pública
                if route.permission_code is None:
                    filtered_routes.append(route)
                    continue

                if route.permission_code in permissions:
                    filtered_routes.append(route)

            if filtered_routes:
                result.append({
                    "id": app.id,
                    "name": app.name,
                    "basePath": app.base_path,
                    "icon": app.icon,
                    "type": app.type,
                    "entryUrl": app.entry_url,
                    "routes": [
                        {
                            "path": r.path,
                            "label": r.label,
                            "icon": r.icon,
                            "showInMenu": r.show_in_menu,
                            "order": r.order,
                        }
                        for r in filtered_routes
                    ]
                })

        return result