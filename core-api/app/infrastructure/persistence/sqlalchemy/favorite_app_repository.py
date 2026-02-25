# app/infrastructure/persistence/sqlalchemy/favorite_app_repository.py


from typing import List
from sqlalchemy.orm import Session

from app.domain.ports.favorite_app_repository import FavoriteAppRepository
from app.infrastructure.db.models import UserFavoriteApp


class SqlAlchemyFavoriteAppRepository(FavoriteAppRepository):

    def __init__(self, session: Session):
        self.session = session

    def list_user_favorites(self, user_id: str) -> List[str]:
        rows = (
            self.session.query(UserFavoriteApp)
            .filter_by(user_id=user_id)
            .all()
        )
        return [r.app_id for r in rows]

    def exists(self, user_id: str, app_id: str) -> bool:
        return (
            self.session.query(UserFavoriteApp)
            .filter_by(user_id=user_id, app_id=app_id)
            .first()
            is not None
        )

    def add(self, user_id: str, app_id: str) -> None:
        model = UserFavoriteApp(
            user_id=user_id,
            app_id=app_id,
        )
        self.session.add(model)

    def remove(self, user_id: str, app_id: str) -> None:
        (
            self.session.query(UserFavoriteApp)
            .filter_by(user_id=user_id, app_id=app_id)
            .delete()
        )