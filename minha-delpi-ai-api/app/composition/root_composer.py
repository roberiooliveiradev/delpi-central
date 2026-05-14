from flask import Flask

from app.extensions.db import db
from app.extensions.migrate import migrate
from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.json_logging import configure_logging
from app.interfaces.http.auth_middleware import register_auth_middleware
from app.interfaces.http.error_handlers import register_error_handlers
from app.interfaces.http.request_logging import register_request_logging
from app.interfaces.http.routes.admin_routes import admin_bp
from app.interfaces.http.routes.chat_routes import chat_bp
from app.interfaces.http.routes.health_routes import health_bp
from app.interfaces.http.routes.knowledge_routes import knowledge_bp
from app.interfaces.http.routes.tool_routes import tool_bp


def create_application() -> Flask:
    configure_logging(Settings.LOG_LEVEL)

    app = Flask(__name__)
    app.config["SERVICE_NAME"] = Settings.SERVICE_NAME
    app.config["ENV"] = Settings.ENV
    if not Settings.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Set DATABASE_URL or configure PLUGINS_DB_USER, PLUGINS_DB_PASSWORD, "
            "PLUGINS_DB_NAME, PLUGINS_DB_HOST and PLUGINS_DB_PORT."
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = Settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Import necessário para registrar models no metadata antes do Alembic.
    from app.infrastructure.db import models  # noqa: F401

    db.init_app(app)
    migrate.init_app(app, db)

    register_request_logging(app)
    register_auth_middleware(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(tool_bp)

    register_error_handlers(app)

    return app
