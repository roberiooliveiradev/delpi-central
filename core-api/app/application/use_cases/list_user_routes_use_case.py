# app/application/use_cases/list_user_routes_use_case.py

from app.domain.ports.route_query_port import RouteQueryPort
from typing import List, Dict


class ListUserRoutesUseCase:

    def __init__(self, route_queries: RouteQueryPort):
        self.route_queries = route_queries

    def execute(self, permissions: List[str]) -> List[Dict]:

        routes = self.route_queries.list_active_menu_routes()

        allowed = []

        for route in routes:

            permission_code = None

            if route.permission:
                permission_code = route.permission.code
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