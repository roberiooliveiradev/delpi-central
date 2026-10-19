"""Fetch a Protheus supplier by 8-digit code+store identifier via REST."""

from __future__ import annotations

import re
from typing import Any

from app.application.services.integrations.protheus_path_resolver import (
    resolve_protheus_rest_config,
)
from app.application.services.integrations.protheus_token_service import (
    ProtheusTokenService,
)
from app.domain.integrations.protheus_rest import (
    SUPPLIER_ID_PATTERN,
    ProtheusRestError,
)
from app.infrastructure.gateways.protheus_rest_gateway import ProtheusRestGateway
from app.infrastructure.persistence.intranet.protheus_integration_params_repository import (
    ProtheusIntegrationParamsRepository,
)


class GetProtheusRestSupplierUseCase:
    def __init__(
        self,
        *,
        params_repository: ProtheusIntegrationParamsRepository,
        token_service: ProtheusTokenService,
        gateway: ProtheusRestGateway,
    ) -> None:
        self._params_repository = params_repository
        self._token_service = token_service
        self._gateway = gateway

    def execute(self, supplier_id: str) -> Any:
        normalized = str(supplier_id or "").strip()
        if not re.fullmatch(SUPPLIER_ID_PATTERN, normalized):
            raise ProtheusRestError(
                "Identificador de fornecedor inválido. Informe exatamente 8 dígitos "
                "(6 do código + 2 da loja).",
                code="PROTHEUS_SUPPLIER_ID_INVALID",
                status_code=422,
                recoverable=False,
            )

        raw = self._params_repository.load_raw_params()
        config = resolve_protheus_rest_config(raw)
        token = self._token_service.get_valid_token(config)

        try:
            return self._gateway.get_supplier(
                config,
                supplier_id=normalized,
                access_token=token,
            )
        except ProtheusRestError as exc:
            if exc.code != "PROTHEUS_TOKEN_INVALID":
                raise
            self._token_service.invalidate()
            token = self._token_service.get_valid_token(config)
            return self._gateway.get_supplier(
                config,
                supplier_id=normalized,
                access_token=token,
            )
