# app/interfaces/http/auth_middleware.py

from datetime import datetime
from uuid import UUID

from flask import request, g

from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

from app.infrastructure.cache.rbac_permission_cache_adapter import (
    RbacCachePermissionCacheAdapter,
)

from app.domain.services.permission_resolver import PermissionResolver
from app.application.use_cases.notify_user_use_case import NotifyUserUseCase


jwt_service = JWTService()


def authenticate():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]

    try:
        claims = jwt_service.verify_token(token)
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

    try:
        with SqlAlchemyUnitOfWork() as uow:

            # ==================================================
            # 1️⃣ Carrega ou cria usuário
            # ==================================================

            user = uow.users.get_by_email(email)
            is_new_user = False

            if not user:
                uow.users.create(
                    id=user_uuid,
                    email=email,
                    name=name,
                    is_superadmin=False,
                )
                is_new_user = True
                user = uow.users.get_by_email(email)

            # Atualiza last login
            uow.users.update_last_login(user_uuid, datetime.utcnow())

            # ==================================================
            # 2️⃣ Notificação de boas-vindas
            # ==================================================

            if is_new_user:
                notify_use_case = NotifyUserUseCase(uow)
                notify_use_case.execute(
                    user_id=str(user.id),
                    title="Bem-vindo à DELPI Central",
                    message="Seu usuário foi criado com sucesso",
                    type="success",
                )

            # ==================================================
            # 3️⃣ Resolver permissões
            # ==================================================

            resolver = PermissionResolver(
                permission_query=uow.permission_queries,
                cache=RbacCachePermissionCacheAdapter(),
            )

            permissions = resolver.resolve(
                user_id=user.id,
                is_superadmin=bool(user.is_superadmin),
            )

        # ==================================================
        # 4️⃣ Fora da transação → popular contexto
        # ==================================================

        g.current_user = user
        g.current_permissions = permissions
        g.current_sub = str(user.id)

        return user

    except Exception:
        # segurança: não quebra autenticação silenciosamente
        return None