from __future__ import annotations

import socketio

from delpi_auth.cors_policy import build_allowed_origins

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=build_allowed_origins(),
    logger=False,
    engineio_logger=False,
)


def create_socket_app(fastapi_app):
    return socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
