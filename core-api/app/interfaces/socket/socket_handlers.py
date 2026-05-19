# app/interfaces/socket/socket_handlers.py

from flask import request
from flask_socketio import join_room

from app.extensions.socket import socketio
from app.infrastructure.presence.presence_store_provider import (
    get_user_presence_store,
    is_user_presence_enabled,
)

from delpi_auth.jwt_validator import validate_token


def _register_presence(user_id: str) -> None:
    if not is_user_presence_enabled():
        return
    get_user_presence_store().register(user_id=user_id, session_id=request.sid)


def _unregister_presence() -> None:
    if not is_user_presence_enabled():
        return
    get_user_presence_store().unregister(request.sid)


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

    except Exception as e:
        print("❌ Token inválido no socket:", repr(e))
        return False


@socketio.on("disconnect")
def handle_disconnect():
    _unregister_presence()


@socketio.on("presence.ping")
def handle_presence_ping():
    if not is_user_presence_enabled():
        return
    get_user_presence_store().touch(request.sid)
