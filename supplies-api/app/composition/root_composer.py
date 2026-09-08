from flask import Flask

from app.infrastructure.config.settings import Settings
from app.interfaces.http.auth_middleware import register_auth_middleware
from app.interfaces.http.error_handlers import register_error_handlers
from app.interfaces.http.routes.health_routes import health_bp


def create_application() -> Flask:
    app = Flask(__name__)
    app.config["SERVICE_NAME"] = Settings.SERVICE_NAME
    app.config["ENV"] = Settings.ENV

    register_error_handlers(app)
    register_auth_middleware(app)
    app.register_blueprint(health_bp)

    return app
