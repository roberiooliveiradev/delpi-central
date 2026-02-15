# app/interfaces/socket/socket_handlers.py

from flask import request
from flask_socketio import join_room, disconnect
from app.extensions.socket import socketio
from app.infrastructure.security.jwt_service import JWTService

jwt_service = JWTService()

@socketio.on("connect")
def handle_connect():
    print("Cliente tentando conectar...")

    token = request.args.get("token")

    if not token:
        print("Sem token")
        disconnect()
        return

    try:
        claims = jwt_service.verify_token(token)
        sub = claims.get("sub")

        print("SUB do socket:", sub)

        join_room(sub)

        print("Entrou na room:", sub)

    except Exception as e:
        print("Erro no socket:", e)
        disconnect()

