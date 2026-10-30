"""Rotas NC da Engineering API — contratos E-NC-01..11 (T2/T4, Plano 48).

Bounded context próprio (``/v1/nonconformities``), NÃO aninhado em
``/v1/lmps`` — separação de navegação do doc 45. Persistência via port
``NonconformityRepository`` composta por ambiente (``ENG_NC_REPOSITORY``);
sem env → ``unavailable`` honesto, nunca lista vazia falsa.

AuthZ unificada: exclusivamente ``engineering.access`` via Core —
fail-closed, principal humano obrigatório, ``caller_app`` nunca é
autoridade. Permissões legadas não são aceitas como substitutas.

Escrita: E-NC-07..10 ficam ativas onde o adapter configurado é
autorizado (sandbox/dev isolado). IMPORT exige ``confirm_replace`` +
opt-in de ambiente — proteção contra substituição total acidental.
"""

import re
from uuid import UUID

from fastapi import APIRouter, Body, Header, Path, Query
from pydantic import BaseModel, Field, field_validator

from delpi_auth.authorization import require_any_permission
from delpi_auth.context_resolver import resolve_user_context

from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.use_cases.nonconformity.actor import (
    nc_actor_from_principal,
)
from engineering_app.composition.nc_composer import (
    build_create_nonconformity_use_case,
    build_delete_nonconformity_use_case,
    build_export_nonconformities_use_case,
    build_get_nonconformity_context_use_case,
    build_get_nonconformity_indicators_use_case,
    build_get_nonconformity_use_case,
    build_import_nonconformities_use_case,
    build_list_nonconformities_use_case,
    build_list_nonconformity_history_use_case,
    build_list_problem_tags_use_case,
    build_prepare_nonconformity_mutation_use_case,
    build_update_nonconformity_use_case,
)
from engineering_app.core.responses import fail, ok
from engineering_app.domain.nonconformity.errors import (
    NcConcurrencyError,
    NcNotFoundError,
    NcRepositoryError,
    NcUnsafeOperationError,
    NcValidationError,
)
from engineering_app.domain.nonconformity.models import NcActor
from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
)

router = APIRouter()

ENGINEERING_ACCESS = "engineering.access"

_STATUS_PATTERN = "^(open|in_progress|done)$"
_DATE_PATTERN = r"^(\d{4}-\d{2}-\d{2})?$"
_SORT_BY_PATTERN = (
    "^(registered_at|occurrence_date|sale_number|lmp_number|customer_name|"
    "launch_date|last_revision_date|executed_by|released_by|status|"
    "defect_description|problem_tags|products)?$"
)
_SORT_DIR_PATTERN = "^(asc|desc)?$"


class NcProductBody(BaseModel):
    product_code: str = Field(..., min_length=1, max_length=60)
    product_description: str | None = Field(default=None, max_length=255)

    @field_validator("product_code", "product_description", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class NonconformityBody(BaseModel):
    """Body create/update — ``registered_at`` é do servidor no create."""

    status: str = Field(default="open", pattern=_STATUS_PATTERN)
    sale_number: str | None = Field(default=None, max_length=20)
    lmp_number: str | None = Field(default=None, max_length=40)
    customer_name: str | None = Field(default=None, max_length=200)
    occurrence_date: str | None = Field(
        default=None, max_length=10, pattern=_DATE_PATTERN
    )
    launch_date: str | None = Field(
        default=None, max_length=10, pattern=_DATE_PATTERN
    )
    last_revision_date: str | None = Field(
        default=None, max_length=10, pattern=_DATE_PATTERN
    )
    executed_by: str | None = Field(default=None, max_length=200)
    released_by: str | None = Field(default=None, max_length=200)
    defect_description: str | None = None
    corrective_actions: str | None = None
    technical_opinion: str | None = None
    problem_tags: list[str] = Field(default_factory=list)
    products: list[NcProductBody] = Field(default_factory=list)
    expected_updated_at: str | None = Field(
        default=None,
        description="ETag otimista (updated_at do GET) — mismatch → 409.",
    )

    @field_validator(
        "sale_number",
        "lmp_number",
        "customer_name",
        "occurrence_date",
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

    @field_validator("products", mode="before")
    @classmethod
    def normalize_products_list(cls, value: object) -> list:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("products deve ser uma lista")
        return value


class ImportNonconformitiesBody(BaseModel):
    items: list[dict] = Field(default_factory=list)
    dry_run: bool = False
    confirm_replace: bool = Field(
        default=False,
        description=(
            "Obrigatório fora de dry_run: a importação substitui todo "
            "o acervo (semântica legado) — proteção anti-acidente."
        ),
    )


def _source_context(user) -> HomeSourceContext:
    return HomeSourceContext(
        user_id=str(getattr(user, "id", "") or ""),
        access_token=str(getattr(user, "access_token", "") or ""),
        request_id=get_request_id(),
    )


def _require_human_principal(operation_id: str):
    user = resolve_user_context()
    if getattr(user, "principal_type", None) != "user":
        return None, fail(
            "Operação de não conformidade exige principal humano.",
            403,
            operation_id=operation_id,
        )
    return user, None


def _actor_from_user(user) -> NcActor:
    return nc_actor_from_principal(user)


def _nc_error_response(exc: Exception, operation_id: str):
    if isinstance(exc, NcNotFoundError):
        return fail("Não conformidade não encontrada.", 404, operation_id=operation_id)
    if isinstance(exc, NcValidationError):
        return fail(str(exc), 400, data={"fields": exc.fields}, operation_id=operation_id)
    if isinstance(exc, NcConcurrencyError):
        return fail(str(exc), 409, operation_id=operation_id)
    if isinstance(exc, NcUnsafeOperationError):
        return fail(str(exc), 403, operation_id=operation_id)
    if isinstance(exc, NcRepositoryError):
        return fail(str(exc), 503, operation_id=operation_id)
    return fail("Erro interno no contexto de não conformidades.", 500, operation_id=operation_id)


def _body_payload(body: NonconformityBody) -> dict:
    data = body.model_dump(exclude={"expected_updated_at"})
    data["products"] = [
        {
            "product_code": item.product_code,
            "product_description": item.product_description,
        }
        for item in body.products
    ]
    return data


# --- READ contracts (E-NC-01..06, 11) -----------------------------------


@router.get(
    "/v1/nonconformities/indicators",
    operation_id="get_nonconformity_indicators",
    summary="E-NC-04 — dias sem NC (streak atual/recorde)",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_nonconformity_indicators():
    user, denied = _require_human_principal("get_nonconformity_indicators")
    if denied is not None:
        return denied
    try:
        data = await build_get_nonconformity_indicators_use_case().execute(
            access_token=str(getattr(user, "access_token", "") or "")
        )
    except Exception as exc:
        return _nc_error_response(exc, "get_nonconformity_indicators")
    return ok(
        data,
        message="Indicadores de dias sem NC carregados.",
        operation_id="get_nonconformity_indicators",
    )


@router.get(
    "/v1/nonconformities/problem-tags",
    operation_id="list_nonconformity_problem_tags",
    summary="E-NC-05 — catálogo de tags de problema identificado",
)
@require_any_permission([ENGINEERING_ACCESS])
async def list_nonconformity_problem_tags():
    user, denied = _require_human_principal("list_nonconformity_problem_tags")
    if denied is not None:
        return denied
    try:
        data = await build_list_problem_tags_use_case().execute()
    except Exception as exc:
        return _nc_error_response(exc, "list_nonconformity_problem_tags")
    return ok(
        {"items": data},
        message="Tags de problema listadas com sucesso.",
        operation_id="list_nonconformity_problem_tags",
    )


@router.get(
    "/v1/nonconformities/export",
    operation_id="export_nonconformities",
    summary="E-NC-06 — exportação JSON completa do acervo",
)
@require_any_permission([ENGINEERING_ACCESS])
async def export_nonconformities():
    user, denied = _require_human_principal("export_nonconformities")
    if denied is not None:
        return denied
    try:
        data = await build_export_nonconformities_use_case().execute()
    except Exception as exc:
        return _nc_error_response(exc, "export_nonconformities")
    return ok(
        data,
        message="Não conformidades exportadas com sucesso.",
        operation_id="export_nonconformities",
    )


@router.get(
    "/v1/nonconformities",
    operation_id="list_nonconformities",
    summary="E-NC-01 — listagem paginada com filtros e ordenação",
)
@require_any_permission([ENGINEERING_ACCESS])
async def list_nonconformities(
    status: str | None = Query(default=None, pattern=_STATUS_PATTERN),
    sale_number: str | None = Query(default=None, max_length=20),
    lmp_number: str | None = Query(default=None, max_length=40),
    customer_name: str | None = Query(default=None, max_length=200),
    product_code: str | None = Query(default=None, max_length=60),
    problem_tag: str | None = Query(default=None, max_length=80),
    date_start: str | None = Query(default=None, pattern=_DATE_PATTERN),
    date_end: str | None = Query(default=None, pattern=_DATE_PATTERN),
    sort_by: str | None = Query(default=None, pattern=_SORT_BY_PATTERN),
    sort_dir: str | None = Query(default=None, pattern=_SORT_DIR_PATTERN),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    user, denied = _require_human_principal("list_nonconformities")
    if denied is not None:
        return denied
    try:
        data = await build_list_nonconformities_use_case().execute(
            status=status,
            sale_number=sale_number,
            lmp_number=lmp_number,
            customer_name=customer_name,
            product_code=product_code,
            problem_tag=problem_tag,
            date_start=date_start,
            date_end=date_end,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
    except Exception as exc:
        return _nc_error_response(exc, "list_nonconformities")
    return ok(
        data,
        message="Não conformidades listadas com sucesso.",
        operation_id="list_nonconformities",
    )


@router.get(
    "/v1/nonconformities/{record_id}/history",
    operation_id="get_nonconformity_history",
    summary="E-NC-03 — histórico append-only da NC",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_nonconformity_history(
    record_id: str = Path(..., description="UUID da não conformidade"),
):
    user, denied = _require_human_principal("get_nonconformity_history")
    if denied is not None:
        return denied
    try:
        UUID(record_id)
    except ValueError:
        return fail("record_id inválido (UUID).", 400, operation_id="get_nonconformity_history")
    try:
        data = await build_list_nonconformity_history_use_case().execute(record_id)
    except Exception as exc:
        return _nc_error_response(exc, "get_nonconformity_history")
    return ok(
        {"items": data},
        message="Histórico da não conformidade listado com sucesso.",
        operation_id="get_nonconformity_history",
    )


@router.get(
    "/v1/nonconformities/{record_id}/context",
    operation_id="get_nonconformity_context",
    summary="E-NC-11 — contexto OV/produto/BOM via fatos oficiais",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_nonconformity_context(
    record_id: str = Path(..., description="UUID da não conformidade"),
    max_depth: int = Query(default=6, ge=1, le=12),
):
    user, denied = _require_human_principal("get_nonconformity_context")
    if denied is not None:
        return denied
    try:
        UUID(record_id)
    except ValueError:
        return fail("record_id inválido (UUID).", 400, operation_id="get_nonconformity_context")
    try:
        data = await build_get_nonconformity_context_use_case().execute(
            _source_context(user), record_id=record_id, max_depth=max_depth
        )
    except Exception as exc:
        return _nc_error_response(exc, "get_nonconformity_context")
    return ok(
        data,
        message="Contexto da não conformidade carregado.",
        operation_id="get_nonconformity_context",
    )


@router.get(
    "/v1/nonconformities/{record_id}",
    operation_id="get_nonconformity",
    summary="E-NC-02 — detalhe de uma não conformidade",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_nonconformity(
    record_id: str = Path(..., description="UUID da não conformidade"),
):
    user, denied = _require_human_principal("get_nonconformity")
    if denied is not None:
        return denied
    try:
        UUID(record_id)
    except ValueError:
        return fail("record_id inválido (UUID).", 400, operation_id="get_nonconformity")
    try:
        data = await build_get_nonconformity_use_case().execute(record_id)
    except Exception as exc:
        return _nc_error_response(exc, "get_nonconformity")
    return ok(
        data,
        message="Não conformidade carregada com sucesso.",
        operation_id="get_nonconformity",
    )


# --- WRITE contracts (E-NC-07..10) — ativos só onde autorizado ----------


@router.post(
    "/v1/nonconformities",
    operation_id="create_nonconformity",
    summary="E-NC-07 — criação com histórico e auditoria do ator",
)
@require_any_permission([ENGINEERING_ACCESS])
async def create_nonconformity(
    body: NonconformityBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=120),
):
    user, denied = _require_human_principal("create_nonconformity")
    if denied is not None:
        return denied
    try:
        data = await build_create_nonconformity_use_case().execute(
            payload=_body_payload(body),
            actor=_actor_from_user(user),
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _nc_error_response(exc, "create_nonconformity")
    return ok(
        data,
        message="Não conformidade criada com sucesso.",
        operation_id="create_nonconformity",
    )


@router.put(
    "/v1/nonconformities/{record_id}",
    operation_id="update_nonconformity",
    summary="E-NC-08 — full-replace com optimistic locking opcional",
)
@require_any_permission([ENGINEERING_ACCESS])
async def update_nonconformity(
    record_id: str = Path(..., description="UUID da não conformidade"),
    body: NonconformityBody = Body(...),
):
    user, denied = _require_human_principal("update_nonconformity")
    if denied is not None:
        return denied
    try:
        UUID(record_id)
    except ValueError:
        return fail("record_id inválido (UUID).", 400, operation_id="update_nonconformity")
    try:
        data = await build_update_nonconformity_use_case().execute(
            record_id=record_id,
            payload=_body_payload(body),
            actor=_actor_from_user(user),
            expected_updated_at=body.expected_updated_at,
        )
    except Exception as exc:
        return _nc_error_response(exc, "update_nonconformity")
    return ok(
        data,
        message="Não conformidade atualizada com sucesso.",
        operation_id="update_nonconformity",
    )


@router.delete(
    "/v1/nonconformities/{record_id}",
    operation_id="delete_nonconformity",
    summary="E-NC-09 — exclusão com cascade do histórico (GUC V008)",
)
@require_any_permission([ENGINEERING_ACCESS])
async def delete_nonconformity(
    record_id: str = Path(..., description="UUID da não conformidade"),
):
    user, denied = _require_human_principal("delete_nonconformity")
    if denied is not None:
        return denied
    try:
        UUID(record_id)
    except ValueError:
        return fail("record_id inválido (UUID).", 400, operation_id="delete_nonconformity")
    try:
        data = await build_delete_nonconformity_use_case().execute(record_id)
    except Exception as exc:
        return _nc_error_response(exc, "delete_nonconformity")
    return ok(
        data,
        message="Não conformidade excluída com sucesso.",
        operation_id="delete_nonconformity",
    )


@router.post(
    "/v1/nonconformities/import",
    operation_id="import_nonconformities",
    summary="E-NC-10 — importação JSON (substituição total; dry-run/confirm)",
)
@require_any_permission([ENGINEERING_ACCESS])
async def import_nonconformities(body: ImportNonconformitiesBody = Body(...)):
    user, denied = _require_human_principal("import_nonconformities")
    if denied is not None:
        return denied
    if not body.items:
        return fail(
            "Nenhuma não conformidade para importar (items vazio).",
            400,
            operation_id="import_nonconformities",
        )
    try:
        result = await build_import_nonconformities_use_case().execute(
            items=body.items,
            actor=_actor_from_user(user),
            dry_run=body.dry_run,
            confirm_replace=body.confirm_replace,
        )
    except Exception as exc:
        return _nc_error_response(exc, "import_nonconformities")
    return ok(
        result.to_dict(),
        message="Importação de não conformidades concluída.",
        operation_id="import_nonconformities",
    )


class PrepareNonconformityBody(BaseModel):
    """Body PREPARE — validação + diff projetado, SEM efeitos colaterais."""

    operation: str = Field(..., pattern="^(create|update)$")
    record_id: str | None = Field(default=None)
    payload: dict = Field(default_factory=dict)


@router.post(
    "/v1/nonconformities/prepare",
    operation_id="prepare_nonconformity_mutation",
    summary="E-NC-12 — PREPARE de mutação (validação + diff, sem gravação)",
)
@require_any_permission([ENGINEERING_ACCESS])
async def prepare_nonconformity_mutation(
    body: PrepareNonconformityBody = Body(...),
):
    user, denied = _require_human_principal("prepare_nonconformity_mutation")
    if denied is not None:
        return denied
    if body.record_id:
        try:
            UUID(body.record_id)
        except ValueError:
            return fail(
                "record_id inválido (UUID esperado).",
                400,
                operation_id="prepare_nonconformity_mutation",
            )
    try:
        result = await build_prepare_nonconformity_mutation_use_case().execute(
            operation=body.operation,
            payload=body.payload,
            record_id=body.record_id,
        )
    except Exception as exc:
        return _nc_error_response(exc, "prepare_nonconformity_mutation")
    return ok(
        result,
        message="Mutação analisada — nada foi gravado.",
        operation_id="prepare_nonconformity_mutation",
    )
