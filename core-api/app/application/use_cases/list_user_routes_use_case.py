# app/application/use_cases/list_user_routes_use_case.py

from app.domain.ports.route_query_port import RouteQueryPort
from typing import List, Dict


class ListUserRoutesUseCase:

    def __init__(self, route_queries: RouteQueryPort):
        self.route_queries = route_queries

    def execute(
        self,
        permissions: List[str],
        is_superadmin: bool,
    ) -> List[Dict]:

        routes = self.route_queries.list_active_menu_routes()

        allowed = []

        for route in routes:

            permission_code = None

            # rota pública
            if route.permission is None:
                allowed.append({
                    "app": route.app.id,
                    "app_name": route.app.name,
                    "app_icon": route.app.icon,
                    "path": route.path,
                    "permission": None,
                    "icon": route.icon,
                    "label": route.label,
                })
                continue

            permission_code = route.permission.code

            # superadmin bypass
            if is_superadmin:
                allowed.append({
                    "app": route.app.id,
                    "app_name": route.app.name,
                    "app_icon": route.app.icon,
                    "path": route.path,
                    "permission": permission_code,
                    "icon": route.icon,
                    "label": route.label,
                })
                continue

            if permission_code not in permissions:
                continue

            allowed.append({
                "app": route.app.id,
                "app_name": route.app.name,
                "app_icon": route.app.icon,
                "path": route.path,
                "permission": permission_code,
                "icon": route.icon,
                "label": route.label,
            })

        return allowed