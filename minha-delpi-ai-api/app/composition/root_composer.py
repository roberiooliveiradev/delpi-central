from flask import Flask

from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.json_logging import configure_logging
from app.interfaces.http.error_handlers import register_error_handlers
from app.interfaces.http.routes.health_routes import health_bp


def create_application() -> Flask:
    configure_logging(Settings.LOG_LEVEL)

    app = Flask(__name__)
    app.config["SERVICE_NAME"] = Settings.SERVICE_NAME
    app.config["ENV"] = Settings.ENV

    app.register_blueprint(health_bp)
    register_error_handlers(app)

    return app
