from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Query
from fastapi.responses import Response

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import PROPOSTAS_COMERCIAIS_ACCESS
from app.composition.propostas_comerciais_composer import (
    build_generate_proposta_comercial_pdf_use_case,
    build_get_proposta_comercial_use_case,
    build_list_propostas_comerciais_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response, not_found_response
from app.domain.propostas_comerciais.exceptions import PropostaComercialNotFoundError
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.schemas.proposta_comercial_pdf_schemas import (
    PropostaComercialPdfExportRequest,
)
from app.utils.logger import log_error

router = APIRouter(
    prefix="/propostas-comerciais",
    tags=["Propostas Comerciais"],
)


@router.get("", include_in_schema=False)
@router.get(
    "/",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_propostas_comerciais",
        path="/propostas-comerciais/",
    ),
)
@require_any_permission(PROPOSTAS_COMERCIAIS_ACCESS)
def list_propostas_comerciais_route(
    limit: int = Query(100, ge=1, le=200, description="Quantidade máxima de propostas recentes"),
):
    try:
        use_case = build_list_propostas_comerciais_use_case()
        result = use_case.execute(limit=limit)
        return api_delpi_success(
            result,
            operation_id="list_propostas_comerciais",
            message="Propostas comerciais listadas com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar propostas comerciais: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError:
        log_error("Erro de banco ao listar propostas comerciais.")
        return error_response(
            "Erro interno ao consultar propostas comerciais.",
            status_code=500,
            code="DATABASE_ERROR",
            recoverable=True,
        )
    except Exception as exc:
        log_error(f"Erro ao listar propostas comerciais: {exc}")
        return error_response(
            "Erro interno ao consultar propostas comerciais.",
            status_code=500,
        )


@router.get("/{proposta_interna}/pdf")
@require_any_permission(PROPOSTAS_COMERCIAIS_ACCESS)
def export_proposta_comercial_pdf_route(proposta_interna: str):
    return _export_proposta_comercial_pdf(proposta_interna)


@router.post("/{proposta_interna}/pdf")
@require_any_permission(PROPOSTAS_COMERCIAIS_ACCESS)
def export_proposta_comercial_pdf_with_overrides_route(
    proposta_interna: str,
    body: Annotated[PropostaComercialPdfExportRequest, Body(...)],
):
    return _export_proposta_comercial_pdf(
        proposta_interna,
        overrides=body.to_overrides_dict(),
    )


def _export_proposta_comercial_pdf(
    proposta_interna: str,
    *,
    overrides: dict | None = None,
):
    try:
        use_case = build_generate_proposta_comercial_pdf_use_case()
        pdf_bytes, filename = use_case.execute(proposta_interna, overrides=overrides)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except PropostaComercialNotFoundError as exc:
        return not_found_response(
            str(exc),
            code="PROPOSTA_COMERCIAL_NOT_FOUND",
        )
    except DatabaseConnectionError:
        log_error(f"Erro de banco ao gerar PDF da proposta comercial {proposta_interna}.")
        return error_response(
            "Erro interno ao gerar PDF da proposta comercial.",
            status_code=500,
            code="DATABASE_ERROR",
            recoverable=True,
        )
    except Exception as exc:
        log_error(f"Erro ao gerar PDF da proposta comercial {proposta_interna}: {exc}")
        return error_response(
            "Erro interno ao gerar PDF da proposta comercial.",
            status_code=500,
        )


@router.get(
    "/{proposta_interna}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_proposta_comercial",
        path="/propostas-comerciais/{proposta_interna}",
    ),
)
@require_any_permission(PROPOSTAS_COMERCIAIS_ACCESS)
def get_proposta_comercial_route(proposta_interna: str):
    try:
        use_case = build_get_proposta_comercial_use_case()
        result = use_case.execute(proposta_interna)
        return api_delpi_success(
            result,
            operation_id="get_proposta_comercial",
            message="Proposta comercial carregada com sucesso.",
        )
    except PropostaComercialNotFoundError as exc:
        return not_found_response(
            str(exc),
            code="PROPOSTA_COMERCIAL_NOT_FOUND",
        )
    except DatabaseConnectionError:
        log_error(f"Erro de banco ao consultar proposta comercial {proposta_interna}.")
        return error_response(
            "Erro interno ao consultar proposta comercial.",
            status_code=500,
            code="DATABASE_ERROR",
            recoverable=True,
        )
    except Exception as exc:
        log_error(f"Erro ao consultar proposta comercial {proposta_interna}: {exc}")
        return error_response(
            "Erro interno ao consultar proposta comercial.",
            status_code=500,
        )
