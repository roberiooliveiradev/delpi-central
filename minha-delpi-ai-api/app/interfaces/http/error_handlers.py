from werkzeug.exceptions import HTTPException

from app.interfaces.http.utils.errors import error_response, not_found, server_error


def register_error_handlers(app):
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
