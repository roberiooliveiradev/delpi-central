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
    build_export_lmp_nonconformities_use_case,
    build_get_lmp_nonconformity_streak_use_case,
    build_get_lmp_nonconformity_use_case,
    build_import_lmp_nonconformities_use_case,
    build_list_lmp_nonconformities_use_case,
    build_list_lmp_nonconformity_history_use_case,
    build_list_lmp_problem_tags_use_case,
    build_update_lmp_nonconformity_use_case,
)
from app.core.responses import error_response, not_found_response
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.interface.http.openapi_agent_metadata import (
    LMP_NONCONFORMITIES_EXPORT,
    LMP_NONCONFORMITIES_IMPORT,
    LMP_NONCONFORMITIES_LIST,
    LMP_NONCONFORMITY_BY_ID,
    LMP_NONCONFORMITY_CREATE,
    LMP_NONCONFORMITY_DELETE,
    LMP_NONCONFORMITY_HISTORY,
    LMP_NONCONFORMITY_STREAK,
    LMP_NONCONFORMITY_UPDATE,
    LMP_PROBLEM_TAGS_LIST,
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

_STREAK_FIELDS = {
    "current_days_without_nc": "Dias atuais sem NC em LMPs",
    "record_days_without_nc": "Recorde de dias sem NC em LMPs",
    "last_nc_date": "Data da última NC",
    "reference_start_date": "Data âncora (primeira OV) quando não há NC",
    "as_of_date": "Data de referência do cálculo",
    "nc_count": "Quantidade de dias com NC registrada",
}

LMP_NC_EXPORT_VERSION = 1

_STATUS_PATTERN = "^(open|in_progress|done)$"
_STATUS_ENUM = ["open", "in_progress", "done"]
_DATE_PATTERN = r"^(\d{4}-\d{2}-\d{2})?$"
_SORT_BY_ENUM = [
    "registered_at",
    "sale_number",
    "lmp_number",
    "customer_name",
    "launch_date",
    "last_revision_date",
    "executed_by",
    "released_by",
    "status",
    "defect_description",
    "problem_tags",
    "products",
]
_SORT_BY_PATTERN = "^(registered_at|sale_number|lmp_number|customer_name|launch_date|last_revision_date|executed_by|released_by|status|defect_description|problem_tags|products)?$"
_SORT_DIR_PATTERN = "^(asc|desc)?$"
_SORT_DIR_ENUM = ["asc", "desc"]


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
        description="Número da OV (Protheus).",
    )
    lmp_number: str | None = Field(
        default=None,
        max_length=40,
        description="Número da LMP (legado / opcional).",
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
        description="Descrição livre do caso (texto do usuário).",
    )
    problem_tags: list[str] = Field(
        default_factory=list,
        description=(
            "Tags de problema identificado (catálogo compartilhado; "
            "ex.: Medida, Desenho, Terminal). Labels novas são criadas no catálogo."
        ),
    )
    corrective_actions: str | None = None
    technical_opinion: str | None = None
    products: list[LmpNcProductBody] = Field(default_factory=list)

    @field_validator(
        "sale_number",
        "lmp_number",
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

    @field_validator("problem_tags", mode="before")
    @classmethod
    def normalize_problem_tags(cls, value: object) -> list:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("problem_tags deve ser uma lista")
        out: list[str] = []
        for item in value:
            text = str(item or "").strip()
            if text:
                out.append(text[:80])
        return out


class ImportLmpNonconformitiesBody(BaseModel):
    items: list[dict] = Field(default_factory=list)
    dry_run: bool = False
    skip_existing: bool = True


def _current_actor() -> dict[str, str | None]:
    """Ator autenticado para auditoria (id, e-mail, nome + label legado)."""
    user = get_current_user()
    if user is None:
        return {
            "user_id": "unknown",
            "email": None,
            "name": None,
            "label": None,
        }
    user_id = getattr(user, "id", None)
    email_raw = getattr(user, "email", None)
    name_raw = None
    for attr in ("name", "full_name", "username"):
        value = getattr(user, attr, None)
        if isinstance(value, str) and value.strip():
            name_raw = value.strip()
            break
    email = email_raw.strip() if isinstance(email_raw, str) and email_raw.strip() else None
    name = name_raw[:300] if name_raw else None
    label = (name or email or (str(user_id) if user_id else None) or None)
    if label:
        label = label[:120]
    return {
        "user_id": str(user_id) if user_id else "unknown",
        "email": email[:255] if email else None,
        "name": name,
        "label": label,
    }


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
        description="Filtro parcial pela OV.",
    ),
    lmp_number: Optional[str] = Query(
        None,
        max_length=40,
        description="Filtro parcial pelo número legado da LMP.",
    ),
    customer_name: Optional[str] = Query(None, max_length=200),
    product_code: Optional[str] = Query(
        None,
        max_length=60,
        description="Filtro por código de produto/material nas linhas.",
    ),
    problem_tag: Optional[str] = Query(
        None,
        max_length=80,
        description="Filtro parcial por tag de problema identificado.",
    ),
    sort_by: Optional[str] = Query(
        None,
        pattern=_SORT_BY_PATTERN,
        json_schema_extra={"enum": _SORT_BY_ENUM},
        description="Coluna de ordenação da listagem.",
    ),
    sort_dir: Optional[str] = Query(
        None,
        pattern=_SORT_DIR_PATTERN,
        json_schema_extra={"enum": _SORT_DIR_ENUM},
        description="Direção da ordenação (asc|desc). Default: desc.",
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
            lmp_number=lmp_number,
            customer_name=customer_name,
            product_code=product_code,
            problem_tag=problem_tag,
            sort_by=sort_by,
            sort_dir=sort_dir,
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


@router.get("/problem-tags", **LMP_PROBLEM_TAGS_LIST)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def list_lmp_problem_tags():
    """Catálogo compartilhado de tags de problema identificado."""
    try:
        data = build_list_lmp_problem_tags_use_case().execute()
        return api_delpi_success(
            data,
            operation_id="list_lmp_problem_tags",
            message="Tags de problema LMP listadas com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar tags de problema LMP: {exc}")
        return error_response(
            "Erro interno ao listar tags de problema.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao listar tags de problema LMP: {exc}")
        return error_response(
            "Erro interno ao listar tags de problema.",
            status_code=500,
        )


@router.get("/streak", **LMP_NONCONFORMITY_STREAK)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def get_lmp_nonconformity_streak():
    """Dias atuais e recorde sem NC em LMPs (placar do dashboard)."""
    try:
        data = build_get_lmp_nonconformity_streak_use_case().execute()
        return api_delpi_success(
            data,
            operation_id="get_lmp_nonconformity_streak",
            message="Streak sem NC em LMPs calculado com sucesso.",
            fields=_STREAK_FIELDS,
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao calcular streak NC LMP: {exc}")
        return error_response(
            "Erro interno ao calcular dias sem NC.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao calcular streak NC LMP: {exc}")
        return error_response(
            "Erro interno ao calcular dias sem NC.",
            status_code=500,
        )


@router.get("/export", **LMP_NONCONFORMITIES_EXPORT)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def export_lmp_nonconformities():
    """Exporta todas as NCs LMP em JSON (listagem completa, sem paginação)."""
    try:
        from datetime import datetime, timezone

        items = build_export_lmp_nonconformities_use_case().execute()
        return api_delpi_success(
            {
                "version": LMP_NC_EXPORT_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "count": len(items),
                "items": items,
            },
            operation_id="export_lmp_nonconformities",
            message="Não conformidades LMP exportadas com sucesso.",
            shape="scalar",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao exportar NCs LMP: {exc}")
        return error_response(
            "Erro interno ao exportar não conformidades.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao exportar NCs LMP: {exc}")
        return error_response(
            "Erro interno ao exportar não conformidades.",
            status_code=500,
        )


@router.post("/import", **LMP_NONCONFORMITIES_IMPORT)
@require_any_permission(ENGINEERING_LMP_NC_WRITE)
def import_lmp_nonconformities(body: ImportLmpNonconformitiesBody = Body(...)):
    """Importa NCs LMP a partir de JSON (create-only; dedupe por id ou chave natural)."""
    try:
        if not body.items:
            return error_response(
                "Nenhuma não conformidade para importar (items vazio).",
                status_code=400,
            )
        actor = _current_actor()
        result = build_import_lmp_nonconformities_use_case().execute(
            body.items,
            created_by=actor["label"],
            actor_user_id=actor["user_id"],
            actor_email=actor["email"],
            actor_name=actor["name"],
            dry_run=body.dry_run,
            skip_existing=body.skip_existing,
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id="import_lmp_nonconformities",
            message="Importação de não conformidades LMP concluída.",
            shape="scalar",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao importar NCs LMP: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro inesperado ao importar NCs LMP: {exc}")
        return error_response(
            "Erro interno ao importar não conformidades.",
            status_code=500,
        )


@router.get("/{record_id}/history", **LMP_NONCONFORMITY_HISTORY)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def list_lmp_nonconformity_history(
    record_id: Annotated[UUID, Path(description="ID da não conformidade")],
):
    try:
        data = build_list_lmp_nonconformity_history_use_case().execute(str(record_id))
        if data is None:
            return not_found_response("Não conformidade não encontrada.")
        return api_delpi_success(
            data,
            operation_id="list_lmp_nonconformity_history",
            message="Histórico da não conformidade LMP listado com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar histórico NC LMP: {exc}")
        return error_response(
            "Erro interno ao listar histórico da não conformidade.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao listar histórico NC LMP: {exc}")
        return error_response(
            "Erro interno ao listar histórico da não conformidade.",
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
        actor = _current_actor()
        data = build_create_lmp_nonconformity_use_case().execute(
            status=body.status,
            sale_number=body.sale_number,
            lmp_number=body.lmp_number,
            customer_name=body.customer_name,
            launch_date=body.launch_date,
            last_revision_date=body.last_revision_date,
            executed_by=body.executed_by,
            released_by=body.released_by,
            defect_description=body.defect_description,
            corrective_actions=body.corrective_actions,
            technical_opinion=body.technical_opinion,
            products=_products_payload(body),
            problem_tags=body.problem_tags,
            created_by=actor["label"],
            actor_user_id=actor["user_id"],
            actor_email=actor["email"],
            actor_name=actor["name"],
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
        actor = _current_actor()
        data = build_update_lmp_nonconformity_use_case().execute(
            record_id=str(record_id),
            status=body.status,
            sale_number=body.sale_number,
            lmp_number=body.lmp_number,
            customer_name=body.customer_name,
            launch_date=body.launch_date,
            last_revision_date=body.last_revision_date,
            executed_by=body.executed_by,
            released_by=body.released_by,
            defect_description=body.defect_description,
            corrective_actions=body.corrective_actions,
            technical_opinion=body.technical_opinion,
            products=_products_payload(body),
            problem_tags=body.problem_tags,
            updated_by=actor["label"],
            actor_user_id=actor["user_id"],
            actor_email=actor["email"],
            actor_name=actor["name"],
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
