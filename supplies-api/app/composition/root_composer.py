from flask import Flask

from app.infrastructure.config.settings import Settings
from app.interfaces.http.auth_middleware import register_auth_middleware
from app.interfaces.http.error_handlers import register_error_handlers
from app.interfaces.http.request_context import register_request_context
from app.interfaces.http.routes.analytics_routes import analytics_bp
from app.interfaces.http.routes.health_routes import health_bp
from app.interfaces.http.routes.home_routes import home_bp
from app.interfaces.http.routes.me_routes import me_bp
from app.interfaces.http.routes.purchase_requests_routes import purchase_requests_bp


def create_application() -> Flask:
    app = Flask(__name__)
    app.config["SERVICE_NAME"] = Settings.SERVICE_NAME
    app.config["ENV"] = Settings.ENV

    register_request_context(app)
    register_error_handlers(app)
    register_auth_middleware(app)
    app.register_blueprint(health_bp)
    app.register_blueprint(me_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(purchase_requests_bp)

    return app

