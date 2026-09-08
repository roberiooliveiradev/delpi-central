from flask import jsonify

from app.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CoreApiUnavailableError,
)


def register_error_handlers(app) -> None:
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(exc: AuthenticationError):
        return jsonify({"detail": exc.message}), 401

    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(exc: AuthorizationError):
        return jsonify({"detail": exc.message}), 403

    @app.errorhandler(CoreApiUnavailableError)
    def handle_core_unavailable(exc: CoreApiUnavailableError):
        return jsonify({"detail": exc.message}), 503
