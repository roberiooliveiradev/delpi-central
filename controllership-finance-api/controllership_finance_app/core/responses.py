from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def ok(
    data: Any = None,
    message: str = "OK",
    status_code: int = 200,
    *,
    operation_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "success": True,
        "message": message,
        "data": jsonable_encoder(data),
    }
    extra: dict[str, Any] = {}
    if operation_id:
        extra["operationId"] = operation_id
    if meta:
        extra.update(meta)
    if extra:
        content["meta"] = extra
    return JSONResponse(status_code=status_code, content=content)


def fail(
    message: str,
    status_code: int = 400,
    data: Any = None,
    *,
    operation_id: str | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "success": False,
        "message": message,
        "data": jsonable_encoder(data),
    }
    if operation_id:
        content["meta"] = {"operationId": operation_id}
    return JSONResponse(status_code=status_code, content=content)
