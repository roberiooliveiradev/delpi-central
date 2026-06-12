from fastapi import APIRouter, Query, Request

from maint_app.composition.maintenance_composer import build_mini_applicators_totvs_gateway
from maint_app.core.errors import format_api_error
from maint_app.core.responses import fail, ok
from maint_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository

router = APIRouter(prefix="/maintenance", tags=["Manutenção"])


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
        "phase": "0-fundacao",
        "db_ready": db_ready,
        "db_hint": db_hint,
    }


@router.get("/options")
def get_options():
    return ok(
        {
            "filiais": [
                {"id": "01", "label": "Matriz"},
                {"id": "02", "label": "ES"},
            ],
            "modulos": [
                {"id": "mini-aplicadores", "label": "Mini-aplicadores"},
            ],
        },
        message="Opções carregadas.",
    )
