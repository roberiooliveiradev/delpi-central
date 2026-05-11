from flask import Flask

from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.json_logging import configure_logging
from app.interfaces.http.auth_middleware import register_auth_middleware
from app.interfaces.http.error_handlers import register_error_handlers
from app.interfaces.http.request_logging import register_request_logging
from app.interfaces.http.routes.chat_routes import chat_bp
from app.interfaces.http.routes.health_routes import health_bp


def create_application() -> Flask:
    configure_logging(Settings.LOG_LEVEL)

    app = Flask(__name__)
    app.config["SERVICE_NAME"] = Settings.SERVICE_NAME
    app.config["ENV"] = Settings.ENV

    register_request_logging(app)
    register_auth_middleware(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(chat_bp)

    register_error_handlers(app)

    return app
