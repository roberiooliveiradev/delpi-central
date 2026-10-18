"""Rotas administrativas dos perfis de sequenciamento por centro de trabalho.

Fundação da iniciativa «Regras de Sequenciamento»: CRUD versionado de perfis
e vínculo perfil ↔ (filial, CT). Configuração apenas administrativa — nenhuma
rota aqui altera a fila WORKING/PUBLISHED nem dispara resequenciamento.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from production_control_app.composition.pc_composer import (
    build_sequencing_profile_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
    SequencingProfileConflict,
    SequencingProfileInvalid,
    SequencingProfileNotFound,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PluginsDatabaseConfigError,
    PluginsDatabaseConnectionError,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Machine load sequencing"])


def _handle_sequencing_errors(exc: Exception):
    if isinstance(exc, InvalidBranch):
        return fail(str(exc), 422)
    if isinstance(exc, BranchAccessDenied):
        return fail(str(exc), 403)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, SequencingProfileNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, SequencingProfileConflict):
        return fail(str(exc), 409)
    if isinstance(exc, (SequencingProfileInvalid, ValueError)):
        return fail(str(exc), 422)
    if isinstance(exc, DelpiGatewayError):
        return fail(str(exc), 502)
    if isinstance(exc, (PluginsDatabaseConfigError, PluginsDatabaseConnectionError)):
        return fail("Configuração de sequenciamento temporariamente indisponível.", 503)
    raise exc


class SequencingCriterionBody(BaseModel):
    type: str = Field(..., min_length=1, max_length=40)
    params: dict[str, Any] | None = None


class SequencingProfileCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    # Lista ordenada: a posição é a precedência; o primeiro deve ser
    # pa_due_date (prioridade obrigatória — validação no domínio).
    criteria: list[SequencingCriterionBody] = Field(..., min_length=1, max_length=8)


class SequencingProfileUpdateBody(SequencingProfileCreateBody):
    status: str = Field(..., min_length=1, max_length=20)
    # Token de concorrência otimista — o cliente declara a revisão que viu;
    # divergência da vigente = 409 sem write.
    expected_revision: int = Field(..., ge=1)


class SequencingBindingBody(BaseModel):
    # Vínculo explícito do CT ao perfil; null desvincula.
    profile_id: UUID | None = None


def _criteria_payload(criteria: list[SequencingCriterionBody]) -> list[dict[str, Any]]:
    return [{"type": item.type, "params": item.params} for item in criteria]


@router.get(
    "/machine-load/sequencing-profiles",
    operation_id="list_machine_load_sequencing_profiles",
)
def list_sequencing_profiles(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """Lista os perfis cadastrados com os vínculos da filial informada."""
    user = resolve_user(request)
    try:
        data = build_sequencing_profile_service().list_profiles(user, branch=branch)
    except Exception as exc:
        return _handle_sequencing_errors(exc)
    return ok(data)


@router.get(
    "/machine-load/sequencing-profiles/{profile_id}",
    operation_id="get_machine_load_sequencing_profile",
)
def get_sequencing_profile(
    request: Request,
    profile_id: UUID,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    user = resolve_user(request)
    try:
        data = build_sequencing_profile_service().get_profile(
            user, branch=branch, profile_id=profile_id
        )
    except Exception as exc:
        return _handle_sequencing_errors(exc)
    return ok(data)


@router.post(
    "/machine-load/sequencing-profiles",
    operation_id="create_machine_load_sequencing_profile",
)
def create_sequencing_profile(
    request: Request,
    body: SequencingProfileCreateBody,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """Cria um perfil em rascunho. Não altera a fila de produção."""
    user = resolve_user(request)
    try:
        data = build_sequencing_profile_service().create_profile(
            user,
            branch=branch,
            name=body.name,
            description=body.description,
            criteria=_criteria_payload(body.criteria),
        )
    except Exception as exc:
        return _handle_sequencing_errors(exc)
    return ok(data)


@router.put(
    "/machine-load/sequencing-profiles/{profile_id}",
    operation_id="update_machine_load_sequencing_profile",
)
def update_sequencing_profile(
    request: Request,
    profile_id: UUID,
    body: SequencingProfileUpdateBody,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """Atualização versionada: expected_revision divergente → 409."""
    user = resolve_user(request)
    try:
        data = build_sequencing_profile_service().update_profile(
            user,
            branch=branch,
            profile_id=profile_id,
            expected_revision=body.expected_revision,
            name=body.name,
            description=body.description,
            status=body.status,
            criteria=_criteria_payload(body.criteria),
        )
    except Exception as exc:
        return _handle_sequencing_errors(exc)
    return ok(data)


@router.get(
    "/machine-load/sequencing-bindings",
    operation_id="list_machine_load_sequencing_bindings",
)
def list_sequencing_bindings(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Centro de trabalho específico (opcional)",
    ),
):
    """Consulta o(s) vínculo(s) perfil ↔ CT da filial."""
    user = resolve_user(request)
    try:
        data = build_sequencing_profile_service().list_bindings(
            user, branch=branch, work_center=work_center
        )
    except Exception as exc:
        return _handle_sequencing_errors(exc)
    return ok(data)


@router.put(
    "/machine-load/sequencing-bindings",
    operation_id="set_machine_load_sequencing_binding",
)
def set_sequencing_binding(
    request: Request,
    body: SequencingBindingBody,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    work_center: str = Query(
        ..., alias="workCenter", description="Centro de trabalho"
    ),
):
    """Vincula (ou desvincula, com profile_id null) um perfil ao CT da filial."""
    user = resolve_user(request)
    try:
        data = build_sequencing_profile_service().set_binding(
            user,
            branch=branch,
            work_center=work_center,
            profile_id=body.profile_id,
        )
    except Exception as exc:
        return _handle_sequencing_errors(exc)
    return ok(data)
