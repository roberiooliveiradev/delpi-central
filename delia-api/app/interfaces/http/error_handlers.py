from flask import Flask, jsonify


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def handle_not_found(_exc):
        return jsonify({"detail": "Not Found", "code": "not_found"}), 404

    @app.errorhandler(500)
    def handle_internal(_exc):
        return jsonify({"detail": "Internal server error", "code": "internal_error"}), 500
