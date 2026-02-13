# app/domain/services/app_resolver.py

from app.infrastructure.db.models import App, AppRoute, Permission
from app.extensions import db


def resolve_user_apps(user_permissions):

    apps = App.query.filter_by(active=True).all()

    result = []

    for app in apps:

        routes = AppRoute.query.filter_by(
            app_id=app.id,
            active=True
        ).order_by(AppRoute.order_index).all()

        allowed_routes = []

        for route in routes:

            # rota pública (sem permissão)
            if not route.permission_id:
                allowed_routes.append(route)
                continue

            permission = Permission.query.get(route.permission_id)

            if permission and permission.code in user_permissions:
                allowed_routes.append(route)

        if allowed_routes:
            result.append({
                "id": app.id,
                "name": app.name,
                "base_path": app.base_path,
                "icon": app.icon,
                "routes": [
                    {
                        "path": r.path,
                        "label": r.label,
                        "icon": r.icon,
                        "show_in_menu": r.show_in_menu,
                        "order": r.order_index
                    }
                    for r in allowed_routes
                ]
            })

    return result
