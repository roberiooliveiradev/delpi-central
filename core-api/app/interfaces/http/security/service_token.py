# app/interfaces/http/security/service_token.py

import os
from functools import wraps

from flask import request

from app.interfaces.http.utils.errors import forbidden, unauthorized


def _get_expected_service_token() -> str | None:
    token = os.getenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "").strip()
    return token or None


def _extract_service_token() -> str | None:
    header_token = request.headers.get("X-Delpi-Service-Token")
    if header_token:
        return header_token.strip()

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return None


def require_service_token():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            expected = _get_expected_service_token()
            if not expected:
                return forbidden("Service token is not configured")

            provided = _extract_service_token()
            if not provided:
                return unauthorized("Service token required")

            if provided != expected:
                return forbidden("Invalid service token")

            return fn(*args, **kwargs)

        return wrapper

    return decorator
