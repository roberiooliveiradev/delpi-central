"""Individual service-to-service authentication for api-delpi routes.

Migrates service authorization off the shared internal token: the caller
presents a Keycloak client-credentials JWT in
``X-Delpi-Service-Authorization`` and api-delpi validates signature, issuer,
dedicated audience, technical client allowlist and operation scope through
``delpi_auth.ServiceTokenValidator``.

The request still carries the end-user Bearer in ``Authorization`` — the
middleware resolves the user principal normally and that principal remains
the delegated actor (audit, ``codusr`` resolution). ``X-Delpi-Caller-App``
stays telemetry metadata and is never identity proof.
"""

from __future__ import annotations

import inspect
import logging
from functools import wraps
from typing import Iterable

from fastapi import HTTPException

from delpi_auth.authorization import require_any_permission
from delpi_auth.context_resolver import resolve_user_context
from delpi_auth.service_contract import extract_service_authorization
from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceAuthError,
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
)
from delpi_auth.service_identity import ServiceIdentity
from delpi_auth.service_token_validator import ServiceTokenValidator

from app.infrastructure.observability.request_context import get_request

logger = logging.getLogger("api-delpi.s2s")


def _extract_service_token() -> str | None:
    request = get_request()
    if request is None:
        return None
    try:
        return extract_service_authorization(request.headers)
    except ValueError as exc:
        raise HTTPException(
            status_code=401, detail="Invalid service authorization"
        ) from exc


def _require_service_identity(
    token: str,
    *,
    required_scopes: Iterable[str],
    allowed_clients: Iterable[str] | None,
) -> ServiceIdentity:
    try:
        validator = ServiceTokenValidator.from_env()
        identity = validator.validate(
            token,
            required_scopes=required_scopes,
            allowed_clients=allowed_clients,
        )
    except ServiceAuthConfigError as exc:
        logger.error("s2s_config_missing code=%s", exc.code)
        raise HTTPException(
            status_code=503, detail="Service authentication unavailable"
        ) from exc
    except (ServiceClientDeniedError, ServiceScopeDeniedError) as exc:
        logger.info("s2s_denied code=%s", exc.code)
        raise HTTPException(status_code=403, detail="Forbidden") from exc
    except ServiceAuthError as exc:
        logger.info("s2s_denied code=%s", exc.code)
        raise HTTPException(
            status_code=401, detail="Invalid service authorization"
        ) from exc

    request = get_request()
    if request is not None:
        request.state.service_identity = identity
    return identity


def require_s2s_service(
    *,
    required_scopes: Iterable[str] = (),
    allowed_clients: Iterable[str] | None = None,
):
    """Strict individual-S2S authentication — the shared token never authorizes."""

    def decorator(fn):
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                token = _extract_service_token()
                if token is None:
                    raise HTTPException(
                        status_code=401, detail="Service authentication required"
                    )
                _require_service_identity(
                    token,
                    required_scopes=required_scopes,
                    allowed_clients=allowed_clients,
                )
                return await fn(*args, **kwargs)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            token = _extract_service_token()
            if token is None:
                raise HTTPException(
                    status_code=401, detail="Service authentication required"
                )
            _require_service_identity(
                token,
                required_scopes=required_scopes,
                allowed_clients=allowed_clients,
            )
            return fn(*args, **kwargs)

        return sync_wrapper

    return decorator


def require_s2s_or_any_permission(
    permission_codes,
    *,
    required_scopes: Iterable[str] = (),
    allowed_clients: Iterable[str] | None = None,
):
    """S2S credential for service callers; user permission for direct callers.

    When the S2S header is present the service credential is validated
    strictly — a wrong client or scope is denied, not silently degraded to
    the user path. When it is absent, a legacy service principal
    (``principal_type == "service"`` minted by the shared internal token) is
    denied outright: the shared token never authorizes this surface.
    """

    def decorator(fn):
        guarded = require_any_permission(permission_codes)(fn)

        def _dispatch(*args, **kwargs):
            token = _extract_service_token()
            if token is not None:
                _require_service_identity(
                    token,
                    required_scopes=required_scopes,
                    allowed_clients=allowed_clients,
                )
                return fn(*args, **kwargs)

            user = resolve_user_context()
            if user is not None and getattr(user, "principal_type", None) == "service":
                logger.info("s2s_denied code=LEGACY_SERVICE_TOKEN")
                raise HTTPException(status_code=403, detail="Forbidden")
            return guarded(*args, **kwargs)

        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                token = _extract_service_token()
                if token is not None:
                    _require_service_identity(
                        token,
                        required_scopes=required_scopes,
                        allowed_clients=allowed_clients,
                    )
                    return await fn(*args, **kwargs)

                user = resolve_user_context()
                if user is not None and getattr(user, "principal_type", None) == "service":
                    logger.info("s2s_denied code=LEGACY_SERVICE_TOKEN")
                    raise HTTPException(status_code=403, detail="Forbidden")
                return await guarded(*args, **kwargs)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            return _dispatch(*args, **kwargs)

        return sync_wrapper

    return decorator
