"""Flask adapter for individual S2S authentication (X0 §5 freeze).

Same contract as api-delpi's ``require_s2s_service``: the caller presents
a Keycloak client-credentials JWT in ``X-Delpi-Service-Authorization``;
``delpi_auth.ServiceTokenValidator`` validates signature, issuer,
audience and client allowlist. No user-JWT authority, no shared-token
fallback, fail-closed on any validator failure.

The validated identity is stored in ``g.service_identity`` — routes use
its ``client_id`` as the rate-limit ``consumer`` dimension.
"""

from __future__ import annotations

import logging
import threading
from functools import wraps
from typing import Iterable

from flask import g, jsonify, request

from delpi_auth.service_contract import extract_service_authorization
from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceAuthError,
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
    ServiceValidatorUnavailableError,
)
from delpi_auth.service_token_validator import ServiceTokenValidator

logger = logging.getLogger("external-data-api.s2s")

_validator_lock = threading.Lock()
_shared_validator: ServiceTokenValidator | None = None


def _validator() -> ServiceTokenValidator:
    global _shared_validator
    if _shared_validator is None:
        with _validator_lock:
            if _shared_validator is None:
                _shared_validator = ServiceTokenValidator.from_env()
    return _shared_validator


def _deny(status: int, code: str, detail: str):
    return jsonify({"detail": detail, "code": code}), status


def require_s2s_service(
    *, allowed_clients: Iterable[str] | None = None,
):
    """Strict individual-S2S authentication — nothing else authorizes."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = extract_service_authorization(request.headers)
            if not token:
                return _deny(
                    401, "unauthorized", "Service authentication required"
                )
            try:
                identity = _validator().validate(
                    token, allowed_clients=allowed_clients
                )
            except (
                ServiceAuthConfigError,
                ServiceValidatorUnavailableError,
            ) as exc:
                logger.error("s2s_unavailable code=%s", exc.code)
                return _deny(
                    503,
                    "service_unavailable",
                    "Service authentication unavailable",
                )
            except (ServiceClientDeniedError, ServiceScopeDeniedError) as exc:
                logger.info("s2s_denied code=%s", exc.code)
                return _deny(403, "forbidden", "Forbidden")
            except ServiceAuthError as exc:
                logger.info("s2s_denied code=%s", exc.code)
                return _deny(401, "unauthorized", "Invalid service authorization")

            g.service_identity = identity
            return fn(*args, **kwargs)

        return wrapper

    return decorator
