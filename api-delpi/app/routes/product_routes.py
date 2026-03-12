from fastapi import APIRouter, HTTPException, Query, Request
from app.services.product_service import get_product, get_structure, get_parents, get_guide, get_inspection, get_product_analyser, get_customers, get_structure_excel
from app.services.product_service import get_suppliers, get_inbound_invoice_items, get_outbound_invoice_items, get_stock, search_products_by_description
from app.services.product_service import get_purchases, get_products_paginated, search_products, get_sales_summary, get_sales_open_orders, get_sales_billing, get_product_pricing, get_internal_movements
from app.core.responses import success_response, error_response
from app.core.exceptions import DatabaseConnectionError
from app.utils.logger import log_info, log_error
from app.repositories.base_repository import BaseRepository
from pydantic import BaseModel
from typing import Optional
from app.models.product_model import ProductSearchRequest
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse

from delpi_auth.authorization import require_permission


router = APIRouter()



# @router.get("/search")
# @require_permission("api-delpi.access")
# def search_products_route(
#     code: Optional[str] = Query(None),
#     group: Optional[str] = Query(None),
#     description: Optional[str] = Query(None),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500)
# ):
#     try:
#         result = search_products(code, group, description, page, page_size)
#         return success_response(data=result)
#     except Exception as e:
#         return error_response(str(e))


# @router.get(
#     "/search/description",
#     summary="Busca específica por descrição, com paginação e score"
# )
# @require_permission("api-delpi.access")
# def search_products_by_description_route(
#     description: str = Query(..., description="Descrição ou termos"),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500),
# ):
#     try:
#         result = search_products_by_description(description, page, page_size)
#         return success_response(
#             data=result,
#             message=f"Busca por descrição realizada com sucesso (página {page}/{result['total_pages']})."
#         )
#     except Exception as e:
#         log_error(f"Erro na busca pela descrição: {e}")
#         return error_response(f"Erro inesperado: {e}")


# @router.get(
#     "",
#     summary="Lista produtos paginados"
# )
# @require_permission("api-delpi.access")
# def list_products(
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500)
# ):
#     try:
#         result = get_products_paginated(page, page_size)

#         return success_response(
#             data=result,
#             message=f"Produtos retornados com sucesso (página {page}/{result['total_pages']})."
#         )

#     except Exception as e:
#         log_error(f"Erro ao listar produtos: {e}")
#         return error_response(f"Erro inesperado: {e}")


# @router.get("/{code}", summary="Consulta produto por código")
# def product(code: str):
#     try:
#         product = get_product(code)

#         return success_response(
#             data={"produto": product.model_dump()},  
#             message="Produto localizado com sucesso!"
#         )

#     except Exception as e:
#         log_error(f"Erro ao consultar produto {code}: {e}")
#         return error_response(f"Erro inesperado: {e}")


# @router.get("/{code}/structure", summary="Consulta estrutura (BOM) paginada via CTE")
# def structure(
#     code: str,
#     max_depth: int = Query(10, ge=1, le=15),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(100, ge=1, le=500)
# ):
#     """
#     Retorna a estrutura (BOM) via CTE com suporte a paginação.
#     """
#     try:
#         result = get_structure(code, max_depth, page, page_size)
#         return success_response(
#             data=result,
#             message=f"Estrutura do produto {code} retornada com sucesso (página {page}/{result['total_pages']})."
#         )
#     except Exception as e:
#         log_error(f"Erro ao consultar estrutura do produto {code}: {e}")
#         return error_response(f"Erro inesperado: {e}")


# @router.get(
#     "/{code}/structure/excel",
#     summary="Exporta a estrutura formatada em planilha Excel (público)",
#     include_in_schema=True
# )
# async def structure_excel_public(
#     request: Request,
#     code: str,
#     format: str = Query("json", description="Use 'xlsx' para baixar o arquivo Excel")
# ):
#     """
#     Se format=xlsx → retorna StreamingResponse (arquivo)
#     Caso contrário → retorna JSON com link para download.
#     """
#     try:
#         # Sempre gera o arquivo (caso o usuário clique no link)
#         excel_file = get_structure_excel(code)
#         filename = f"Estrutura_{code}.xlsx"

#         # ------------------------------
#         # Se pediu Excel → baixa arquivo
#         # ------------------------------
#         if format.lower() == "xlsx":
#             return StreamingResponse(
#                 excel_file,
#                 media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                 headers={
#                     "Content-Disposition": f"attachment; filename={filename}",
#                     "Cache-Control": "no-cache, no-store, must-revalidate",
#                     "Pragma": "no-cache",
#                     "Expires": "0",
#                 }
#             )

#         # ------------------------------
#         # Retorna JSON com link dinâmico
#         # ------------------------------
#         public_url = str(request.url.replace(query="format=xlsx"))
#         html_link = f'<a href="{public_url}" target="_blank">📂 Baixar Estrutura {code}</a>'

#         return JSONResponse(
#             content={
#                 "message": "Arquivo Excel gerado com sucesso!",
#                 "download_url": public_url,
#                 "html_link": html_link
#             }
#         )

#     except Exception as e:
#         log_error(f"Erro ao gerar planilha Excel pública de {code}: {e}")
#         return JSONResponse(content={"error": str(e)}, status_code=500)


# @router.get("/{code}/parents", summary="Consulta produtos pai (Where Used) paginada via CTE")
# def parents(
#     code: str,
#     max_depth: int = Query(10, ge=1, le=15),
#     page: int = Query(1, ge=1),
#     page_size: int = Query(100, ge=1, le=500)
# ):
#     """
#     Retorna produtos pai (Where Used) via CTE com paginação.
#     """
#     try:
#         result = get_parents(code, max_depth, page, page_size)
#         return success_response(
#             data=result,
#             message=f"Produtos pai de {code} retornados com sucesso (página {page}/{result['total_pages']})."
#         )
#     except Exception as e:
#         log_error(f"Erro ao consultar pais do item {code}: {e}")
#         return error_response(f"Erro inesperado: {e}")


# @router.get("/{code}/suppliers", summary="Consulta os fornecedores de um produto com paginação")
# def suppliers(
#     code: str,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500)
# ):
#     """
#     Retorna os fornecedores de um produto com suporte a paginação.
#     """
#     try:
#         result = get_suppliers(code, page, page_size)
#         return success_response(
#             data=result,
#             message=f"Fornecedores de {code} retornados com sucesso (página {page}/{result['total_pages']})."
#         )
#     except Exception as e:
#         log_error(f"Erro ao consultar fornecedores do item {code}: {e}")
#         return error_response(f"Erro inesperado: {e}")


# @router.get("/{code}/inbound-invoice-items", summary="Consulta as notas fiscais de entrada (paginadas e filtráveis)")
# def inbound_invoice_items(
#     code: str,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500),
#     issue_date_start: Optional[str] = Query(None),
#     issue_date_end: Optional[str] = Query(None),
#     supplier: Optional[str] = Query(None),
#     branch: Optional[str] = Query(None)
# ):
#     """
#     Retorna as notas fiscais de entrada (SD1010) com paginação e filtros opcionais.
#     """
#     try:
#         result = get_inbound_invoice_items(code, page, page_size, issue_date_start, issue_date_end, supplier, branch)
#         return success_response(
#             data=result,
#             message=f"Inbound invoices for {code} fetched successfully (page {page}/{result['total_pages']})."
#         )
#     except Exception as e:
#         log_error(f"Erro ao consultar NF-es de entrada para {code}: {e}")
#         return error_response(f"Unexpected error: {e}")


# @router.get("/{code}/outbound-invoice-items", summary="Consulta as notas fiscais de saída (paginadas e filtráveis)")
# def outbound_invoice_items(
#     code: str,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500),
#     issue_date_start: Optional[str] = Query(None),
#     issue_date_end: Optional[str] = Query(None),
#     customer: Optional[str] = Query(None),
#     branch: Optional[str] = Query(None)
# ):
#     """
#     Retorna as notas fiscais de saída (SD2010) com paginação e filtros opcionais.
#     """
#     try:
#         result = get_outbound_invoice_items(code, page, page_size, issue_date_start, issue_date_end, customer, branch)
#         return success_response(
#             data=result,
#             message=f"Outbound invoices for {code} fetched successfully (page {page}/{result['total_pages']})."
#         )
#     except Exception as e:
#         log_error(f"Erro ao consultar NF-es de saída para {code}: {e}")
#         return error_response(f"Unexpected error: {e}")


# @router.get(
#     "/{code}/purchases",
#     summary="Histórico resumido de compras do produto"
# )
# def purchases(
#     code: str,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500)
# ):
#     try:
#         result = get_purchases(code, page, page_size)
#         return success_response(
#             data=result,
#             message=f"Histórico de compras de {code} retornado com sucesso (página {page}/{result['total_pages']})."
#         )
#     except Exception as e:
#         log_error(f"Erro ao consultar compras do item {code}: {e}")
#         return error_response(f"Erro inesperado: {e}")


@router.get(
    "/{code}/sales",
    summary="Resumo consolidado de vendas do produto"
)
def product_sales_summary(code: str):
    """
    Retorna o resumo consolidado de vendas realizadas do produto.
    Base: SD2010
    """
    try:
        result = get_sales_summary(code)
        return success_response(
            data=result,
            message=f"Resumo de vendas do produto {code} retornado com sucesso."
        )
    except Exception as e:
        log_error(f"Erro ao consultar vendas do produto {code}: {e}")
        return error_response(f"Erro inesperado: {e}")


@router.get(
    "/{code}/sales/open-orders",
    summary="Carteira de pedidos de venda do produto"
)
def product_sales_open_orders(code: str):
    """
    Retorna a carteira de pedidos de venda (abertos).
    Base: SC5010
    """
    try:
        result = get_sales_open_orders(code)
        return success_response(
            data=result,
            message=f"Carteira de pedidos do produto {code} retornada com sucesso."
        )
    except Exception as e:
        log_error(f"Erro ao consultar carteira do produto {code}: {e}")
        return error_response(f"Erro inesperado: {e}")



@router.get(
    "/{code}/sales/billing",
    summary="Resumo de faturamento do produto"
)
def product_sales_billing(code: str):
    """
    Retorna o resumo de faturamento financeiro do produto.
    Base: SF2010
    """
    try:
        result = get_sales_billing(code)
        return success_response(
            data=result,
            message=f"Faturamento do produto {code} retornado com sucesso."
        )
    except Exception as e:
        log_error(f"Erro ao consultar faturamento do produto {code}: {e}")
        return error_response(f"Erro inesperado: {e}")


@router.get(
    "/{code}/pricing",
    summary="Preços comerciais do produto"
)
def product_pricing(code: str):
    """
    Retorna os preços do produto conforme tabelas comerciais.
    Base: DA1010
    """
    try:
        result = get_product_pricing(code)
        return success_response(
            data=result,
            message=f"Preços do produto {code} retornados com sucesso."
        )
    except Exception as e:
        log_error(f"Erro ao consultar preços do produto {code}: {e}")
        return error_response(f"Erro inesperado: {e}")


# @router.get("/{code}/stock", summary="Consulta o estoque de um produto com filtros e paginação")
# def stock(
#     code: str,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500),
#     branch: Optional[str] = Query(None, description="Filial (B2_FILIAL)"),
#     location: Optional[str] = Query(None, description="Local (B2_LOCAL)")
# ):
#     """
#     Retorna o estoque do produto consultando a tabela SB2010.
#     Possui filtros opcionais para filial e local, além de paginação.
#     """
#     try:
#         result = get_stock(code, page, page_size, branch, location)
#         return success_response(
#             data=result,
#             message=f"Estoque de {code} retornado com sucesso (página {page}/{result['total_pages']})."
#         )
#     except Exception as e:
#         log_error(f"Erro ao consultar estoque do item {code}: {e}")
#         return error_response(f"Erro inesperado: {e}")


# @router.get(
#     "/{code}/internal-movements",
#     summary="Histórico de movimentações internas do produto"
# )
# def internal_movements(
#     code: str,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500),
#     date_start: Optional[str] = Query(None),
#     date_end: Optional[str] = Query(None),
#     branch: Optional[str] = Query(None),
#     location: Optional[str] = Query(None),
#     tm: Optional[str] = Query(None, description="Tipo de movimento (D3_TM)"),
#     op: Optional[str] = Query(None, description="Ordem de produção")
# ):
#     try:
#         result = get_internal_movements(
#             code,
#             page,
#             page_size,
#             date_start,
#             date_end,
#             branch,
#             location,
#             tm,
#             op
#         )

#         return success_response(
#             data=result,
#             message=f"Movimentações internas do produto {code} retornadas com sucesso."
#         )

#     except Exception as e:
#         log_error(f"Erro ao consultar movimentações internas de {code}: {e}")
#         return error_response(f"Erro inesperado: {e}")


# @router.get("/{code}/guide", summary="Consulta o roteiro de um produto e seus componentes com filtros e paginação")
# def guide(
#     code: str,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500),
#     branch: Optional[str] = Query(None, description="Filial (G2_FILIAL)"),
#     max_depth: int = Query(10, ge=1, le=15)
# ):
#     """
#     Retorna o roteiro do produto consultando a tabela SG2010.
#     Possui filtros opcionais para filial e local, além de paginação.
#     """
#     try:
#         result = get_guide(code, page, page_size, branch, max_depth)
#         return success_response(
#             data=result,
#             message=f"Roteiro de {code} retornado com sucesso (página {page}/{result['total_pages']})."
#         )
#     except Exception as e:
#         log_error(f"Erro ao consultar roteiro do item {code}: {e}")
#         return error_response(f"Erro inesperado: {e}")
    

# @router.get(
#     "/{code}/inspection",
#     summary="Consulta a inspeção de processos do produto e seus componentes"
# )
# def inspection(
#     code: str,
#     max_depth: int = Query(10, ge=1, le=15)
# ):
#     """
#     Retorna a inspeção do produto consultando QP6, QP7 e QP8,
#     incluindo inspeções dos componentes (via SG1010).
#     """
#     try:
#         result = get_inspection(code, max_depth)
#         return success_response(
#             data=result,
#             message=f"Inspeção de {code} retornada com sucesso."
#         )
#     except Exception as e:
#         log_error(f"Erro ao consultar inspeção do item {code}: {e}")
#         return error_response(f"Erro inesperado: {e}")


@router.get(
    "/{code}/analyser",
    summary="Análise completa do produto (genérico + BOM + roteiro + inspeções)"
)
def product_analyser(
    code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    max_depth: int = Query(10, ge=1, le=15)
):
    """
    Retorna:
    - Dados gerais do produto
    - Estrutura completa (produto + componentes)
    - Roteiro completo
    - Inspeções QP6/QP7/QP8 de produto e componentes
    """
    try:
        result = get_product_analyser(code, page, page_size, max_depth)
        return success_response(
            data=result,
            message=f"Análise completa de {code} retornada com sucesso."
        )
    except Exception as e:
        log_error(f"Erro ao analisar completamente o produto {code}: {e}")
        return error_response(f"Erro inesperado: {e}")


# @router.get("/{code}/customers", summary="Consulta os clientes amarrados a um produto com paginação")
# def customers(
#     code: str,
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=500)
# ):
#     """
#     Retorna os clientes vinculados a um produto (SA7010 — Amarração Produto x Cliente)
#     com suporte a paginação.
#     """
#     try:
#         result = get_customers(code, page, page_size)
#         return success_response(
#             data=result,
#             message=f"Clientes vinculados ao produto {code} retornados com sucesso (página {page}/{result['total_pages']})."
#         )
#     except Exception as e:
#         log_error(f"Erro ao consultar clientes do item {code}: {e}")
#         return error_response(f"Erro inesperado: {e}")

