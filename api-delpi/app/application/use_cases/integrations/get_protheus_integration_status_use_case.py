"""Diagnose Protheus REST configuration, authentication and connectivity."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from app.application.services.integrations.protheus_path_resolver import (
    resolve_protheus_rest_config,
)
from app.application.services.integrations.protheus_token_service import (
    ProtheusTokenService,
)
from app.domain.integrations.protheus_rest import (
    ProtheusIntegrationStatus,
    ProtheusRestError,
)
from app.infrastructure.gateways.protheus_rest_gateway import ProtheusRestGateway
from app.infrastructure.persistence.intranet.protheus_integration_params_repository import (
    ProtheusIntegrationParamsRepository,
)

# Probe responses that prove the REST channel answered with a recognized outcome.
_CONNECTION_OK_CODES = frozenset({"PROTHEUS_SUPPLIER_NOT_FOUND"})


class GetProtheusIntegrationStatusUseCase:
    def __init__(
        self,
        *,
        params_repository: ProtheusIntegrationParamsRepository,
        token_service: ProtheusTokenService,
        gateway: ProtheusRestGateway,
        probe_supplier_id: str = "00000000",
    ) -> None:
        self._params_repository = params_repository
        self._token_service = token_service
        self._gateway = gateway
        self._probe_supplier_id = probe_supplier_id

    def execute(self) -> dict[str, Any]:
        configuration = "missing"
        authentication = "unavailable"
        connection = "unavailable"
        mismatch = False
        transport = "unknown"

        try:
            raw = self._params_repository.load_raw_params()
            config = resolve_protheus_rest_config(raw)
            configuration = "ok"
            mismatch = config.path_label_mismatch
            transport = _transport_label(config.base_url)
        except ProtheusRestError as exc:
            if exc.code in {"PROTHEUS_CONFIG_MISSING", "PROTHEUS_CONFIG_INVALID"}:
                configuration = "missing" if "MISSING" in exc.code else "invalid"
            else:
                configuration = "unavailable"
            return ProtheusIntegrationStatus(
                integration="protheus",
                configuration=configuration,
                authentication=authentication,
                connection=connection,
                config_path_label_mismatch=mismatch,
                transport=transport,
            ).to_dict()

        try:
            token = self._token_service.get_valid_token(config)
            authentication = "ok"
        except ProtheusRestError:
            authentication = "failed"
            return ProtheusIntegrationStatus(
                integration="protheus",
                configuration=configuration,
                authentication=authentication,
                connection=connection,
                config_path_label_mismatch=mismatch,
                transport=transport,
            ).to_dict()

        try:
            self._gateway.get_supplier(
                config,
                supplier_id=self._probe_supplier_id,
                access_token=token,
            )
            connection = "ok"
        except ProtheusRestError as exc:
            # Recognized business response (e.g. supplier 002) proves the channel.
            # Unexpected ERP/HTTP failures must not be reported as healthy.
            if exc.code in _CONNECTION_OK_CODES:
                connection = "ok"
            else:
                connection = "failed"

        return ProtheusIntegrationStatus(
            integration="protheus",
            configuration=configuration,
            authentication=authentication,
            connection=connection,
            config_path_label_mismatch=mismatch,
            transport=transport,
        ).to_dict()


def _transport_label(base_url: str) -> str:
    scheme = (urlparse(base_url).scheme or "").lower()
    if scheme == "https":
        return "https"
    if scheme == "http":
        return "http_cleartext"
    return "unknown"
