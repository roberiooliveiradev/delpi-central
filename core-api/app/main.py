# app/main.py

import eventlet
eventlet.monkey_patch()

from app.create_app import create_app
from app.extensions.socket import socketio

app = create_app()

if __name__ == "__main__":
    # ✅ MUITO IMPORTANTE:
    # Sem reloader no Docker, senão cria 2 processos e perde eventos do socket
    socketio.run(
        app,
        host="0.0.0.0",
        port=8000,
        debug=False,
        use_reloader=False
    )
