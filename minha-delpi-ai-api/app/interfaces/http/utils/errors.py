from flask import jsonify


def error_response(status_code: int, code: str, message: str, path: str = "_global"):
    payload = {
        "errors": [
            {
                "code": code,
                "message": message,
                "path": path,
            }
        ]
    }

    return jsonify(payload), status_code


def not_found(message: str = "Resource not found"):
    return error_response(404, "not_found", message)


def server_error(message: str = "Internal server error"):
    return error_response(500, "internal_error", message)
