# app/interfaces/socket/socket_handlers.py

from flask import request
from flask_socketio import join_room

from app.extensions.socket import socketio
from app.infrastructure.app_usage.app_usage_live_store_provider import (
    get_app_usage_live_store,
    is_app_usage_enabled,
)
from app.infrastructure.presence.presence_store_provider import (
    get_user_presence_store,
    is_user_presence_enabled,
)
from app.application.use_cases.admin.record_app_usage_use_case import (
    RecordAppUsageUseCase,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

from delpi_auth.jwt_validator import validate_token


def _register_presence(user_id: str) -> None:
    if not is_user_presence_enabled():
        return
    get_user_presence_store().register(user_id=user_id, session_id=request.sid)


def _unregister_presence() -> None:
    if not is_user_presence_enabled():
        return
    get_user_presence_store().unregister(request.sid)


def _bind_app_usage_session(user_id: str) -> None:
    if not is_app_usage_enabled():
        return
    get_app_usage_live_store().bind_session(
        user_id=user_id,
        session_id=request.sid,
    )


def _unbind_app_usage_session() -> None:
    if not is_app_usage_enabled():
        return
    get_app_usage_live_store().unbind_session(request.sid)


def _extract_app_usage_payload(data) -> tuple[str | None, str | None]:
    if not isinstance(data, dict):
        return None, None

    app_id = data.get("appId") or data.get("app_id")
    route_path = data.get("routePath") or data.get("route_path")

    normalized_app_id = str(app_id).strip() if app_id else None
    normalized_route = str(route_path).strip() if route_path else None

    return normalized_app_id or None, normalized_route or None


@socketio.on("connect")
def handle_connect(auth):

    token = None

    # Socket.IO v4 padrão
    if auth and "token" in auth:
        token = auth["token"]

    # compatibilidade fallback
    if not token:
        from flask import request as flask_request

        token = flask_request.args.get("token")

    if not token:
        print("❌ Socket connect sem token -> disconnect")
        return False

    try:
        claims = validate_token(token)

        sub = claims.get("sub")

        if not sub:
            print("❌ Token sem sub -> disconnect")
            return False

        print("✅ Cliente conectado. SUB:", sub)

        join_room(sub)
        _register_presence(str(sub))
        _bind_app_usage_session(str(sub))

    except Exception as e:
        print("❌ Token inválido no socket:", repr(e))
        return False


@socketio.on("disconnect")
def handle_disconnect():
    _unregister_presence()
    _unbind_app_usage_session()


@socketio.on("presence.ping")
def handle_presence_ping():
    if not is_user_presence_enabled():
        return
    get_user_presence_store().touch(request.sid)


@socketio.on("app_usage.open")
def handle_app_usage_open(data):
    if not is_app_usage_enabled():
        return

    app_id, route_path = _extract_app_usage_payload(data)
    if not app_id:
        return

    user_id = get_app_usage_live_store().get_user_id(request.sid)
    if not user_id:
        return

    try:
        with SqlAlchemyUnitOfWork() as uow:
            # LGPD: respeitar opt-out de rastreamento de uso
            from uuid import UUID
            consent = uow.consents.get_by_user_and_purpose(
                UUID(str(user_id)), "usage_tracking"
            )
            if consent and not consent.granted:
                return

            RecordAppUsageUseCase(uow).execute(
                user_id=user_id,
                session_id=request.sid,
                app_id=app_id,
                route_path=route_path,
            )
            uow.commit()
    except Exception as exc:
        print("⚠️ app_usage.open failed:", repr(exc))


@socketio.on("app_usage.ping")
def handle_app_usage_ping(data):
    if not is_app_usage_enabled():
        return

    app_id, _route_path = _extract_app_usage_payload(data)
    store = get_app_usage_live_store()
    store.touch(request.sid, app_id=app_id)
