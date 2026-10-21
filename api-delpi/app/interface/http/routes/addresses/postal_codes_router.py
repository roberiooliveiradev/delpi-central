"""Consulta de endereço por CEP — capacidade compartilhada (INT-CEP-01).

Owner da integração externa: api-delpi (ViaCEP → BrasilAPI). Consumidores
são BFFs autorizados via credencial S2S individual — a rota nunca é
anônima e MFEs não a chamam diretamente. A conciliação IBGE→CC2 permanece
no consumidor TOTVS; este contrato devolve o IBGE de 7 dígitos do provider.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.application.use_cases.addresses.lookup_postal_address_use_case import (
    LookupPostalAddressUseCase,
)
from app.core.responses import error_response
from app.domain.addresses.postal_address import PostalAddressProviderError
from app.infrastructure.gateways.postal_address.postal_address_providers import (
    default_postal_address_providers,
)
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.s2s_service_access import require_s2s_service
from app.utils.logger import log_error

router = APIRouter(
    prefix="/addresses/postal-codes",
    tags=["Addresses — Postal codes"],
)

_ALLOWED_BFF_CLIENTS = ("supplies-api",)


@router.get(
    "/{postal_code}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "lookup_postal_address",
        path="/addresses/postal-codes/{postal_code}",
    ),
)
@require_s2s_service(allowed_clients=_ALLOWED_BFF_CLIENTS)
def lookup_postal_address(postal_code: str):
    """operationId: lookup_postal_address — proposta de endereço por CEP."""
    try:
        result = LookupPostalAddressUseCase(
            providers=default_postal_address_providers()
        ).execute(postal_code)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PostalAddressProviderError as exc:
        log_error(f"Falha de provider na consulta de CEP: {exc}")
        if exc.status_code is None:
            return error_response(
                "Serviço de consulta de CEP indisponível.",
                status_code=504,
            )
        return error_response(
            "Erro ao consultar o serviço de CEP.",
            status_code=502,
        )
    except Exception as exc:
        log_error(f"Erro ao consultar CEP: {exc}")
        return error_response(
            "Erro interno ao consultar o CEP.",
            status_code=500,
        )
    return api_delpi_success(
        result.to_dict(),
        operation_id="lookup_postal_address",
        message="Consulta de CEP concluída.",
    )
