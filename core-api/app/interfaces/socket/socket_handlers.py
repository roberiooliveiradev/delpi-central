# app/interfaces/socket/socket_handlers.py

from flask import request
from flask_socketio import join_room, disconnect
from app.extensions.socket import socketio
from app.infrastructure.security.jwt_service import JWTService

jwt_service = JWTService()

@socketio.on("connect")
def handle_connect():
    token = request.args.get("token")

    if not token:
        print("Socket connect sem token -> disconnect")
        disconnect()
        return

    try:
        claims = jwt_service.verify_token(token)
        sub = claims.get("sub")

        if not sub:
            print("Socket token sem sub -> disconnect")
            disconnect()
            return

        print("Cliente tentando conectar...")
        print("SUB do socket:", sub)

        join_room(sub)

        print("Entrou na room:", sub)

    except Exception as e:
        print("Erro no socket:", e)
        disconnect()
