# app/create_app.py

from flask import Flask, request
from app.infrastructure.config.settings import Config, TestingConfig

from app.extensions.db import db
from app.extensions.migrate import migrate
from app.extensions.socket import socketio

# Socket handlers
import app.interfaces.socket.socket_handlers  # noqa

# Blueprints
from app.interfaces.http.health_controller import health_bp
from app.interfaces.http.dashboard_controller import dashboard_bp
from app.interfaces.http.notification_controller import notification_bp
from app.interfaces.http.favorite_controller import favorite_bp
from app.interfaces.http.apps_controller import admin_apps_bp
from app.interfaces.http.rbac_controller import rbac_bp
from app.interfaces.http.plugins_controller import admin_plugins_bp
from app.interfaces.http.routes_controller import admin_routes_bp

from app.interfaces.http.auth_middleware import authenticate

from app.infrastructure.db.models import *  # noqa
from app.infrastructure.seeds.permissions_seed import seed_base_permissions


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
        # health endpoint não precisa autenticação
        if app.url_map.is_endpoint_expecting(request.endpoint, None):
            return

        authenticate()

    # ==========================================================
    # BLUEPRINTS
    # ==========================================================
    app.register_blueprint(health_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(favorite_bp)
    app.register_blueprint(admin_apps_bp)
    app.register_blueprint(rbac_bp)
    app.register_blueprint(admin_plugins_bp)
    app.register_blueprint(admin_routes_bp)
    # ==========================================================
    # DB INIT (dev only)
    # ==========================================================
    with app.app_context():
        db.create_all()
        seed_base_permissions(db.session)

    return app