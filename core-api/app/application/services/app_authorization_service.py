# app/application/services/app_authorization_service.py

from typing import List
from app.domain.ports.app_query_port import AppDTO, RouteDTO
from app.domain.plugins.route_permission import route_allows_any


class AppAuthorizationService:
    """
    Serviço responsável por aplicar regras de autorização
    sobre uma lista de aplicações e suas rotas.

    Não acessa banco.
    Não resolve permissões.
    Apenas filtra com base nas permissões já resolvidas.

    Rotas com ``any_of_permission_codes`` exigem ANY-OF (não ALL).
    """

    def filter_apps(
        self,
        apps: List[AppDTO],
        permissions: List[str],
        is_superadmin: bool,
    ) -> List[AppDTO]:

        if is_superadmin:
            return apps

        authorized_apps: List[AppDTO] = []

        for app in apps:
            filtered_routes: List[RouteDTO] = []

            for route in app.routes:
                if route_allows_any(
                    permission_code=route.permission_code,
                    any_of_permission_codes=route.any_of_permission_codes,
                    user_permissions=permissions,
                ):
                    filtered_routes.append(route)

            if filtered_routes:
                authorized_apps.append(
                    AppDTO(
                        id=app.id,
                        name=app.name,
                        base_path=app.base_path,
                        icon=app.icon,
                        type=app.type,
                        entry_url=app.entry_url,
                        render_mode=app.render_mode,
                        routes=filtered_routes,
                    )
                )

        return authorized_apps

    def filter_app_ids(
        self,
        apps: List[AppDTO],
        permissions: List[str],
        is_superadmin: bool,
    ) -> set[str]:
        authorized = self.filter_apps(apps, permissions, is_superadmin)
        return {app.id for app in authorized}