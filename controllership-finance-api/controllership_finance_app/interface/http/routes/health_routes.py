from fastapi import APIRouter

from controllership_finance_app.config import missing_required_config

router = APIRouter(tags=["Health"])


@router.get("/health", operation_id="get_controllership_finance_health")
def health():
    return {"status": "online", "service": "controllership-finance-api"}


@router.get("/ready", operation_id="get_controllership_finance_ready")
def ready():
    """Readiness diagnóstico (doc 45 §5/§9): config obrigatória presente.

    Endpoint diagnóstico — o healthcheck do container e o tráfego do
    gateway observam `/health`. Não inventa dependência de banco e não
    realiza chamadas de rede.
    """
    missing = missing_required_config()
    config_ready = not missing
    payload: dict = {
        "status": "ready" if config_ready else "degraded",
        "service": "controllership-finance-api",
        "config_ready": config_ready,
    }
    if missing:
        payload["core_hint"] = (
            "Configuração obrigatória ausente: " + ", ".join(missing)
        )
    return payload
