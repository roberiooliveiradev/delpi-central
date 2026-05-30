# app/core/responses.py
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(data: Any, message: str = "Operação realizada com sucesso"):
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": message,
            "data": jsonable_encoder(data),
        },
    )

def error_response(message: str, status_code: int = 400):
    return JSONResponse(status_code=status_code, content={"success": False, "message": message})
