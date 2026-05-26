# app/create_app.py

from flask import Flask
import logging

from app.infrastructure.config.settings import Config, TestingConfig
from delpi_auth.credential_guard import check_credentials

from app.extensions.db import db
from app.extensions.migrate import migrate
from app.extensions.socket import socketio

# Socket handlers
import app.interfaces.socket.socket_handlers  # noqa

# Blueprints
from app.interfaces.http.health_controller import health_bp
from app.interfaces.http.rbac_controller import rbac_bp
from app.interfaces.http.apps_controller import admin_apps_bp
from app.interfaces.http.me_controller import me_bp
from app.interfaces.http.notifications_controller import (
    admin_notifications_bp,
    integrations_notifications_bp,
)
from app.interfaces.http.presence_controller import admin_presence_bp
from app.interfaces.http.app_usage_controller import admin_app_usage_bp
from app.interfaces.http.admin_statistics_controller import admin_statistics_bp

from app.interfaces.http.auth_middleware import authenticate

from app.infrastructure.db.models import *  # noqa
from app.infrastructure.seeds.permissions_seed import seed_base_permissions
from app.infrastructure.schedulers.notification_dispatch_scheduler import (
    start_notification_dispatch_scheduler,
)

# IMPORTANT: registra policies
import app.interfaces.http.security.policies


def create_app(config_name: str | None = None) -> Flask:

    app = Flask(__name__)

    # ==========================================================
    # CONFIG
    # ==========================================================
    if config_name == "testing":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    # ==========================================================
    # LGPD CREDENTIAL GUARD (Art. 46)
    # ==========================================================
    if config_name != "testing":
        check_credentials()

    # ==========================================================
    # EXTENSIONS
    # ==========================================================
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    # ==========================================================
    # AUTH MIDDLEWARE
    # ==========================================================
    @app.before_request
    def before_request():

        if app.config.get("TESTING"):
            return

        result = authenticate()

        if result:
            return result

    # ==========================================================
    # BLUEPRINTS
    # ==========================================================
    app.register_blueprint(health_bp)
    app.register_blueprint(rbac_bp)
    app.register_blueprint(admin_apps_bp)
    app.register_blueprint(me_bp)
    app.register_blueprint(admin_notifications_bp)
    app.register_blueprint(integrations_notifications_bp)
    app.register_blueprint(admin_presence_bp)
    app.register_blueprint(admin_app_usage_bp)
    app.register_blueprint(admin_statistics_bp)

    # ==========================================================
    # DB INIT
    # ==========================================================
    with app.app_context():

        if not app.config.get("TESTING"):
            try:
                seed_base_permissions(db.session)
            except Exception as e:
                logging.warning(f"Permission seed failed: {e}")

    start_notification_dispatch_scheduler(app)

    # ==========================================================
    # CLI COMMANDS
    # ==========================================================
    from app.infrastructure.cli.data_retention_cli import data_retention_cli
    app.cli.add_command(data_retention_cli)

    return app