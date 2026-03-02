# app/interfaces/http/auth_middleware.py

from datetime import datetime
from uuid import UUID

from flask import request, g

from delpi_auth.jwt_validator import validate_token
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.application.use_cases.notify_user_use_case import NotifyUserUseCase


def authenticate():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]

    try:
        claims = validate_token(token)
    except Exception:
        return None

    sub = claims.get("sub")
    email = claims.get("email")
    name = claims.get("name") or email or "Usuário"

    if not sub or not email:
        return None

    try:
        user_uuid = UUID(str(sub))
    except Exception:
        return None

    permissions = claims.get("permissions", [])
    is_superadmin = bool(claims.get("is_superadmin"))

    try:
        with SqlAlchemyUnitOfWork() as uow:

            user = uow.users.get_by_email(email)
            is_new_user = False

            if not user:
                uow.users.create(
                    id=user_uuid,
                    email=email,
                    name=name,
                    is_superadmin=is_superadmin,
                )
                is_new_user = True
                user = uow.users.get_by_email(email)

            uow.users.update_last_login(user_uuid, datetime.utcnow())

            if is_new_user:
                notify_use_case = NotifyUserUseCase(uow)
                notify_use_case.execute(
                    user_id=str(user.id),
                    title="Bem-vindo à DELPI Central",
                    message="Seu usuário foi criado com sucesso",
                    type="success",
                )

        # 🔥 SEM PermissionResolver
        g.current_user = user
        g.current_permissions = permissions
        g.current_sub = str(user.id)

        return user

    except Exception:
        return None