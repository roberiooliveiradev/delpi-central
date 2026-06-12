from fastapi import APIRouter, Query, Request

from maint_app.application.services.filial_access_scope_service import FilialAccessScopeService
from maint_app.application.services.maintenance_submodule_catalog import filter_submodules_for_user
from maint_app.composition.maintenance_composer import build_mini_applicators_totvs_gateway
from maint_app.core.errors import format_api_error
from maint_app.core.responses import fail, ok
from maint_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository
from maint_app.interface.http.filial_access_http import resolve_access_scope, resolve_user

router = APIRouter(prefix="/maintenance", tags=["Manutenção"])

_scope = FilialAccessScopeService()


@router.get("/health")
def module_health():
    db_ready = False
    db_hint = None
    try:
        row = PluginBaseRepository().fetch_one(
            """
            SELECT to_regclass('maintenance.schema_migrations')::text AS migrations_table
            """
        )
        db_ready = bool(row and row.get("migrations_table"))
        if not db_ready:
            db_hint = (
                "Tabela maintenance.schema_migrations não encontrada. "
                "Reinicie a API com migrations habilitadas."
            )
    except Exception as exc:
        db_hint = format_api_error(exc)

    return {
        "status": "online" if db_ready else "degraded",
        "module": "maintenance",
        "phase": "2-preventiva",
        "db_ready": db_ready,
        "db_hint": db_hint,
    }


@router.get("/options")
def get_options(request: Request):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    filiais = [
        {"id": "01", "label": "Matriz"},
        {"id": "02", "label": "ES"},
    ]
    filiais = _scope.filter_filiais_options(filiais, scope)
    submodules = filter_submodules_for_user(user)
    default_filial = _scope.resolve_default_filial(scope, filiais)
    return ok(
        {
            "filiais": filiais,
            "submodules": submodules,
            "modulos": submodules,
            "default_filial": default_filial,
            "access_scope": scope.meta(),
        },
        message="Opções carregadas.",
    )
