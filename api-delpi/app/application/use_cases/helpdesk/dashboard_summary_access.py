"""Who may ask the Helpdesk summary for the institutional reader.

A personal caller keeps their GLPI OAuth session. A service caller is denied
unless it presents the canonical S2S identity ``tv-dashboard-api`` with scope
``helpdesk.dashboard.read``. ``is_superadmin`` on the shared internal token
is not a grant.
"""

from __future__ import annotations

from delpi_auth.service_contract import extract_service_authorization
from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceAuthError,
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
)
from delpi_auth.service_identity import ServiceIdentity
from delpi_auth.service_token_validator import ServiceTokenValidator

DASHBOARD_READER_SCOPE = "helpdesk.dashboard.read"
DASHBOARD_READER_CLIENT = "tv-dashboard-api"


class DashboardSummaryAccessError(Exception):
    def __init__(self, message: str, *, status_code: int, code: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


def load_summary_service_identity(headers, *, principal_type: str | None):
    try:
        token = extract_service_authorization(headers)
    except ValueError as exc:
        raise DashboardSummaryAccessError(
            "Credencial de serviço inválida.",
            status_code=401,
            code="institutional_credential_invalid",
        ) from exc
    if token is None or principal_type != "service":
        return None
    try:
        return ServiceTokenValidator.from_env().validate(
            token,
            required_scopes=(DASHBOARD_READER_SCOPE,),
            allowed_clients=(DASHBOARD_READER_CLIENT,),
        )
    except ServiceAuthConfigError as exc:
        raise DashboardSummaryAccessError(
            "Leitura institucional do Helpdesk indisponível.",
            status_code=503,
            code="institutional_reader_unavailable",
        ) from exc
    except (ServiceClientDeniedError, ServiceScopeDeniedError) as exc:
        raise DashboardSummaryAccessError(
            "Leitura institucional do Helpdesk não autorizada.",
            status_code=403,
            code="institutional_read_denied",
        ) from exc
    except ServiceAuthError as exc:
        raise DashboardSummaryAccessError(
            "Credencial de serviço inválida.",
            status_code=401,
            code="institutional_credential_invalid",
        ) from exc


def service_summary_is_denied(user, identity: ServiceIdentity | None) -> bool:
    """True when this caller is a service and may not use the institutional reader."""
    if getattr(user, "principal_type", None) != "service":
        return False
    if identity is None:
        return True
    return identity.client_id != DASHBOARD_READER_CLIENT or not identity.has_scope(
        DASHBOARD_READER_SCOPE
    )
