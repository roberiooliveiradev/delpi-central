# app/routes/cliente_routes.py
from fastapi import APIRouter, HTTPException
from app.services.clientes_service import get_clientes
from app.core.responses import success_response, error_response
from app.core.exceptions import DatabaseConnectionError


from delpi_auth.authorization import (require_permission, require_any_permission)

router = APIRouter()

@router.get("/clientes")
@require_any_permission(["api-delpi.access.full", "api-delpi.acess"])
def listar_clientes(limite: int = 10):
    try:
        clientes = get_clientes(limite)
        return success_response(
            data={"total": len(clientes), "clientes": [c.model_dump() for c in clientes]},
            message="Consulta realizada com sucesso!"
        )
    except ConnectionError:
        raise DatabaseConnectionError("Falha ao conectar ao banco Protheus.")
    except Exception as e:
        return error_response(f"Erro inesperado: {e}")
