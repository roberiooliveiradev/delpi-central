from fastapi import APIRouter, Request

import logging

from tm_app.application.services.filial_access_scope_service import FilialAccessScopeService
from tm_app.core.catalogs import DEFAULT_SETORES, FILIAIS, options_payload
from tm_app.core.errors import format_api_error
from tm_app.core.responses import ok
from tm_app.interface.http.filial_access_http import resolve_access_scope
from tm_app.infrastructure.persistence.repositories.filial_repository import FilialRepository
from tm_app.infrastructure.persistence.repositories.processo_repository import ProcessoRepository
from tm_app.infrastructure.persistence.repositories.setor_repository import SetorRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transformometro", tags=["Transformometro"])


@router.get("/health")
def module_health():
    db_ready = False
    db_hint = None
    try:
        row = ProcessoRepository().fetch_one(
            """
            SELECT to_regclass('transformometro.processos')::text AS processos_table
            """
        )
        db_ready = bool(row and row.get("processos_table"))
        if not db_ready:
            db_hint = "Tabela transformometro.processos nao encontrada. Reinicie a API com migrations habilitadas."
    except Exception as exc:
        db_hint = format_api_error(exc)

    return {
        "status": "online" if db_ready else "degraded",
        "module": "transformometro",
        "phase": "4-melhorias",
        "db_ready": db_ready,
        "db_hint": db_hint,
    }


def _load_filiais_for_options() -> list[dict]:
    try:
        rows = FilialRepository().list_for_options()
        if rows:
            return rows
    except Exception as exc:
        logger.warning("filiais_options_fallback err=%s", format_api_error(exc))
    return [{"id": k, "label": v} for k, v in FILIAIS.items()]


def _load_setores_for_options() -> list[dict]:
    try:
        return SetorRepository().list_for_options()
    except Exception as exc:
        logger.warning("setores_options_fallback err=%s", format_api_error(exc))
        return [
            {"id": setor_id, "label": setor_id, "filiais": list(FILIAIS.keys())}
            for setor_id in DEFAULT_SETORES
        ]


@router.get("/options")
def get_options(request: Request):
    scope = resolve_access_scope(request)
    filiais = FilialAccessScopeService().filter_filiais_options(
        _load_filiais_for_options(),
        scope,
    )
    setores = _load_setores_for_options()
    if not scope.is_unrestricted:
        allowed = scope.allowed_codigos
        setores = [
            item
            for item in setores
            if not item.get("filiais")
            or any(str(code) in allowed for code in item.get("filiais") or [])
        ]
    payload = options_payload(setores, filiais)
    payload["access_scope"] = scope.meta()
    return ok(payload)
