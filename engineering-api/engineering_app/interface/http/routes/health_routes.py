from fastapi import APIRouter

from engineering_app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", operation_id="get_engineering_health")
def health():
    return {"status": "online", "service": settings.SERVICE_NAME}


@router.get("/ready", operation_id="get_engineering_ready")
def ready():
    return {
        "status": "ready",
        "service": settings.SERVICE_NAME,
        "root_path": settings.ENGINEERING_API_ROOT_PATH,
    }
