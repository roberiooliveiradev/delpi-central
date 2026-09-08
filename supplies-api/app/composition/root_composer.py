from flask import Flask

from app.infrastructure.config.settings import Settings
from app.interfaces.http.routes.health_routes import health_bp


def create_application() -> Flask:
    app = Flask(__name__)
    app.config["SERVICE_NAME"] = Settings.SERVICE_NAME
    app.config["ENV"] = Settings.ENV

    app.register_blueprint(health_bp)

    return app
