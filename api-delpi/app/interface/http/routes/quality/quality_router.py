# app/interface/http/routes/quality/quality_router.py

from fastapi import APIRouter

from app.interface.http.routes.quality.nonconformity_routes import router as nonconformity_router
from app.interface.http.routes.quality.kaizen_routes import router as kaizen_router
from app.interface.http.routes.quality.audit_5s_routes import router as audit_5s_router
from app.interface.http.routes.quality.ppm_routes import router as ppm_router

router = APIRouter(prefix="/quality", tags=["Qualidade"])

router.include_router(
    nonconformity_router,
    prefix="/nonconformities",
)

router.include_router(
    kaizen_router,
    prefix="/kaizens",
)

router.include_router(
    audit_5s_router,
    prefix="/audit-5s",
)

router.include_router(
    ppm_router,
    prefix="/ppm",
)