# app/interfaces/socket/socket_handlers.py

from flask import request
from flask_socketio import join_room, disconnect
from app.extensions.socket import socketio
from app.infrastructure.security.jwt_service import JWTService

jwt_service = JWTService()


@socketio.on("connect")
def handle_connect():

    token = None

    # Novo padrão (socket.io v4)
    if hasattr(request, "auth") and request.auth:
        token = request.auth.get("token")

    # 🔁 Compatibilidade antiga
    if not token:
        token = request.args.get("token")

    if not token:
        print("❌ Socket connect sem token -> disconnect")
        return False  # use False ao invés de disconnect()

    try:
        claims = jwt_service.verify_token(token)
        sub = claims.get("sub")

        if not sub:
            print("❌ Token sem sub -> disconnect")
            return False

        print("✅ Cliente conectado. SUB:", sub)

        join_room(sub)

    except Exception as e:
        print("❌ Token inválido no socket:", repr(e))
        return False