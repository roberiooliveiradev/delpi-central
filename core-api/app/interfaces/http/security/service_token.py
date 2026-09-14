# app/interfaces/http/security/service_token.py

import os
import secrets
from functools import wraps

from flask import request

from app.interfaces.http.utils.errors import forbidden, unauthorized

# Dedicated secret for effective-access-by-subject (CALLER_BINDING via secret separation).
# Must NOT fall back to CORE_API_INTEGRATIONS_SERVICE_TOKEN — that shared secret is held by
# many plugins and must not unlock full permission dumps for arbitrary subjects.
EFFECTIVE_ACCESS_SERVICE_TOKEN_ENV = "CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN"
INTEGRATIONS_SERVICE_TOKEN_ENV = "CORE_API_INTEGRATIONS_SERVICE_TOKEN"


def _get_expected_service_token() -> str | None:
    token = os.getenv(INTEGRATIONS_SERVICE_TOKEN_ENV, "").strip()
    return token or None


def _get_expected_effective_access_service_token() -> str | None:
    token = os.getenv(EFFECTIVE_ACCESS_SERVICE_TOKEN_ENV, "").strip()
    return token or None


def _extract_service_token() -> str | None:
    header_token = request.headers.get("X-Delpi-Service-Token")
    if header_token:
        return header_token.strip()

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return None


def matches_effective_access_service_token(token: str | None) -> bool:
    """True when Bearer/header value equals the dedicated effective-access secret."""
    expected = _get_expected_effective_access_service_token()
    if not expected or not token:
        return False
    return secrets.compare_digest(token.strip(), expected)


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

            if not secrets.compare_digest(provided, expected):
                return forbidden("Invalid service token")

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_effective_access_service_token():
    """AuthN for GET /integrations/effective-access/** — dedicated secret only."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            expected = _get_expected_effective_access_service_token()
            if not expected:
                return forbidden("Effective access service token is not configured")

            provided = _extract_service_token()
            if not provided:
                return unauthorized("Service token required")

            if not secrets.compare_digest(provided, expected):
                return forbidden("Invalid service token")

            return fn(*args, **kwargs)

        return wrapper

    return decorator
