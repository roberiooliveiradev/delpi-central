# app/core/exceptions.py
from fastapi import HTTPException

class DatabaseConnectionError(HTTPException):
    def __init__(self, detail: str = "Erro ao conectar ao banco de dados."):
        super().__init__(status_code=500, detail=detail)

class BusinessLogicError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)
