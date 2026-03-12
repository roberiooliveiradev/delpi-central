# app/interface/http/routes/data_routes.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.application.dto.run_sql_request import RunSqlRequest
from app.composition.data_composer import build_run_sql_use_case

from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from delpi_auth.authorization import require_any_permission


router = APIRouter()



@router.post(
    "/sql",
    summary="Executa SQL puro (somente SELECT, com CTE e recursivo permitido).",
    response_class=JSONResponse,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                # 🔹 Opção 1: Envio JSON
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "Instrução SQL bruta (somente SELECT, pode conter quebras de linha)."
                            }
                        },
                        "required": ["sql"]
                    },
                    "example": {
                        "sql": "SELECT TOP 3 * FROM SB1010 WHERE D_E_L_E_T_ = '';"
                    }
                },
                # 🔹 Opção 2: Envio texto puro
                "text/plain": {
                    "schema": {"type": "string"},
                    "example": "SELECT TOP 3 * FROM SB1010 WHERE D_E_L_E_T_ = '';"
                }
            }
        }
    },
)
@require_any_permission(["api-delpi.access.full", "api-delpi.data"])
async def execute_sql_raw(request: Request):

    try:

        content_type = request.headers.get("content-type", "").lower()

        # JSON
        if "application/json" in content_type:
            payload = await request.json()
            sql_text = payload.get("sql", "").strip()

        # TEXT
        else:
            sql_text = (await request.body()).decode("utf-8").strip()

        if not sql_text:
            return error_response("Empty body — SQL not provided.")

        dto = RunSqlRequest(sql=sql_text)

        use_case = build_run_sql_use_case()

        result = use_case.execute(dto)

        return success_response(
            data=result,
            message="SQL executed successfully."
        )

    except Exception as e:

        log_error(f"[DATA_SQL] Unexpected error: {e}")

        return error_response(str(e))