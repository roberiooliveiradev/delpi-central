from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def ok(
    data: Any = None,
    message: str = "OK",
    status_code: int = 200,
    *,
    operation_id: str | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "success": True,
        "message": message,
        "data": jsonable_encoder(data),
    }
    if operation_id:
        content["meta"] = {"operationId": operation_id}
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
