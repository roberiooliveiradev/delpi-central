# app/extensions/socket.py

from flask_socketio import SocketIO

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",  # moderno, sem eventlet
    logger=False,
    engineio_logger=False,
)