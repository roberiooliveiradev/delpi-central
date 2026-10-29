# app/interface/http/routes/engineering/lmp_facts_router.py
"""Facts contract F-LMP-01..04 (doc 33 — ENGINEERING.LMP.G1/G2).

Extração oficial de fatos LMP para a engineering-api executar as regras de
negócio (owner-alvo). Sem classificação de status/nível/prazo/KPI e sem
enriquecimento de metas — esses resultados pertencem aos respectivos owners.

AuthZ: ``require_s2s_or_any_permission`` — Bearer humano com permissão LMP
(contrato funcional existente) OU credencial S2S estrita
(``X-Delpi-Service-Authorization`` + escopo ``engineering-facts.read`` +
client allowlist). O token interno compartilhado nunca autoriza; se o S2S
não estiver provisionado, a validação falha fechada (503/401/403).
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Body, Path, Query
from pydantic import BaseModel, Field, field_validator

from app.application.security.api_delpi_permissions import ENGINEERING_LMP_ACCESS
from app.composition.engineering_composer import (
    build_engineering_get_lmp_fact_use_case,
    build_engineering_get_lmp_facts_history_use_case,
    build_engineering_get_lmp_pi_counts_use_case,
    build_engineering_list_lmp_facts_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata import (
    LMP_FACT_DETAIL,
    LMP_FACT_HISTORY_EVENTS,
    LMP_FACT_HISTORY_FLOW,
    LMP_FACT_LIST,
    LMP_PI_COUNTS,
)
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.period_query_params import (
    END_DATE_QUERY,
    LEGACY_DATE_END_QUERY,
    LEGACY_DATE_START_QUERY,
    START_DATE_QUERY,
    resolve_period_dates,
)
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    LMP_LISTING_TYPE_QUERY,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.engineering.lmp_route_helpers import (
    build_get_lmp_history_request,
    build_get_lmp_request,
    build_list_lmp_request,
)
from app.interface.http.s2s_service_access import require_s2s_or_any_permission
from app.utils.logger import log_error

router = APIRouter(
    prefix="/lmps/facts",
    tags=["Engenharia — LMP Facts"],
)

FACTS_S2S_REQUIRED_SCOPES = ("engineering-facts.read",)
FACTS_S2S_ALLOWED_CLIENTS = ("engineering-api",)


def _facts_guard(fn):
    return require_s2s_or_any_permission(
        ENGINEERING_LMP_ACCESS,
        required_scopes=FACTS_S2S_REQUIRED_SCOPES,
        allowed_clients=FACTS_S2S_ALLOWED_CLIENTS,
    )(fn)


class LmpFactOvKey(BaseModel):
    branch: str = Field(..., min_length=1, max_length=8)
    sale_number: str = Field(..., min_length=1, max_length=20)
    revision: str = Field(..., min_length=1, max_length=8)

    @field_validator("branch", "sale_number", "revision", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return str(value).strip() if value is not None else value


class LmpPiCountsBody(BaseModel):
    ovs: list[LmpFactOvKey] = Field(..., min_length=1, max_length=500)
    branch: Optional[str] = Field(default=None, max_length=8)


@router.get("", **LMP_FACT_LIST)
@_facts_guard
def list_lmp_facts_route(
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    listing_type: Optional[str] = LMP_LISTING_TYPE_QUERY(),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = PAGE_SIZE_QUERY("page_50_500"),
    include_qtd_pi: Optional[bool] = Query(
        None,
        description="Incluir contagem de PI via BOM (mais lento). Padrão: false.",
    ),
):
    try:
        start_date, end_date = resolve_period_dates(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        dto = build_list_lmp_request(
            date_start=start_date,
            date_end=end_date,
            branch=branch,
            listing_type=listing_type,
            page=page,
            page_size=page_size,
            include_qtd_pi=include_qtd_pi,
        )
        result = build_engineering_list_lmp_facts_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id="list_lmp_facts",
            message="Fatos de LMPs carregados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar fatos LMP: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao listar fatos LMP: {exc}")
        return error_response("Erro interno ao listar fatos de LMPs.", status_code=500)


@router.post("/pi-counts", **LMP_PI_COUNTS)
@_facts_guard
def get_lmp_pi_counts_route(body: LmpPiCountsBody = Body(...)):
    try:
        result = build_engineering_get_lmp_pi_counts_use_case().execute(
            ov_keys=[key.model_dump() for key in body.ovs],
            requested_branch=body.branch,
        )
        return api_delpi_success(
            result,
            operation_id="get_lmp_pi_counts",
            message="Contagens de PI carregadas com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação nas contagens PI: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao consultar contagens PI: {exc}")
        return error_response("Erro interno ao consultar contagens de PI.", status_code=500)


@router.get("/{sale_number}/history/events", **LMP_FACT_HISTORY_EVENTS)
@_facts_guard
def get_lmp_facts_history_events_route(
    sale_number: Annotated[str, Path(description="Número da OV")],
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    revision: Optional[str] = Query(None, description="Revisão específica da OV."),
):
    return _facts_history_route(
        sale_number,
        view="events",
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
        branch=branch,
        revision=revision,
        operation_id="get_lmp_facts_history_events",
    )


@router.get("/{sale_number}/history/flow", **LMP_FACT_HISTORY_FLOW)
@_facts_guard
def get_lmp_facts_history_flow_route(
    sale_number: Annotated[str, Path(description="Número da OV")],
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    revision: Optional[str] = Query(None, description="Revisão específica da OV."),
):
    return _facts_history_route(
        sale_number,
        view="flow",
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
        branch=branch,
        revision=revision,
        operation_id="get_lmp_facts_history_flow",
    )


def _facts_history_route(
    sale_number: str,
    *,
    view: str,
    start_date: Optional[str],
    end_date: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
    branch: Optional[str],
    revision: Optional[str],
    operation_id: str,
):
    try:
        start_date, end_date = resolve_period_dates(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        dto = build_get_lmp_history_request(
            sale_number,
            date_start=start_date,
            date_end=end_date,
            branch=branch,
            revision=revision,
        )
        result = build_engineering_get_lmp_facts_history_use_case().execute(
            dto,
            view=view,
        )
        return api_delpi_success(
            result,
            operation_id=operation_id,
            message="Histórico de fatos da LMP carregado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação no histórico de fatos LMP: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao consultar histórico de fatos LMP: {exc}")
        return error_response(
            "Erro interno ao consultar histórico de fatos.", status_code=500
        )


@router.get("/{sale_number}", **LMP_FACT_DETAIL)
@_facts_guard
def get_lmp_fact_route(
    sale_number: Annotated[str, Path(description="Número da OV")],
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    include: Optional[str] = Query(
        None,
        description="Extras opcionais separados por vírgula: products, history.",
    ),
):
    try:
        start_date, end_date = resolve_period_dates(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        dto = build_get_lmp_request(
            sale_number,
            date_start=start_date,
            date_end=end_date,
            branch=branch,
        )
        result = build_engineering_get_lmp_fact_use_case().execute(
            dto,
            include=include,
        )
        return api_delpi_success(
            result,
            operation_id="get_lmp_fact",
            message="Fato da LMP carregado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao consultar fato LMP: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao consultar fato LMP: {exc}")
        return error_response("Erro interno ao consultar fato de LMP.", status_code=500)
