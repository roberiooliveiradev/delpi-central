from __future__ import annotations

from flask import Flask

from app.infrastructure.config.settings import Settings
from app.infrastructure.logging import configure_logging
from app.interfaces.http.error_handlers import register_error_handlers
from app.interfaces.http.health_routes import health_bp
from app.interfaces.http.request_logging import register_request_logging


def create_application(*, testing: bool = False) -> Flask:
    settings = Settings.for_testing() if testing else Settings()
    logger = configure_logging(settings.service_name, settings.log_level)

    app = Flask(__name__)
    app.config["TESTING"] = testing
    app.config["DEBUG"] = False if testing else settings.debug
    app.config["SERVICE_NAME"] = settings.service_name
    app.config["SERVICE_VERSION"] = settings.service_version
    app.config["DELIA_ENV"] = settings.environment
    app.config["PROPAGATE_EXCEPTIONS"] = False

    register_error_handlers(app)
    register_request_logging(app, logger)
    app.register_blueprint(health_bp)

    logger.info(
        "delia_api_started service=%s version=%s env=%s",
        settings.service_name,
        settings.service_version,
        settings.environment,
    )
    return app
