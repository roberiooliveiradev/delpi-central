# app/interfaces/http/serializers/user_serializer.py

from datetime import date, datetime
from app.domain.ports.user_repository_port import UserDTO


def serialize_user_dto(user: UserDTO) -> dict:
    birth_date = user.birth_date
    if isinstance(birth_date, datetime):
        birth_date = birth_date.date()

    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "active": user.active,
        "is_superadmin": user.is_superadmin,
        "last_login_at": user.last_login_at.isoformat() + "Z"
        if user.last_login_at
        else None,
        "birth_date": birth_date.isoformat() if isinstance(birth_date, date) else None,
    }
