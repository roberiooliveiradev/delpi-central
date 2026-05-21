from fastapi import APIRouter

from tm_app.core.catalogs import options_payload
from tm_app.core.responses import ok

router = APIRouter(prefix="/transformometro", tags=["Transformômetro"])


@router.get("/health")
def module_health():
    return {
        "status": "online",
        "module": "transformometro",
        "phase": "1-crud",
    }
