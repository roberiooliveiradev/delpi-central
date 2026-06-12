from typing import Any

from fastapi.responses import JSONResponse

from maint_app.core.serialize import json_safe


def ok(data: Any = None, message: str = "OK", status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": json_safe(data)},
    )


def fail(message: str, status_code: int = 400, data: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message, "data": json_safe(data)},
    )
