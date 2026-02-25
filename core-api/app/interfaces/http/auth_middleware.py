# app/interfaces/http/auth_middleware.py
from datetime import datetime
from uuid import UUID

from flask import request, g

from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.db.models import User
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.cache.rbac_permission_cache_adapter import RbacCachePermissionCacheAdapter
from app.domain.services.permission_resolver import PermissionResolver

from app.infrastructure.socket.socket_event_dispatcher import SocketIOEventDispatcher
from app.application.use_cases.notify_user_use_case import NotifyUserUseCase


jwt_service = JWTService()


def authenticate():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]
    claims = jwt_service.verify_token(token)

    sub = claims.get("sub")
    email = claims.get("email")
    name = claims.get("name") or email or "Usuário"

    if not sub or not email:
        return None

    # sub (Keycloak) costuma ser UUID string; User.id no seu model é UUID.
    try:
        user_uuid = UUID(str(sub))
    except Exception:
        # Se seu realm não usa UUID, aqui você decide uma estratégia.
        # Por enquanto: rejeita (mantém consistência do model User.id=UUID).
        return None

    uow = SqlAlchemyUnitOfWork()

    # 1) Carrega/cria usuário (via repo)
    user = uow.users.get_by_email(email)
    is_new_user = False

    if not user:
        user = User(
            id=user_uuid,
            email=email,
            name=name,
        )
        uow.users.add(user)
        is_new_user = True

    user.last_login_at = datetime.utcnow()
    uow.users.update(user)
    uow.commit()

    # 2) Notificação de boas-vindas (⚠️ migrar para port/usecase depois)
    if is_new_user:
        dispatcher = SocketIOEventDispatcher()
        notify_use_case = NotifyUserUseCase(
            uow=uow,
            notification_repo=uow.notifications,
            event_dispatcher=dispatcher,
        )

        notify_use_case.execute(
            user_id=sub,
            title="Bem-vindo à DELPI Central",
            message="Seu usuário foi criado com sucesso",
            type="success",
        )

    # 3) Resolve permissões via Domain Service + Ports
    cache = RbacCachePermissionCacheAdapter()
    resolver = PermissionResolver(permission_query=uow.permission_queries, cache=cache)

    permissions = resolver.resolve(user_id=user.id, is_superadmin=bool(user.is_superadmin))

    # 4) Contexto do request
    g.current_user = user
    g.current_permissions = permissions
    g.current_sub = sub  # usado por notifications (sub string)

    return user