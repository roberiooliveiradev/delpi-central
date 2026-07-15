from __future__ import annotations

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from app.application.services.kaizen_portal_notification_service import (
    notify_public_suggestion_created,
)
from app.composition.kaizen_composer import build_kaizen_repository
from app.core.responses import error_response
from app.domain.services.kaizen.kaizen_public_suggestion_mapper import (
    build_suggestion_record_fields,
)
from app.domain.services.kaizen.kaizen_status_date_rules import KaizenStatusDateError
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

# Rota pública (sem JWT) — liberada no auth_middleware por prefixo /public/kaizen/.
router = APIRouter(prefix="/public/kaizen", tags=["Kaizen — público"])

_CREATED_BY = "public-suggestion"


class PublicKaizenSuggestionBody(BaseModel):
    proposer_name: str = Field(..., min_length=2, max_length=200)
    sector: str = Field(..., min_length=1, max_length=200)
    employee_registration: str = Field(..., min_length=1, max_length=50)
    work_center_or_location: str = Field(..., min_length=1, max_length=200)
    problem_description: str = Field(..., min_length=5, max_length=4000)
    proposed_solution: str = Field(..., min_length=5, max_length=4000)
    branch_code: str | None = Field(default="01", pattern="^(01|02)$")
    # Honeypot — bots preenchem; humanos deixam vazio.
    website: str | None = Field(default=None, max_length=200)


@router.post("/suggestions")
def create_public_kaizen_suggestion(
    body: PublicKaizenSuggestionBody = Body(...),
):
    if (body.website or "").strip():
        return api_delpi_success({"id": None, "accepted": True}, operation_id="create_public_kaizen_suggestion")

    try:
        fields = build_suggestion_record_fields(
            proposer_name=body.proposer_name,
            sector=body.sector,
            employee_registration=body.employee_registration,
            work_center_or_location=body.work_center_or_location,
            problem_description=body.problem_description,
            proposed_solution=body.proposed_solution,
            branch_code=body.branch_code or "01",
        )
        repo = build_kaizen_repository()
        created = repo.create_record(
            fields=fields,
            created_by_user_id=_CREATED_BY,
            actor_name=body.proposer_name.strip()[:200] or None,
        )
        try:
            notify_public_suggestion_created(record=created)
        except Exception:
            log_error("Falha ao notificar sugestão Kaizen (seguindo sem bloquear).")
        return api_delpi_success(
            {"id": created.get("id"), "status": created.get("status")},
            operation_id="create_public_kaizen_suggestion",
            message="Sugestão recebida com sucesso.",
        )
    except KaizenStatusDateError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao gravar sugestão pública Kaizen: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao gravar sugestão pública Kaizen: {exc}")
        return error_response("Erro interno ao enviar a sugestão.", status_code=500)
