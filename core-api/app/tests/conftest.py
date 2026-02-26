# app/tests/conftest.py

import pytest
from flask import Flask

from app.interfaces.http.health_controller import health_bp
from app.interfaces.http.dashboard_controller import dashboard_bp
from app.interfaces.http.favorite_controller import favorite_bp
from app.interfaces.http.notification_controller import notification_bp
from app.interfaces.http.apps_controller import admin_apps_bp
from app.interfaces.http.routes_controller import admin_routes_bp
from app.interfaces.http.plugins_controller import admin_plugins_bp
from app.interfaces.http.rbac_controller import rbac_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    app.register_blueprint(health_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(favorite_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(admin_apps_bp)
    app.register_blueprint(admin_routes_bp)
    app.register_blueprint(admin_plugins_bp)
    app.register_blueprint(rbac_bp)

    return app


@pytest.fixture
def client(app):
    return app.test_client()