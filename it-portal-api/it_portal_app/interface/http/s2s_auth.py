"""Autenticação S2S individual para rotas de coletor (E4.S1).

Espelha a postura de ``external-data-api``: somente
``X-Delpi-Service-Authorization`` autoriza. Sem JWT de usuário, sem token
interno compartilhado e sem ``is_superadmin``.
"""

from __future__ import annotations

import logging
import threading
from typing import Iterable

from fastapi import HTTPException, Request

from delpi_auth.service_contract import extract_service_authorization
from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceAuthError,
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
    ServiceValidatorUnavailableError,
)
from delpi_auth.service_identity import ServiceIdentity
from delpi_auth.service_token_validator import ServiceTokenValidator

logger = logging.getLogger("it-portal-api.s2s")

OBSERVATIONS_INGEST_SCOPE = "it-portal.observations.ingest"

_validator_lock = threading.Lock()
_shared_validator: ServiceTokenValidator | None = None


class S2SHttpException(HTTPException):
    def __init__(self, status_code: int, detail: str, code: str) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = code


def _validator() -> ServiceTokenValidator:
    global _shared_validator
    if _shared_validator is None:
        with _validator_lock:
            if _shared_validator is None:
                _shared_validator = ServiceTokenValidator.from_env()
    return _shared_validator


def require_collector_identity(
    request: Request,
    *,
    required_scopes: Iterable[str] = (OBSERVATIONS_INGEST_SCOPE,),
    allowed_clients: Iterable[str] | None = None,
) -> ServiceIdentity:
    try:
        token = extract_service_authorization(request.headers)
    except ValueError as exc:
        raise S2SHttpException(
            status_code=401,
            detail="Invalid service authorization",
            code="S2S_TOKEN_INVALID",
        ) from exc
    if not token:
        raise S2SHttpException(
            status_code=401,
            detail="Service authentication required",
            code="S2S_TOKEN_MISSING",
        )
    try:
        identity = _validator().validate(
            token,
            required_scopes=required_scopes,
            allowed_clients=allowed_clients,
        )
    except (ServiceAuthConfigError, ServiceValidatorUnavailableError) as exc:
        logger.error("s2s_unavailable code=%s", exc.code)
        raise S2SHttpException(
            status_code=503,
            detail="Service authentication unavailable",
            code=exc.code,
        ) from exc
    except (ServiceClientDeniedError, ServiceScopeDeniedError) as exc:
        logger.info("s2s_denied code=%s", exc.code)
        raise S2SHttpException(status_code=403, detail="Forbidden", code=exc.code) from exc
    except ServiceAuthError as exc:
        logger.info("s2s_denied code=%s", exc.code)
        raise S2SHttpException(
            status_code=401,
            detail="Invalid service authorization",
            code=exc.code,
        ) from exc

    request.state.service_identity = identity
    return identity


def reset_validator_for_tests() -> None:
    """Limpa o singleton — somente testes."""
    global _shared_validator
    with _validator_lock:
        _shared_validator = None
