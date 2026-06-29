# app/interfaces/http/auth_middleware.py

import logging
import os
import secrets
from datetime import datetime
from types import SimpleNamespace
from uuid import UUID

from flask import g, jsonify, request

from delpi_auth.jwt_validator import validate_token

from app.application.use_cases.send_welcome_notification_use_case import (
    SendWelcomeNotificationUseCase,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)


def _matches_integrations_service_token(token: str) -> bool:
    expected = os.getenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "").strip()
    if not expected or not token:
        return False
    return secrets.compare_digest(token.strip(), expected)


def _name_from_keycloak_claims(claims: dict, *, email: str) -> str:
    name = (claims.get("name") or "").strip()
    if name:
        return name

    given = (claims.get("given_name") or "").strip()
    family = (claims.get("family_name") or "").strip()
    combined = f"{given} {family}".strip()
    if combined:
        return combined

    preferred = (claims.get("preferred_username") or "").strip()
    if preferred and "@" not in preferred:
        return preferred

    return email or "Usuário"


def authenticate():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None  # endpoint público pode passar

    token = auth_header.split(" ", 1)[1]

    if _matches_integrations_service_token(token):
        return None

    try:
        claims = validate_token(token)
    except Exception:
        return jsonify({
            "errors": [
                {"code": "invalid_token", "message": "Token inválido", "path": "_global"}
            ]
        }), 401

    sub = claims.get("sub")
    email = (claims.get("email") or "").strip().lower()

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

    name = _name_from_keycloak_claims(claims, email=email)
    is_new_user = False

    with SqlAlchemyUnitOfWork() as uow:
        user = uow.users.get_by_id(user_uuid) or uow.users.get_by_email(email)

        if not user:
            is_new_user = True
            uow.users.create(
                id=user_uuid,
                email=email,
                name=name,
                is_superadmin=False,
            )
            uow.session.commit()
            user = uow.users.get_by_id(user_uuid)
        elif user.name != name or user.email != email:
            uow.users.update_identity(user.id, name=name, email=email)
            uow.session.commit()
            user = uow.users.get_by_id(user.id)

        uow.users.update_last_login(user.id, datetime.utcnow())
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