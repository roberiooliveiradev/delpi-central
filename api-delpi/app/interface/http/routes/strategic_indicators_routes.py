from fastapi import APIRouter, HTTPException, Request

from app.interface.http.schemas.strategic_indicators_settings_schema import (
    UpdateStrategicIndicatorsSettingsBodySchema,
)

from app.application.dto.strategic_indicators.update_settings_request import (
    UpdateStrategicIndicatorsSettingsRequest,
)

from app.application.use_cases.strategic_indicators.update_settings_use_case import (
    StrategicIndicatorsSettingsValidationError,
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
async def update_strategic_indicators_settings(
    body: UpdateStrategicIndicatorsSettingsBodySchema,
    request: Request,
):
    try:
        user_context = getattr(request.state, "user", None)
        actor_user_id = None
        actor_email = None

        if isinstance(user_context, dict):
            actor_user_id = user_context.get("sub")
            actor_email = user_context.get("email")

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