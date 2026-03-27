# app/interface/http/routes/engineering/engineering_router.py

from fastapi import APIRouter

from app.interface.http.routes.engineering.lmp_routes import router as lmp_router
from app.interface.http.routes.engineering.transforma_mais_routes import router as transforma_mais_router

router = APIRouter(prefix="/engineering", tags=["Engenharia"])

router.include_router(
    lmp_router,
    prefix="/lmps",
)

router.include_router(
    transforma_mais_router,
    prefix="/transforma-mais",
)