from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Path, Query
from pydantic import BaseModel, Field, field_validator

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    ENGINEERING_LMP_ACCESS,
    ENGINEERING_LMP_NC_WRITE,
)
from app.composition.engineering_composer import (
    build_create_lmp_nonconformity_use_case,
    build_delete_lmp_nonconformity_use_case,
    build_get_lmp_nonconformity_use_case,
    build_list_lmp_nonconformities_use_case,
    build_update_lmp_nonconformity_use_case,
)
from app.core.responses import error_response, not_found_response
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.interface.http.openapi_agent_metadata import (
    LMP_NONCONFORMITIES_LIST,
    LMP_NONCONFORMITY_BY_ID,
    LMP_NONCONFORMITY_CREATE,
    LMP_NONCONFORMITY_DELETE,
    LMP_NONCONFORMITY_UPDATE,
)
from app.interface.http.period_query_params import (
    END_DATE_QUERY,
    LEGACY_DATE_END_QUERY,
    LEGACY_DATE_START_QUERY,
    START_DATE_QUERY,
    resolve_period_dates,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/lmps/nonconformities",
    tags=["Engenharia — NC LMP"],
)

_STATUS_PATTERN = "^(open|in_progress|done)$"
_STATUS_ENUM = ["open", "in_progress", "done"]
_DATE_PATTERN = r"^(\d{4}-\d{2}-\d{2})?$"


class LmpNcProductBody(BaseModel):
    product_code: str = Field(..., min_length=1, max_length=60)
    product_description: str | None = Field(default=None, max_length=255)

    @field_validator("product_code", "product_description", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class LmpNonconformityBody(BaseModel):
    """Body de create/update — ``registered_at`` é definido pelo servidor no create."""

    status: str = Field(
        default="open",
        pattern=_STATUS_PATTERN,
        json_schema_extra={"enum": _STATUS_ENUM},
    )
    sale_number: str | None = Field(
        default=None,
        max_length=20,
        description="Número da OV (= identificador da LMP).",
    )
    customer_name: str | None = Field(default=None, max_length=200)
    launch_date: str | None = Field(
        default=None,
        max_length=10,
        pattern=_DATE_PATTERN,
        description="Data de lançamento (YYYY-MM-DD), snapshot editável.",
    )
    last_revision_date: str | None = Field(
        default=None,
        max_length=10,
        pattern=_DATE_PATTERN,
        description="Data da última revisão (YYYY-MM-DD), snapshot editável.",
    )
    executed_by: str | None = Field(default=None, max_length=200)
    released_by: str | None = Field(default=None, max_length=200)
    defect_description: str | None = Field(
        default=None,
        description="Problema identificado.",
    )
    corrective_actions: str | None = None
    technical_opinion: str | None = None
    products: list[LmpNcProductBody] = Field(default_factory=list)

    @field_validator(
        "sale_number",
        "customer_name",
        "launch_date",
        "last_revision_date",
        "executed_by",
        "released_by",
        "defect_description",
        "corrective_actions",
        "technical_opinion",
        mode="before",
    )
    @classmethod
    def empty_str_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("products", mode="before")
    @classmethod
    def normalize_products(cls, value: object) -> list:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("products deve ser uma lista")
        return value


def _current_user_label() -> str | None:
    user = get_current_user()
    if user is None:
        return None
    for attr in ("email", "name", "id"):
        value = getattr(user, attr, None)
        if value:
            return str(value)[:120]
    return None


def _products_payload(body: LmpNonconformityBody) -> list[dict[str, str | None]]:
    return [
        {
            "product_code": item.product_code,
            "product_description": item.product_description,
        }
        for item in body.products
    ]


@router.get("", **LMP_NONCONFORMITIES_LIST)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def list_lmp_nonconformities(
    status: Optional[str] = Query(
        None,
        pattern=_STATUS_PATTERN,
        json_schema_extra={"enum": _STATUS_ENUM},
        description="Filtro por status (open, in_progress, done).",
    ),
    sale_number: Optional[str] = Query(
        None,
        max_length=20,
        description="Filtro parcial pela OV (= LMP).",
    ),
    customer_name: Optional[str] = Query(None, max_length=200),
    product_code: Optional[str] = Query(
        None,
        max_length=60,
        description="Filtro por código de produto/material nas linhas.",
    ),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    try:
        start_date, end_date = resolve_period_dates(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        data = build_list_lmp_nonconformities_use_case().execute(
            status=status,
            sale_number=sale_number,
            customer_name=customer_name,
            product_code=product_code,
            date_start=start_date,
            date_end=end_date,
            page=page,
            page_size=page_size,
        )
        return api_delpi_success(
            data,
            operation_id="list_lmp_nonconformities",
            message="Não conformidades LMP listadas com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Validação ao listar NCs LMP: {exc}")
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar NCs LMP: {exc}")
        return error_response(
            "Erro interno ao listar não conformidades.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao listar NCs LMP: {exc}")
        return error_response(
            "Erro interno ao listar não conformidades.",
            status_code=500,
        )


@router.get("/{record_id}", **LMP_NONCONFORMITY_BY_ID)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def get_lmp_nonconformity(
    record_id: Annotated[UUID, Path(description="ID da não conformidade")],
):
    try:
        data = build_get_lmp_nonconformity_use_case().execute(str(record_id))
        if data is None:
            return not_found_response("Não conformidade não encontrada.")
        return api_delpi_success(
            data,
            operation_id="get_lmp_nonconformity",
            message="Não conformidade LMP carregada com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao buscar NC LMP: {exc}")
        return error_response(
            "Erro interno ao buscar não conformidade.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao buscar NC LMP: {exc}")
        return error_response(
            "Erro interno ao buscar não conformidade.",
            status_code=500,
        )


@router.post("", **LMP_NONCONFORMITY_CREATE)
@require_any_permission(ENGINEERING_LMP_NC_WRITE)
def create_lmp_nonconformity(body: LmpNonconformityBody = Body(...)):
    try:
        data = build_create_lmp_nonconformity_use_case().execute(
            status=body.status,
            sale_number=body.sale_number,
            customer_name=body.customer_name,
            launch_date=body.launch_date,
            last_revision_date=body.last_revision_date,
            executed_by=body.executed_by,
            released_by=body.released_by,
            defect_description=body.defect_description,
            corrective_actions=body.corrective_actions,
            technical_opinion=body.technical_opinion,
            products=_products_payload(body),
            created_by=_current_user_label(),
        )
        return api_delpi_success(
            data,
            operation_id="create_lmp_nonconformity",
            message="Não conformidade LMP criada com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao criar NC LMP: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro inesperado ao criar NC LMP: {exc}")
        return error_response(
            "Erro interno ao criar não conformidade.",
            status_code=500,
        )


@router.put("/{record_id}", **LMP_NONCONFORMITY_UPDATE)
@require_any_permission(ENGINEERING_LMP_NC_WRITE)
def update_lmp_nonconformity(
    record_id: Annotated[UUID, Path(description="ID da não conformidade")],
    body: LmpNonconformityBody = Body(...),
):
    try:
        data = build_update_lmp_nonconformity_use_case().execute(
            record_id=str(record_id),
            status=body.status,
            sale_number=body.sale_number,
            customer_name=body.customer_name,
            launch_date=body.launch_date,
            last_revision_date=body.last_revision_date,
            executed_by=body.executed_by,
            released_by=body.released_by,
            defect_description=body.defect_description,
            corrective_actions=body.corrective_actions,
            technical_opinion=body.technical_opinion,
            products=_products_payload(body),
            updated_by=_current_user_label(),
        )
        if data is None:
            return not_found_response("Não conformidade não encontrada.")
        return api_delpi_success(
            data,
            operation_id="update_lmp_nonconformity",
            message="Não conformidade LMP atualizada com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao atualizar NC LMP: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro inesperado ao atualizar NC LMP: {exc}")
        return error_response(
            "Erro interno ao atualizar não conformidade.",
            status_code=500,
        )


@router.delete("/{record_id}", **LMP_NONCONFORMITY_DELETE)
@require_any_permission(ENGINEERING_LMP_NC_WRITE)
def delete_lmp_nonconformity(
    record_id: Annotated[UUID, Path(description="ID da não conformidade")],
):
    try:
        deleted = build_delete_lmp_nonconformity_use_case().execute(str(record_id))
        if not deleted:
            return not_found_response("Não conformidade não encontrada.")
        return api_delpi_success(
            {"id": str(record_id), "deleted": True},
            operation_id="delete_lmp_nonconformity",
            message="Não conformidade LMP excluída com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao excluir NC LMP: {exc}")
        return error_response(
            "Erro interno ao excluir não conformidade.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao excluir NC LMP: {exc}")
        return error_response(
            "Erro interno ao excluir não conformidade.",
            status_code=500,
        )
