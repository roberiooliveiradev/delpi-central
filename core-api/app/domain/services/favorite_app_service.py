# app/domain/services/favorite_app_service.py

from sqlalchemy import func
from app.extensions.db import db
from app.infrastructure.db.models import (
    UserFavoriteApp,
    App,
)
from app.domain.services.permission_resolver import resolve_user_permissions
from app.domain.services.app_resolver import resolve_user_apps


class FavoriteAppService:

    @staticmethod
    def list_favorites(user):
        permissions = resolve_user_permissions(user)
        allowed_apps = resolve_user_apps(permissions)
        allowed_ids = {a["id"] for a in allowed_apps}

        favorites = (
            db.session.query(UserFavoriteApp)
            .join(App)
            .filter(
                UserFavoriteApp.user_id == user.id,
                App.active == True,
            )
            .order_by(UserFavoriteApp.order_index.asc())
            .all()
        )

        return [
            {
                "id": f.app.id,
                "name": f.app.name,
                "base_path": f.app.base_path,
                "icon": f.app.icon,
                "order_index": f.order_index
            }
            for f in favorites
            if f.app_id in allowed_ids
        ]


    @staticmethod
    def add_favorite(user, app_id):
        # Verifica se app existe e está ativa
        app = App.query.filter_by(id=app_id, active=True).first()
        if not app:
            raise ValueError("Application not found or inactive")

        # Verifica permissão do usuário na app
        permissions = resolve_user_permissions(user)
        allowed_apps = resolve_user_apps(permissions)
        allowed_ids = {a["id"] for a in allowed_apps}

        if app_id not in allowed_ids:
            raise PermissionError("User has no access to this application")

        # Evita duplicidade
        existing = UserFavoriteApp.query.filter_by(
            user_id=user.id,
            app_id=app_id
        ).first()

        if existing:
            return existing

        # Calcula próximo order_index
        max_order = (
            db.session.query(func.max(UserFavoriteApp.order_index))
            .filter_by(user_id=user.id)
            .scalar()
        )

        next_order = (max_order or 0) + 1

        favorite = UserFavoriteApp(
            user_id=user.id,
            app_id=app_id,
            order_index=next_order
        )

        db.session.add(favorite)
        db.session.commit()

        return favorite

    @staticmethod
    def reorder_favorites(user, items):
        """
        items = [
            {"app_id": "...", "order_index": 1},
            ...
        ]
        """

        favorites = {
            f.app_id: f
            for f in UserFavoriteApp.query.filter_by(user_id=user.id).all()
        }

        for item in items:
            app_id = item.get("app_id")
            order_index = item.get("order_index")

            if app_id not in favorites:
                raise ValueError(f"App {app_id} is not in favorites")

            favorites[app_id].order_index = int(order_index)

        db.session.commit()

        return True

    @staticmethod
    def remove_favorite(user, app_id):
        favorite = UserFavoriteApp.query.filter_by(
            user_id=user.id,
            app_id=app_id
        ).first()

        if not favorite:
            raise ValueError("Favorite not found")

        db.session.delete(favorite)
        db.session.commit()

        return True
