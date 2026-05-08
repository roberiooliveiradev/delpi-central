# app/infrastructure/persistence/sqlalchemy/favorite_app_repository.py

from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.domain.ports.favorite_app_repository import FavoriteAppRepository
from app.infrastructure.db.models import UserFavoriteApp, App


class SqlAlchemyFavoriteAppRepository(FavoriteAppRepository):

    def __init__(self, session: Session):
        self.session = session

    def list_user_favorites(self, user_id: str) -> List[Dict]:
        rows = (
            self.session.query(UserFavoriteApp, App)
            .join(App, App.id == UserFavoriteApp.app_id)
            .filter(UserFavoriteApp.user_id == user_id)
            .order_by(asc(UserFavoriteApp.order_index))
            .all()
        )

        result = []
        for fav, app in rows:
            result.append({
                "id": app.id,
                "name": app.name,
                "base_path": app.base_path,
                "icon": app.icon,
                "order_index": fav.order_index,
            })

        return result

    def exists(self, user_id: str, app_id: str) -> bool:
        return (
            self.session.query(UserFavoriteApp)
            .filter_by(user_id=user_id, app_id=app_id)
            .first()
            is not None
        )

    def add(self, user_id: str, app_id: str) -> None:
        max_index = (
            self.session.query(UserFavoriteApp)
            .filter_by(user_id=user_id)
            .count()
        )

        model = UserFavoriteApp(
            user_id=user_id,
            app_id=app_id,
            order_index=max_index,
        )
        self.session.add(model)

    def remove(self, user_id: str, app_id: str) -> None:
        (
            self.session.query(UserFavoriteApp)
            .filter_by(user_id=user_id, app_id=app_id)
            .delete(synchronize_session=False)
        )

    def delete_by_user_id(self, user_id: str) -> None:
        (
            self.session.query(UserFavoriteApp)
            .filter(UserFavoriteApp.user_id == user_id)
            .delete(synchronize_session=False)
        )