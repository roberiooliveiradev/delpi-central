# app/create_app.py

from flask import Flask, g
from app.infrastructure.config.settings import Config, TestingConfig
from app.extensions.db import db
from app.extensions.migrate import migrate
from app.extensions.socket import socketio

import app.interfaces.socket.socket_handlers  # noqa: F401

from app.interfaces.http.health_controller import health_bp
from app.interfaces.http.auth_middleware import authenticate
from app.interfaces.http.me_controller import me_bp
from app.interfaces.http.plugins_controller import plugins_bp
from app.interfaces.http.dashboard_controller import dashboard_bp
from app.interfaces.http.notification_controller import notification_bp
from app.interfaces.http.rbac_admin_controller import rbac_admin_bp
from app.interfaces.http.apps_admin_controller import apps_admin_bp

from app.infrastructure.db.models import User  # 👈 precisamos disso
from app.infrastructure.db.models import *  # noqa: F401,F403

from app.domain.services.bootstrap_service import seed_initial_superadmin
from app.infrastructure.seeds.apps_seed import seed_crm_app
from app.infrastructure.seeds.permissions_seed import seed_base_permissions


def create_app(config_name: str | None = None):
    app = Flask(__name__)

    if config_name == "testing":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    # ==========================================================
    # AUTH HANDLING
    # ==========================================================

    if app.config.get("TESTING", False):

        # 🔥 Override simples para testes
        @app.before_request
        def fake_auth_for_testing():
            user = User.query.first()
            if user:
                g.current_user = user
                g.current_permissions = []
                g.current_sub = str(user.id)

    else:

        @app.before_request
        def before_request():
            authenticate()

    # ==========================================================
    # BLUEPRINTS
    # ==========================================================

    app.register_blueprint(health_bp, url_prefix="/core-api")
    app.register_blueprint(me_bp, url_prefix="/core-api")
    app.register_blueprint(plugins_bp, url_prefix="/core-api/plugins")
    app.register_blueprint(dashboard_bp, url_prefix="/core-api")
    app.register_blueprint(notification_bp, url_prefix="/core-api")
    app.register_blueprint(rbac_admin_bp)
    app.register_blueprint(apps_admin_bp)

    # ==========================================================
    # DB INIT
    # ==========================================================

    with app.app_context():
        db.create_all()

        if not app.config.get("TESTING", False):
            seed_base_permissions()
            seed_initial_superadmin()

    return app