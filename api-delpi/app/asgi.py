from __future__ import annotations

import socketio

from app.main import app
from app.interface.socket.sio_server import sio

_sio_app = socketio.ASGIApp(sio, socketio_path="socket.io")

_SOCKET_PREFIXES = (
    "/socket.io",
    "/apps/api-delpi/socket.io",
)


def _is_socketio_request(path: str) -> bool:
    normalized = (path or "/").split("?", 1)[0]
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}/")
        for prefix in _SOCKET_PREFIXES
    )


def _rewrite_socket_path(scope: dict) -> dict:
    path = scope.get("path", "")
    gateway_prefix = "/apps/api-delpi/socket.io"
    if path.startswith(gateway_prefix):
        suffix = path[len(gateway_prefix):] or "/"
        return {**scope, "path": f"/socket.io{suffix}"}
    return scope


async def application(scope, receive, send):
    if scope["type"] in ("http", "websocket") and _is_socketio_request(scope.get("path", "")):
        await _sio_app(_rewrite_socket_path(scope), receive, send)
        return

    await app(scope, receive, send)
