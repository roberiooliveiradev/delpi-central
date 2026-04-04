from fastapi import APIRouter, HTTPException, Request

from delpi_auth.authorization import require_permission

from app.interface.http.schemas.strategic_indicators_settings_schema import (
    UpdateStrategicIndicatorsSettingsBodySchema,
)

from app.application.dto.strategic_indicators.update_settings_request import (
    UpdateStrategicIndicatorsSettingsRequest,
)

from app.application.use_cases.strategic_indicators.update_settings_use_case import (
    StrategicIndicatorsSettingsValidationError,
)

from app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_settings_audit_repository import (
    PostgresStrategicIndicatorsSettingsAuditRepository,
)

from app.composition.strategic_indicators_composer import (
    build_get_strategic_indicators_settings_use_case,
    build_update_strategic_indicators_settings_use_case,
)

router = APIRouter(
    prefix="/strategic-indicators",
    tags=["Strategic Indicators"],
)


@router.get("/health")
def strategic_indicators_health():
    return {
        "status": "online",
        "module": "strategic-indicators",
    }


@router.get("/settings")
@require_permission("strategic-indicators.settings.manage")
def get_strategic_indicators_settings():
    try:
        use_case = build_get_strategic_indicators_settings_use_case()
        result = use_case.execute()

        return {
            "weights": result.weights,
            "goals": result.goals,
            "parameters": result.parameters,
            "governance": result.governance,
            "meta": {
                "source": result.meta.source,
                "updated_at": result.meta.updated_at,
                "updated_by_email": result.meta.updated_by_email,
            },
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao carregar configurações do Strategic Indicators: {exc}",
        ) from exc
    

@router.put("/settings")
@require_permission("strategic-indicators.settings.manage")
async def update_strategic_indicators_settings(
    body: UpdateStrategicIndicatorsSettingsBodySchema,
    request: Request,
):
    try:
        user_context = getattr(request.state, "user", None)
        actor_user_id = None
        actor_email = None

        if user_context is not None:
            actor_user_id = getattr(user_context, "id", None) or getattr(user_context, "sub", None)
            actor_email = getattr(user_context, "email", None)

        dto = UpdateStrategicIndicatorsSettingsRequest(
            weights=body.weights.model_dump(),
            goals=body.goals.model_dump(),
            parameters=body.parameters.model_dump(),
            governance=body.governance.model_dump(),
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )

        use_case = build_update_strategic_indicators_settings_use_case()
        result = use_case.execute(dto)

        return result

    except StrategicIndicatorsSettingsValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao atualizar configurações do Strategic Indicators: {exc}",
        ) from exc
    

@router.get("/settings/audit")
@require_permission("strategic-indicators.settings.manage")
def get_strategic_indicators_settings_audit():
    try:
        repository = PostgresStrategicIndicatorsSettingsAuditRepository()
        rows = repository.list_recent_events(limit=20)
        return {
            "items": rows,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao carregar auditoria do Strategic Indicators: {exc}",
        ) from exc