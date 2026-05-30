from __future__ import annotations

import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)


def create_socket_app(fastapi_app):
    return socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
