# app/interfaces/socket/socket_handlers.py

from flask import request
from flask_socketio import join_room
from app.extensions.socket import socketio

from delpi_auth.jwt_validator import validate_token


@socketio.on("connect")
def handle_connect():

    token = None

    # Socket.IO v4
    if hasattr(request, "auth") and request.auth:
        token = request.auth.get("token")

    # Compatibilidade antiga
    if not token:
        token = request.args.get("token")

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

    except Exception as e:
        print("❌ Token inválido no socket:", repr(e))
        return False