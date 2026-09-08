from flask import jsonify

from app.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CoreApiUnavailableError,
)


def register_error_handlers(app) -> None:
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(exc: AuthenticationError):
        return jsonify({"detail": exc.message, "code": "unauthorized"}), 401

    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(exc: AuthorizationError):
        return jsonify({"detail": exc.message, "code": "forbidden"}), 403

    @app.errorhandler(CoreApiUnavailableError)
    def handle_core_unavailable(exc: CoreApiUnavailableError):
        return jsonify({"detail": exc.message, "code": "authz_unavailable"}), 503

    @app.errorhandler(404)
    def handle_not_found(_exc):
        return jsonify({"detail": "Not Found", "code": "not_found"}), 404

    @app.errorhandler(409)
    def handle_conflict(_exc):
        return jsonify({"detail": "Conflict", "code": "conflict"}), 409

    @app.errorhandler(422)
    def handle_unprocessable(_exc):
        return jsonify({"detail": "Unprocessable Entity", "code": "unprocessable"}), 422

    @app.errorhandler(500)
    def handle_internal(_exc):
        return jsonify({"detail": "Internal server error", "code": "internal_error"}), 500
