# app/main.py

from app.create_app import create_app
from app.extensions.socket import socketio

app = create_app()

if __name__ == "__main__":
    # Usa threading (padrão moderno)
    # Não depende de eventlet nem monkey_patch
    socketio.run(
        app,
        host="0.0.0.0",
        port=8000,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )