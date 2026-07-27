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
from app.interface.http.query_param_enums import BRANCH_QUERY_OPTIONAL
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/lmps/nonconformities",
    tags=["Engenharia — NC LMP"],
)

_STATUS_PATTERN = "^(open|in_progress|done)$"
_STATUS_ENUM = ["open", "in_progress", "done"]


class LmpNonconformityBody(BaseModel):
    registered_at: str = Field(
        ...,
        min_length=8,
        max_length=40,
        description="Data/hora do registro (ISO 8601).",
    )
    status: str = Field(
        default="open",
        pattern=_STATUS_PATTERN,
        json_schema_extra={"enum": _STATUS_ENUM},
    )
    sale_number: str | None = Field(default=None, max_length=20)
    branch_code: str | None = Field(
        default=None,
        pattern="^(01|02)$",
        json_schema_extra={"enum": ["01", "02"]},
    )
    material_code: str | None = Field(default=None, max_length=60)
    supplier_name: str | None = Field(default=None, max_length=200)
    purchase_order: str | None = Field(default=None, max_length=40)
    invoice_number: str | None = Field(default=None, max_length=40)
    qty_received: float | None = Field(default=None, ge=0)
    qty_accepted: float | None = Field(default=None, ge=0)
    qty_rejected: float | None = Field(default=None, ge=0)
    defect_description: str | None = None
    corrective_actions: str | None = None
    technical_opinion: str | None = None
    product_codes: list[str] = Field(default_factory=list)

    @field_validator(
        "sale_number",
        "branch_code",
        "material_code",
        "supplier_name",
        "purchase_order",
        "invoice_number",
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

    @field_validator("product_codes", mode="before")
    @classmethod
    def normalize_codes(cls, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("product_codes deve ser uma lista")
        out: list[str] = []
        for item in value:
            text = str(item or "").strip()
            if text:
                out.append(text)
        return out


def _current_user_label() -> str | None:
    user = get_current_user()
    if user is None:
        return None
    for attr in ("email", "name", "id"):
        value = getattr(user, attr, None)
        if value:
            return str(value)[:120]
    return None


@router.get("", **LMP_NONCONFORMITIES_LIST)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def list_lmp_nonconformities(
    status: Optional[str] = Query(
        None,
        pattern=_STATUS_PATTERN,
        json_schema_extra={"enum": _STATUS_ENUM},
        description="Filtro por status (open, in_progress, done).",
    ),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    sale_number: Optional[str] = Query(None, max_length=20),
    material_code: Optional[str] = Query(None, max_length=60),
    product_code: Optional[str] = Query(None, max_length=60),
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
            branch_code=branch,
            sale_number=sale_number,
            material_code=material_code,
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
            registered_at=body.registered_at,
            status=body.status,
            sale_number=body.sale_number,
            branch_code=body.branch_code,
            material_code=body.material_code,
            supplier_name=body.supplier_name,
            purchase_order=body.purchase_order,
            invoice_number=body.invoice_number,
            qty_received=body.qty_received,
            qty_accepted=body.qty_accepted,
            qty_rejected=body.qty_rejected,
            defect_description=body.defect_description,
            corrective_actions=body.corrective_actions,
            technical_opinion=body.technical_opinion,
            product_codes=body.product_codes,
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
            registered_at=body.registered_at,
            status=body.status,
            sale_number=body.sale_number,
            branch_code=body.branch_code,
            material_code=body.material_code,
            supplier_name=body.supplier_name,
            purchase_order=body.purchase_order,
            invoice_number=body.invoice_number,
            qty_received=body.qty_received,
            qty_accepted=body.qty_accepted,
            qty_rejected=body.qty_rejected,
            defect_description=body.defect_description,
            corrective_actions=body.corrective_actions,
            technical_opinion=body.technical_opinion,
            product_codes=body.product_codes,
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
