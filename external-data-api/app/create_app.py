from flask import Flask

from app.infrastructure.config.settings import Settings
from app.interfaces.http.routes.cnpj_routes import cnpj_bp
from app.interfaces.http.routes.health_routes import health_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SERVICE_NAME"] = Settings.SERVICE_NAME
    app.config["ENV"] = Settings.ENV

    app.register_blueprint(health_bp)
    app.register_blueprint(cnpj_bp)

    return app
