"""Fail-closed gate for the institutional Helpdesk summary reader.

The shared internal token and ``is_superadmin`` do not grant this read.
A service identity must carry the scope ``helpdesk.dashboard.read`` for the
client ``tv-dashboard-api``. The GLPI credential is a dedicated user token,
never the upload or profile-sync token. An empty entity allowlist, or the
root entity ``0`` without an explicit override, keeps the reader unavailable.
Listing ``0`` means tickets whose entity id is ``0``. It does not include
child entities; those must appear as their own ids. Any other id is dropped.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from delpi_auth.service_contract import extract_service_authorization
from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceAuthError,
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
)
from delpi_auth.service_identity import ServiceIdentity
from delpi_auth.service_token_validator import ServiceTokenValidator

from helpdesk_app.domain.errors import (
    InstitutionalCredentialInvalid,
    InstitutionalReadDenied,
    InstitutionalReaderUnavailable,
)

logger = logging.getLogger("helpdesk.dashboard_reader")

DASHBOARD_READER_SCOPE = "helpdesk.dashboard.read"
DASHBOARD_READER_CLIENT = "tv-dashboard-api"
LOGICAL_IDENTITY = "minha-delpi-dashboard-reader"


@dataclass(frozen=True)
class DashboardReaderConfig:
    enabled: bool
    app_token: str
    user_token: str
    entity_ids: tuple[int, ...]
    group_ids: tuple[int, ...]
    allow_root: bool
    legacy_user_token: str
    profile_sync_user_token: str


def _flag(name: str) -> bool:
    return str(os.getenv(name, "false") or "false").lower() in {"1", "true", "yes", "on"}


def _id_list(name: str) -> tuple[int, ...]:
    ids: list[int] = []
    for part in str(os.getenv(name, "") or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            value = int(part)
        except ValueError:
            continue
        if value >= 0 and value not in ids:
            ids.append(value)
    return tuple(ids)


def _entity_ids() -> tuple[int, ...]:
    primary = _id_list("GLPI_DASHBOARD_READER_ENTITY_IDS")
    if primary:
        return primary
    return _id_list("GLPI_DASHBOARD_READER_ALLOWED_ENTITIES")


def load_dashboard_reader_config() -> DashboardReaderConfig:
    return DashboardReaderConfig(
        enabled=_flag("GLPI_DASHBOARD_READER_ENABLED"),
        app_token=str(os.getenv("GLPI_DASHBOARD_READER_APP_TOKEN", "") or "").strip(),
        user_token=str(os.getenv("GLPI_DASHBOARD_READER_USER_TOKEN", "") or "").strip(),
        entity_ids=_entity_ids(),
        group_ids=_id_list("GLPI_DASHBOARD_READER_GROUP_IDS"),
        allow_root=_flag("GLPI_DASHBOARD_READER_ALLOW_ROOT"),
        legacy_user_token=str(os.getenv("GLPI_LEGACY_USER_TOKEN", "") or "").strip(),
        profile_sync_user_token=str(os.getenv("GLPI_PROFILE_SYNC_USER_TOKEN", "") or "").strip(),
    )


def reader_is_ready(config: DashboardReaderConfig) -> bool:
    if not config.enabled or not config.app_token or not config.user_token:
        return False
    reused = {config.legacy_user_token, config.profile_sync_user_token} - {""}
    if config.user_token in reused or config.app_token in reused:
        return False
    if not config.entity_ids:
        return False
    if 0 in config.entity_ids and not config.allow_root:
        return False
    return True


def load_dashboard_service_identity(request) -> ServiceIdentity | None:
    """Return a validated service identity, or None when the caller stays personal.

    A human principal cannot opt into the reader by sending the service header.
    """
    try:
        token = extract_service_authorization(request.headers)
    except ValueError as exc:
        raise InstitutionalCredentialInvalid("Credencial de serviço inválida.") from exc
    if token is None:
        return None
    user = getattr(request.state, "user", None)
    if getattr(user, "principal_type", None) != "service":
        return None
    try:
        return ServiceTokenValidator.from_env().validate(
            token,
            required_scopes=(DASHBOARD_READER_SCOPE,),
            allowed_clients=(DASHBOARD_READER_CLIENT,),
        )
    except ServiceAuthConfigError as exc:
        logger.info(
            "helpdesk_dashboard_reader decision=unavailable logical_identity=%s reason=s2s_config",
            LOGICAL_IDENTITY,
        )
        raise InstitutionalReaderUnavailable(
            "Leitura institucional do Helpdesk indisponível."
        ) from exc
    except (ServiceClientDeniedError, ServiceScopeDeniedError) as exc:
        raise InstitutionalReadDenied(
            "Leitura institucional do Helpdesk não autorizada."
        ) from exc
    except ServiceAuthError as exc:
        raise InstitutionalCredentialInvalid("Credencial de serviço inválida.") from exc


def classify_ticket_list(request) -> str:
    """personal | denied | unavailable | ready. Superadmin is not a grant."""
    identity = load_dashboard_service_identity(request)
    if identity is None:
        return "personal"
    if identity.client_id != DASHBOARD_READER_CLIENT or not identity.has_scope(DASHBOARD_READER_SCOPE):
        return "denied"
    config = load_dashboard_reader_config()
    decision = "ready" if reader_is_ready(config) else "unavailable"
    logger.info(
        "helpdesk_dashboard_reader decision=%s principal_type=service logical_identity=%s entities=%s groups=%s",
        decision,
        LOGICAL_IDENTITY,
        ",".join(str(item) for item in config.entity_ids),
        ",".join(str(item) for item in config.group_ids),
    )
    return decision
