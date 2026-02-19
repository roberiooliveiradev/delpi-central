# app/create_app.py

from flask import Flask
from app.infrastructure.config.settings import Config
from app.extensions.db import db
from app.extensions.migrate import migrate
from app.extensions.socket import socketio

# garante que os handlers do socket sejam registrados
import app.interfaces.socket.socket_handlers  # noqa: F401

from app.interfaces.http.health_controller import health_bp
from app.interfaces.http.auth_middleware import authenticate
from app.interfaces.http.me_controller import me_bp
from app.interfaces.http.plugins_controller import plugins_bp
from app.interfaces.http.dashboard_controller import dashboard_bp
from app.interfaces.http.notification_controller import notification_bp
from app.interfaces.http.rbac_admin_controller import rbac_admin_bp
from app.interfaces.http.apps_admin_controller import apps_admin_bp

from app.infrastructure.db.models import *  # noqa: F401,F403
from app.domain.services.bootstrap_service import seed_initial_superadmin
from app.infrastructure.seeds.apps_seed import seed_crm_app
from app.infrastructure.seeds.permissions_seed import seed_base_permissions


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    @app.before_request
    def before_request():
        authenticate()

    # url_prefix centralizado aqui
    app.register_blueprint(health_bp, url_prefix="/core-api")
    app.register_blueprint(me_bp, url_prefix="/core-api")
    app.register_blueprint(plugins_bp, url_prefix="/core-api/plugins")
    app.register_blueprint(dashboard_bp, url_prefix="/core-api")
    app.register_blueprint(notification_bp, url_prefix="/core-api")
    
    # Admin
    app.register_blueprint(rbac_admin_bp)         # /core-api/admin/rbac
    app.register_blueprint(apps_admin_bp)         # /core-api/admin/apps
    
    with app.app_context():
        seed_base_permissions()
        seed_crm_app()
        seed_initial_superadmin()

    return app
