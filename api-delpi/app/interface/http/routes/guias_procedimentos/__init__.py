from app.interface.http.routes.guias_procedimentos.guias_procedimentos_router import (
    router,
)
from app.interface.http.routes.guias_procedimentos.guias_procedimentos_media_router import (
    admin_media_router,
    read_media_router,
)

__all__ = ["router", "admin_media_router", "read_media_router"]
