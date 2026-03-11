# app/interface/http/routes/product_routes.py
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

from typing import Optional
from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.list_products_requests import ListProductsRequest
from app.application.dto.list_product_structured_request import ListProductStructureRequest
from app.application.dto.list_product_parents_request import ListProductParentsRequest
from app.application.dto.export_structure_excel_request import ExportStructureExcelRequest


from app.composition.product_composer import (
    build_search_products_use_case,
    build_list_structure_use_case,
    build_export_structure_excel_use_case,
    build_list_parents_use_case,
    )



router = APIRouter()

@router.get("/search")
@require_permission("api-delpi.access")
def search_products_route(
    code: Optional[str] = Query(None),
    group_code: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort: Optional[str]=Query(None),
    direction: Optional[str] = Query(None)
):
    try:

        dto = ListProductsRequest(
            code=code,
            group_code=group_code,
            description=description,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
        )

        use_case = build_search_products_use_case()

        result = use_case.execute(dto)

        return success_response(data=result.to_dict())

    except Exception as e:
        log_error(f"Erro ao buscar produtos: {e}")
        return error_response(str(e))

@router.get("/structure/{code}")
@require_permission("api-delpi.access")
def get_structure(
    code: str,
    max_depth: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None
):

    try:

        dto = ListProductStructureRequest(
            code=code,
            max_depth=max_depth,
            page=page,
            page_size=page_size
        )

        use_case = build_list_structure_use_case()

        result = use_case.execute(dto)

        return success_response(data=result)

    except Exception as e:
        log_error(f"Erro ao buscar estrutura do produto {code}: {e}")
        return error_response(str(e))

@router.get("/{code}/structure/excel")
@require_permission("api-delpi.access")
async def structure_excel_public(
    request: Request,
    code: str,
    format: str = Query("json")
):

    try:

        dto = ExportStructureExcelRequest(code=code)

        use_case = build_export_structure_excel_use_case()

        excel_stream = use_case.execute(dto)

        filename = f"Estrutura_{code}.xlsx"

        if format.lower() == "xlsx":

            return StreamingResponse(
                excel_stream,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

        public_url = str(request.url.replace(query="format=xlsx"))

        return JSONResponse(
            content={
                "message": "Arquivo Excel gerado com sucesso!",
                "download_url": public_url
            }
        )

    except Exception as e:

        log_error(f"Erro ao gerar planilha Excel pública de {code}: {e}")

        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
    
@router.get("/{code}/parents")
@require_permission("api-delpi.access")
def parents(
    code: str,
    max_depth: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None
):

    try:

        dto = ListProductParentsRequest(
            code=code,
            max_depth=max_depth,
            page=page,
            page_size=page_size
        )

        use_case = build_list_parents_use_case()

        result = use_case.execute(dto)

        data = {
            "structure": result["structure"],
            "pagination": result["pagination"].to_dict() if result["pagination"] else None
        }

        return success_response(data=data)

    except Exception as e:

        log_error(f"Erro ao consultar pais do item {code}: {e}")

        return error_response(str(e))