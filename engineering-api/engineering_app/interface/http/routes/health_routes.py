from fastapi import APIRouter

from engineering_app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", operation_id="get_engineering_health")
def health():
    return {"status": "online", "service": settings.SERVICE_NAME}


@router.get("/ready", operation_id="get_engineering_ready")
def ready():
    # Readiness honesta: reflete bootstrap local + presença da configuração
    # exigida pela camada de auth. Não valida conectividade com Core/Keycloak
    # (custo por healthcheck sem justificativa) — falha de autoridade efetiva
    # é observada por request (fail-closed no middleware).
    return {
        "status": "ready",
        "service": settings.SERVICE_NAME,
        "root_path": settings.ENGINEERING_API_ROOT_PATH,
        "auth_configured": not settings.missing_auth_envs(),
    }
