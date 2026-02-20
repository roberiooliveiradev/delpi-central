# app/interfaces/http/auth_middleware.py

from flask import request, g
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.db.models import User
from app.extensions.db import db
from datetime import datetime
from app.domain.services.notification_service import notify_user
from app.infrastructure.security.rbac_cache import rbac_cache
from app.domain.services.permission_resolver import resolve_user_permissions

jwt_service = JWTService()


def authenticate():
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    claims = jwt_service.verify_token(token)

    sub = claims.get("sub")
    email = claims.get("email")
    name = claims.get("name")

    user = User.query.filter_by(email=email).first()

    is_new_user = False

    if not user:
        user = User(
            id=sub,
            email=email,
            name=name
        )
        db.session.add(user)
        is_new_user = True

    user.last_login_at = datetime.utcnow()

    db.session.commit()

    if is_new_user:
        notify_user(
            sub=sub,
            title="Bem-vindo à DELPI Central",
            message="Seu usuário foi criado com sucesso",
            type="success"
        )

    g.current_user = user

    cached = rbac_cache.get(str(user.id))

    if cached is not None:
        permissions = cached
    else:
        permissions = resolve_user_permissions(user)
        rbac_cache.set(str(user.id), permissions)

    g.current_permissions = permissions
    g.current_sub = sub


    return user
