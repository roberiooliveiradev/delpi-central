from werkzeug.exceptions import HTTPException

from app.domain.exceptions.auth_exceptions import (
    AuthenticationError,
    InvalidClaimsError,
    InvalidTokenError,
)
from app.domain.exceptions.authorization_exceptions import (
    AuthorizationError,
    CoreApiUnavailableError,
)
from app.interfaces.http.utils.errors import error_response, not_found, server_error


def register_error_handlers(app):
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        return error_response(
            status_code=401,
            code=getattr(error, "code", "unauthorized"),
            message=getattr(error, "message", "Authentication required"),
        )

    @app.errorhandler(InvalidTokenError)
    def handle_invalid_token_error(error):
        return error_response(
            status_code=401,
            code=getattr(error, "code", "invalid_token"),
            message=getattr(error, "message", "Invalid token"),
        )

    @app.errorhandler(InvalidClaimsError)
    def handle_invalid_claims_error(error):
        return error_response(
            status_code=401,
            code=getattr(error, "code", "invalid_claims"),
            message=getattr(error, "message", "Token missing required claims"),
        )

    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error):
        return error_response(
            status_code=403,
            code=getattr(error, "code", "forbidden"),
            message=getattr(error, "message", "Permission denied"),
        )

    @app.errorhandler(CoreApiUnavailableError)
    def handle_core_api_unavailable(error):
        return error_response(
            status_code=503,
            code=getattr(error, "code", "core_api.unavailable"),
            message=getattr(error, "message", "Core API unavailable"),
        )

    @app.errorhandler(404)
    def handle_not_found(_error):
        return not_found()

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return error_response(
            status_code=error.code or 500,
            code="http_error",
            message=error.description or "HTTP error",
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        app.logger.exception("Unhandled exception", exc_info=error)
        return server_error()
