"""Rotas públicas de leitura — Guias e Procedimentos."""

from __future__ import annotations

from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    GUIAS_PROCEDIMENTOS_READ_PERMISSIONS,
)
from app.composition.guias_procedimentos_composer import (
    build_get_guias_department_by_slug_use_case,
    build_get_guias_procedure_by_slug_use_case,
    build_list_guias_departments_use_case,
)
from app.core.responses import error_response, not_found_response
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(tags=["Guias e Procedimentos"])


@router.get("/departments", operation_id="list_guias_procedimentos_departments")
@require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)
def list_guias_departments():
    try:
        data = build_list_guias_departments_use_case().execute()
        return api_delpi_success(
            data,
            operation_id="list_guias_procedimentos_departments",
            message="Departamentos recuperados com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar departamentos de guias: {exc}")
        return error_response(
            "Erro interno ao listar departamentos.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao listar departamentos de guias: {exc}")
        return error_response(
            "Erro interno ao listar departamentos.",
            status_code=500,
        )


@router.get("/departments/{slug}", operation_id="get_guias_procedimentos_department")
@require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)
def get_guias_department(slug: str):
    try:
        data = build_get_guias_department_by_slug_use_case().execute(slug)
        if data is None:
            return not_found_response("Departamento não encontrado.")
        return api_delpi_success(
            data,
            operation_id="get_guias_procedimentos_department",
            message="Departamento recuperado com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao consultar departamento de guias: {exc}")
        return error_response(
            "Erro interno ao consultar departamento.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao consultar departamento de guias: {exc}")
        return error_response(
            "Erro interno ao consultar departamento.",
            status_code=500,
        )


@router.get("/procedures/{slug}", operation_id="get_guias_procedimentos_procedure")
@require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)
def get_guias_procedure(slug: str):
    try:
        data = build_get_guias_procedure_by_slug_use_case().execute(slug)
        if data is None:
            return not_found_response("Procedimento não encontrado.")
        return api_delpi_success(
            data,
            operation_id="get_guias_procedimentos_procedure",
            message="Procedimento recuperado com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao consultar procedimento de guias: {exc}")
        return error_response(
            "Erro interno ao consultar procedimento.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao consultar procedimento de guias: {exc}")
        return error_response(
            "Erro interno ao consultar procedimento.",
            status_code=500,
        )
