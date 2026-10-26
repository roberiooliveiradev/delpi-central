"""Diagnose Protheus REST configuration, authentication and connectivity."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from app.application.services.integrations.protheus_path_resolver import (
    assert_protheus_write_target,
    resolve_protheus_rest_config,
)
from app.application.services.integrations.protheus_token_service import (
    ProtheusTokenService,
)
from app.config import settings
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

# Transport-level failures: the REST host never produced an HTTP response.
_TRANSPORT_FAILURE_CODES = frozenset({"PROTHEUS_TIMEOUT", "PROTHEUS_UNAVAILABLE"})

_ENVIRONMENT_LABELS = {"1": "production", "2": "homologation"}


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
        checked_at = datetime.now(timezone.utc).isoformat()
        environment = _ENVIRONMENT_LABELS.get(
            (settings.INTRANET_PARAMS_AMBIENTE or "").strip(), "unknown"
        )
        create_gate = (
            "enabled" if settings.PROTHEUS_SUPPLIER_CREATE_ENABLED else "disabled"
        )
        update_gate = (
            "enabled" if settings.PROTHEUS_SUPPLIER_UPDATE_ENABLED else "disabled"
        )

        def _status(**overrides: Any) -> dict[str, Any]:
            base: dict[str, Any] = {
                "integration": "protheus",
                "configuration": "unavailable",
                "authentication": "unavailable",
                "connection": "unavailable",
                "config_path_label_mismatch": False,
                "transport": "unknown",
                "checked_at": checked_at,
                "environment": environment,
                "connectivity": "not_checked",
                "authentication_http_status": None,
                "suppliers_read": "not_checked",
                "create_gate": create_gate,
                "update_gate": update_gate,
                "write_target_guard": "unverified",
                "write_validation": "not_tested",
                "overall": "unavailable",
            }
            base.update(overrides)
            return ProtheusIntegrationStatus(**base).to_dict()

        try:
            raw = self._params_repository.load_raw_params()
            config = resolve_protheus_rest_config(raw)
        except ProtheusRestError as exc:
            if exc.code in {"PROTHEUS_CONFIG_MISSING", "PROTHEUS_CONFIG_INVALID"}:
                configuration = "missing" if "MISSING" in exc.code else "invalid"
            else:
                configuration = "unavailable"
            return _status(configuration=configuration)

        guard = "ok"
        try:
            assert_protheus_write_target(
                config, settings.PROTHEUS_REST_EXPECTED_BASE_URL
            )
        except ProtheusRestError as exc:
            guard = (
                "mismatch"
                if exc.code == "PROTHEUS_REST_TARGET_MISMATCH"
                else "unverified"
            )

        shared = {
            "configuration": "ok",
            "config_path_label_mismatch": config.path_label_mismatch,
            "transport": _transport_label(config.base_url),
            "write_target_guard": guard,
        }

        try:
            token = self._token_service.get_valid_token(config)
        except ProtheusRestError as exc:
            # An HTTP answer (even 4xx) proves the host is reachable; transport
            # failures (timeout/unavailable/other) mean connectivity failed.
            if exc.code in _TRANSPORT_FAILURE_CODES or exc.upstream_status is None:
                return _status(
                    **shared,
                    connectivity="failed",
                    authentication="not_checked",
                    overall="unavailable",
                )
            return _status(
                **shared,
                connectivity="ok",
                authentication="failed",
                authentication_http_status=exc.upstream_status,
                overall="upstream_pending",
            )

        try:
            self._gateway.get_supplier(
                config,
                supplier_id=self._probe_supplier_id,
                access_token=token,
            )
            read_state = "ok"
            read_overall = "ready_for_attempt"
        except ProtheusRestError as exc:
            if exc.code in _CONNECTION_OK_CODES:
                read_state = "ok"
                read_overall = "ready_for_attempt"
            else:
                read_state = "failed"
                read_overall = (
                    "upstream_pending"
                    if exc.code == "PROTHEUS_TOKEN_INVALID"
                    else "unavailable"
                )

        overall = read_overall
        if read_state == "ok" and guard != "ok":
            # Ready only when the write-target pin also proves the destination.
            overall = "unavailable"

        return _status(
            **shared,
            connectivity="ok",
            authentication="ok",
            connection=read_state,
            suppliers_read=read_state,
            overall=overall,
        )


def _transport_label(base_url: str) -> str:
    scheme = (urlparse(base_url).scheme or "").lower()
    if scheme == "https":
        return "https"
    if scheme == "http":
        return "http_cleartext"
    return "unknown"
