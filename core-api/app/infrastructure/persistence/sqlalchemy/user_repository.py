# app/infrastructure/persistence/sqlalchemy/user_repository.py

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.infrastructure.db.models import User


class SqlAlchemyUserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter_by(email=email).first()

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self.session.get(User, user_id)

    def add(self, user: User) -> None:
        self.session.add(user)

    def update(self, user: User) -> None:
        # SQLAlchemy já trackeia; método existe por contrato
        self.session.add(user)