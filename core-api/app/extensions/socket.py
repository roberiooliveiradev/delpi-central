# app/extensions/socket.py

from flask_socketio import SocketIO

from delpi_auth.cors_policy import build_allowed_origins


socketio = SocketIO(
    cors_allowed_origins=build_allowed_origins(),
    async_mode="eventlet",
    logger=False,
    engineio_logger=False,
)