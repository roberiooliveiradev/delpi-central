"""Create Protheus supplier via REST — identity from Core; write behind feature gate."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from app.application.services.integrations.protheus_path_resolver import (
    resolve_protheus_rest_config,
)
from app.application.services.integrations.protheus_supplier_create_payload import (
    build_upstream_create_body,
    normalize_supplier_fields,
    validate_codusr,
)
from app.application.services.integrations.protheus_token_service import (
    ProtheusTokenService,
)
from app.config import settings
from app.domain.integrations.protheus_rest import ProtheusRestError
from app.infrastructure.gateways.core_protheus_identity_gateway import (
    CoreProtheusIdentityGateway,
)
from app.infrastructure.gateways.protheus_rest_gateway import ProtheusRestGateway
from app.infrastructure.persistence.intranet.protheus_integration_params_repository import (
    ProtheusIntegrationParamsRepository,
)
from app.utils.logger import log_info


class CreateProtheusRestSupplierUseCase:
    def __init__(
        self,
        *,
        params_repository: ProtheusIntegrationParamsRepository,
        token_service: ProtheusTokenService,
        gateway: ProtheusRestGateway,
        identity_gateway: CoreProtheusIdentityGateway,
    ) -> None:
        self._params_repository = params_repository
        self._token_service = token_service
        self._gateway = gateway
        self._identity_gateway = identity_gateway

    def execute(
        self,
        *,
        actor_user_id: UUID,
        fornecedor: Mapping[str, Any],
    ) -> dict[str, Any]:
        normalized = normalize_supplier_fields(fornecedor)
        codusr = self._resolve_codusr(actor_user_id)

        if not settings.PROTHEUS_SUPPLIER_CREATE_ENABLED:
            log_info(
                "protheus_supplier_create_blocked_by_feature_gate "
                f"actor_user_id={actor_user_id}"
            )
            raise ProtheusRestError(
                "Criação de fornecedor Protheus desabilitada neste ambiente "
                "(PROTHEUS_SUPPLIER_CREATE_ENABLED=false). "
                "Nenhuma escrita foi enviada ao ERP.",
                code="PROTHEUS_SUPPLIER_CREATE_DISABLED",
                status_code=503,
                recoverable=False,
            )

        body = build_upstream_create_body(codusr=codusr, fornecedor=normalized)
        raw = self._params_repository.load_raw_params()
        config = resolve_protheus_rest_config(raw)
        token = self._token_service.get_valid_token(config)

        try:
            upstream = self._gateway.create_supplier(
                config, body=body, access_token=token
            )
        except ProtheusRestError as exc:
            # Never auto-retry the write POST (non-idempotent). Invalidate stale
            # token cache so the next authorized attempt can refresh OAuth.
            if exc.code == "PROTHEUS_TOKEN_INVALID":
                self._token_service.invalidate()
            raise

        log_info(
            "protheus_supplier_create_submitted "
            f"actor_user_id={actor_user_id} "
            f"creation_confirmed={upstream.get('creation_confirmed')}"
        )
        return {
            "codusr": codusr,
            "supplier_store": normalized.get("supplier_store"),
            **upstream,
        }

    def _resolve_codusr(self, actor_user_id: UUID) -> str:
        mapping = self._identity_gateway.get_identity_for_user(actor_user_id)
        status = str(mapping.get("mapping_status") or "").strip().lower()
        if status == "ambiguous":
            raise ProtheusRestError(
                "Identidade Protheus ambígua; resolva o vínculo no Core antes de criar fornecedor.",
                code="PROTHEUS_IDENTITY_AMBIGUOUS",
                status_code=422,
                recoverable=False,
            )
        if status != "mapped":
            raise ProtheusRestError(
                "Usuário sem vínculo Protheus mapeado no Core.",
                code="PROTHEUS_IDENTITY_UNMAPPED",
                status_code=422,
                recoverable=False,
            )
        if not bool(mapping.get("verified")):
            raise ProtheusRestError(
                "Identidade Protheus do usuário não está verificada.",
                code="PROTHEUS_IDENTITY_NOT_VERIFIED",
                status_code=422,
                recoverable=False,
            )
        protheus_user_id = str(mapping.get("protheus_user_id") or "").strip()
        if not protheus_user_id:
            raise ProtheusRestError(
                "Vínculo Protheus sem USR_ID.",
                code="PROTHEUS_IDENTITY_UNMAPPED",
                status_code=422,
                recoverable=False,
            )
        # Equivalence codusr ≡ USR_ID is TO_INVENTORY; format gate is 6 digits.
        return validate_codusr(protheus_user_id)
