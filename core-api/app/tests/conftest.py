# app/tests/conftest.py

import pytest
from flask import Flask

from app.interfaces.http.health_controller import health_bp
from app.interfaces.http.me_controller import me_bp
from app.interfaces.http.notifications_controller import admin_notifications_bp
from app.interfaces.http.apps_controller import admin_apps_bp
from app.interfaces.http.rbac_controller import rbac_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    app.register_blueprint(health_bp)
    app.register_blueprint(me_bp)
    app.register_blueprint(admin_notifications_bp)
    app.register_blueprint(admin_apps_bp)
    app.register_blueprint(rbac_bp)

    return app


@pytest.fixture
def client(app):
    return app.test_client()