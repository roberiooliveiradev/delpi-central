from typing import Any
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

def _envelope(*, success: bool, message: str, data: Any = None, error: dict | None = None, meta: dict | None = None) -> dict:
    payload = {"success": success, "message": message, "data": jsonable_encoder(data) if data is not None else None, "error": error}
    if meta:
        payload["meta"] = meta
    return payload

def success_response(data: Any, message: str = "Operação realizada com sucesso", *, meta: dict | None = None):
    return JSONResponse(status_code=200, content=_envelope(success=True, message=message, data=data, error=None, meta=meta))

def error_response(message: str, status_code: int = 400, *, code: str | None = None, recoverable: bool = True, fields: list | None = None, meta: dict | None = None):
    error = {"code": code, "recoverable": recoverable} if code else None
    if error is not None and fields:
        error["fields"] = fields
    return JSONResponse(status_code=status_code, content=_envelope(success=False, message=message, data=None, error=error, meta=meta))

def not_found_response(message: str = "Recurso não encontrado", *, code: str = "NOT_FOUND"):
    return error_response(message, status_code=404, code=code, recoverable=False)
