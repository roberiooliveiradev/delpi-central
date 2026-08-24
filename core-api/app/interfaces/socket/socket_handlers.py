# app/interfaces/socket/socket_handlers.py

from uuid import UUID

from flask import request
from flask_socketio import join_room

from app.extensions.socket import socketio
from app.application.services.usage_session_recorder import persist_usage_segment
from app.infrastructure.app_usage.app_usage_live_store_provider import (
    get_app_usage_live_store,
    is_app_usage_enabled,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.presence.presence_store_provider import (
    get_user_presence_store,
    is_user_presence_enabled,
)
from app.application.use_cases.admin.record_app_usage_use_case import (
    RecordAppUsageUseCase,
)

from delpi_auth.jwt_validator import validate_token

_socket_authenticated_users: dict[str, str] = {}


def _resolve_socket_user_id() -> str | None:
    user_id = _socket_authenticated_users.get(request.sid)
    if user_id:
        return user_id
    if is_app_usage_enabled():
        return get_app_usage_live_store().get_user_id(request.sid)
    return None


def _user_has_usage_tracking_consent(user_id: str) -> bool:
    from app.domain.services.usage_tracking_consent_service import (
        user_has_usage_tracking_consent,
    )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            return user_has_usage_tracking_consent(uow, UUID(str(user_id)))
    except Exception:
        return False


def _register_presence(user_id: str) -> None:
    if not is_user_presence_enabled():
        return
    get_user_presence_store().register(user_id=user_id, session_id=request.sid)


def _flush_presence_session() -> None:
    if not is_user_presence_enabled():
        return

    store = get_user_presence_store()
    pop = getattr(store, "pop_connection", None)
    if not callable(pop):
        store.unregister(request.sid)
        return

    connection = pop(request.sid)
    if not connection:
        return

    persist_usage_segment(
        user_id=connection["user_id"],
        app_id=None,
        route_path=None,
        started_at=connection["started_at"],
        ended_at=connection["ended_at"],
        source="socket_disconnect",
        socket_session_id=connection.get("socket_session_id"),
    )


def _flush_active_app_session(*, app_id: str | None, source: str) -> None:
    if not is_app_usage_enabled():
        return

    store = get_app_usage_live_store()
    pop = getattr(store, "pop_active_segment", None)
    if not callable(pop):
        if app_id:
            store.clear_active_app(request.sid, app_id=app_id)
        return

    segment = pop(request.sid, app_id=app_id)
    if not segment:
        return

    persist_usage_segment(
        user_id=segment["user_id"],
        app_id=segment.get("app_id"),
        route_path=segment.get("route_path"),
        started_at=segment["started_at"],
        ended_at=segment["ended_at"],
        source=source,
        socket_session_id=request.sid,
    )


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

    if auth and "token" in auth:
        token = auth["token"]

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

        user_id = str(sub)
        _socket_authenticated_users[request.sid] = user_id
        join_room(user_id)

        if _user_has_usage_tracking_consent(user_id):
            _register_presence(user_id)
            _bind_app_usage_session(user_id)

    except Exception as e:
        print("❌ Token inválido no socket:", repr(e))
        return False


@socketio.on("disconnect")
def handle_disconnect():
    user_id = _resolve_socket_user_id()
    if user_id and _user_has_usage_tracking_consent(user_id):
        _flush_active_app_session(app_id=None, source="socket_disconnect")
        _flush_presence_session()
    else:
        if is_user_presence_enabled():
            get_user_presence_store().unregister(request.sid)
        _unbind_app_usage_session()

    _socket_authenticated_users.pop(request.sid, None)


@socketio.on("presence.ping")
def handle_presence_ping():
    if not is_user_presence_enabled():
        return

    user_id = _resolve_socket_user_id()
    if not user_id or not _user_has_usage_tracking_consent(user_id):
        return

    get_user_presence_store().touch(request.sid)


@socketio.on("app_usage.open")
def handle_app_usage_open(data):
    if not is_app_usage_enabled():
        return

    app_id, route_path = _extract_app_usage_payload(data)
    if not app_id:
        return

    user_id = _resolve_socket_user_id()
    if not user_id:
        return

    try:
        with SqlAlchemyUnitOfWork() as uow:
            from app.domain.services.usage_tracking_consent_service import (
                user_has_usage_tracking_consent,
            )

            user_uuid = UUID(str(user_id))
            if not user_has_usage_tracking_consent(uow, user_uuid):
                return

            _bind_app_usage_session(user_id)
            _register_presence(user_id)

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

    user_id = _resolve_socket_user_id()
    if not user_id or not _user_has_usage_tracking_consent(user_id):
        return

    app_id, _route_path = _extract_app_usage_payload(data)
    get_app_usage_live_store().touch(request.sid, app_id=app_id)


@socketio.on("app_usage.close")
def handle_app_usage_close(data):
    if not is_app_usage_enabled():
        return

    user_id = _resolve_socket_user_id()
    if not user_id or not _user_has_usage_tracking_consent(user_id):
        return

    app_id, _route_path = _extract_app_usage_payload(data)
    _flush_active_app_session(app_id=app_id, source="socket_close")
