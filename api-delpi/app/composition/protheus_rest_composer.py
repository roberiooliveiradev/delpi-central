"""Composition root — Protheus REST integration (read + gated supplier create)."""

from __future__ import annotations

from app.application.services.integrations.protheus_token_service import (
    ProtheusTokenService,
)
from app.application.use_cases.integrations.create_protheus_rest_supplier_use_case import (
    CreateProtheusRestSupplierUseCase,
)
from app.application.use_cases.integrations.update_protheus_rest_supplier_use_case import (
    UpdateProtheusRestSupplierUseCase,
)
from app.application.use_cases.integrations.get_protheus_integration_status_use_case import (
    GetProtheusIntegrationStatusUseCase,
)
from app.application.use_cases.integrations.get_protheus_rest_supplier_use_case import (
    GetProtheusRestSupplierUseCase,
)
from app.infrastructure.gateways.core_protheus_identity_gateway import (
    CoreProtheusIdentityGateway,
)
from app.infrastructure.gateways.protheus_rest_gateway import ProtheusRestGateway
from app.infrastructure.persistence.intranet.protheus_integration_params_repository import (
    ProtheusIntegrationParamsRepository,
)

_gateway: ProtheusRestGateway | None = None
_token_service: ProtheusTokenService | None = None
_identity_gateway: CoreProtheusIdentityGateway | None = None


def build_protheus_params_repository() -> ProtheusIntegrationParamsRepository:
    return ProtheusIntegrationParamsRepository()


def build_protheus_rest_gateway() -> ProtheusRestGateway:
    global _gateway
    if _gateway is None:
        _gateway = ProtheusRestGateway()
    return _gateway


def build_protheus_token_service() -> ProtheusTokenService:
    global _token_service
    if _token_service is None:
        _token_service = ProtheusTokenService(build_protheus_rest_gateway())
    return _token_service


def build_core_protheus_identity_gateway() -> CoreProtheusIdentityGateway:
    global _identity_gateway
    if _identity_gateway is None:
        _identity_gateway = CoreProtheusIdentityGateway()
    return _identity_gateway


def build_get_protheus_integration_status_use_case() -> GetProtheusIntegrationStatusUseCase:
    return GetProtheusIntegrationStatusUseCase(
        params_repository=build_protheus_params_repository(),
        token_service=build_protheus_token_service(),
        gateway=build_protheus_rest_gateway(),
    )


def build_get_protheus_rest_supplier_use_case() -> GetProtheusRestSupplierUseCase:
    return GetProtheusRestSupplierUseCase(
        params_repository=build_protheus_params_repository(),
        token_service=build_protheus_token_service(),
        gateway=build_protheus_rest_gateway(),
    )


def build_create_protheus_rest_supplier_use_case() -> CreateProtheusRestSupplierUseCase:
    return CreateProtheusRestSupplierUseCase(
        params_repository=build_protheus_params_repository(),
        token_service=build_protheus_token_service(),
        gateway=build_protheus_rest_gateway(),
        identity_gateway=build_core_protheus_identity_gateway(),
    )


def build_update_protheus_rest_supplier_use_case() -> UpdateProtheusRestSupplierUseCase:
    return UpdateProtheusRestSupplierUseCase(
        params_repository=build_protheus_params_repository(),
        token_service=build_protheus_token_service(),
        gateway=build_protheus_rest_gateway(),
        identity_gateway=build_core_protheus_identity_gateway(),
    )


def reset_protheus_rest_singletons_for_tests() -> None:
    """Test helper — clear process-local gateway/token singletons."""
    global _gateway, _token_service, _identity_gateway
    _gateway = None
    _token_service = None
    _identity_gateway = None
