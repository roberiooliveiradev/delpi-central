# app/create_app.py

from flask import Flask
from app.infrastructure.config.settings import Config
from app.extensions import db, migrate
from app.interfaces.http.health_controller import health_bp

from app.infrastructure.db.models import *  # noqa: F401,F403


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(health_bp)

    return app
