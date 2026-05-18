# app/interfaces/http/auth_middleware.py

from datetime import datetime
from uuid import UUID
from types import SimpleNamespace

from flask import request, g, jsonify

from delpi_auth.jwt_validator import validate_token
from app.application.use_cases.send_welcome_notification_use_case import (
    SendWelcomeNotificationUseCase,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
import logging

logger = logging.getLogger(__name__)


def authenticate():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None  # endpoint público pode passar

    token = auth_header.split(" ", 1)[1]

    try:
        claims = validate_token(token)
    except Exception:
        return jsonify({
            "errors": [
                {"code": "invalid_token", "message": "Token inválido", "path": "_global"}
            ]
        }), 401

    sub = claims.get("sub")
    email = claims.get("email")
    name = claims.get("name") or email or "Usuário"

    if not sub or not email:
        return jsonify({
            "errors": [
                {"code": "invalid_claims", "message": "Token inválido", "path": "_global"}
            ]
        }), 401

    try:
        user_uuid = UUID(str(sub))
    except Exception:
        return jsonify({
            "errors": [
                {"code": "invalid_uuid", "message": "Identificador inválido", "path": "_global"}
            ]
        }), 401

    is_new_user = False

    with SqlAlchemyUnitOfWork() as uow:
        user = uow.users.get_by_email(email)

        if not user:
            is_new_user = True
            uow.users.create(
                id=user_uuid,
                email=email,
                name=name,
                is_superadmin=False,
            )
            uow.session.commit()
            user = uow.users.get_by_email(email)

        uow.users.update_last_login(user_uuid, datetime.utcnow())
        uow.session.commit()

        roles = uow.rbac_queries.list_role_codes_by_user(user.id)
        groups = uow.rbac_queries.list_group_codes_by_user(user.id)
        permissions = uow.rbac_queries.list_permission_codes_by_user(user.id)

    if is_new_user and user:
        try:
            with SqlAlchemyUnitOfWork() as welcome_uow:
                SendWelcomeNotificationUseCase(welcome_uow).execute(str(user.id))
                welcome_uow.commit()
        except Exception:
            logger.exception("welcome notification failed for user %s", user.id)

    g.current_user = SimpleNamespace(
        id=str(user.id),
        email=user.email,
        name=user.name,
        roles=roles,
        groups=groups,
        permissions=permissions,
        is_superadmin=user.is_superadmin,
    )

    return None