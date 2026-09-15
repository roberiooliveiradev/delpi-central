from __future__ import annotations

from fastapi import APIRouter, File, Query, Request, UploadFile

from production_control_app.composition.pc_composer import build_product_3d_model_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import Product3DModelInvalid, Product3DModelNotFound
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Product 3D models"])


def _handle_errors(exc: Exception):
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, Product3DModelNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, Product3DModelInvalid):
        return fail(str(exc), 422)
    if isinstance(exc, ValueError):
        return fail(str(exc), 422)
    raise exc


@router.get("/product-3d-models")
def list_product_3d_models(
    request: Request,
    q: str | None = Query(default=None, description="Filtro por código ou nome do arquivo"),
):
    user = resolve_user(request)
    try:
        data = build_product_3d_model_service().list(user, search=q)
    except Exception as exc:
        return _handle_errors(exc)
    return ok(data)


@router.get("/product-3d-models/{product_code}")
def get_product_3d_model(request: Request, product_code: str):
    user = resolve_user(request)
    try:
        data = build_product_3d_model_service().get(user, product_code=product_code)
    except Exception as exc:
        return _handle_errors(exc)
    return ok(data)


@router.put("/product-3d-models/{product_code}")
async def upsert_product_3d_model(
    request: Request,
    product_code: str,
    file: UploadFile = File(..., description="Arquivo .glb do produto da OP"),
):
    user = resolve_user(request)
    payload = await file.read()
    try:
        data = build_product_3d_model_service().upsert(
            user,
            product_code=product_code,
            original_filename=file.filename,
            payload=payload,
        )
    except Exception as exc:
        return _handle_errors(exc)
    return ok(data)


@router.delete("/product-3d-models/{product_code}")
def delete_product_3d_model(request: Request, product_code: str):
    user = resolve_user(request)
    try:
        data = build_product_3d_model_service().delete(user, product_code=product_code)
    except Exception as exc:
        return _handle_errors(exc)
    return ok(data)
