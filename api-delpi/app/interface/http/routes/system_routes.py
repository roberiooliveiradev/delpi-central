# app/interface/http/routes/system_routes.py

from fastapi import APIRouter, Query

from app.application.dto.system.system_requests import (
    GetTableRequest,
    ListTableColumnsRequest,
    SearchTablesByDescriptionRequest,
    GetTableIndexesRequest,
    GetTableRelationsRequest,
    GetTableSchemaRequest,
    SearchColumnsInTableRequest,
    SearchColumnsByDescriptionRequest,
)
from app.composition.system_composer import (
    build_get_table_use_case,
    build_list_table_columns_use_case,
    build_search_tables_by_description_use_case,
    build_get_table_indexes_use_case,
    build_get_table_relations_use_case,
    build_get_table_schema_use_case,
    build_search_columns_in_table_use_case,
    build_search_columns_by_description_use_case,
)
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.core.exceptions import DatabaseConnectionError, BusinessLogicError
from app.utils.logger import log_info, log_error

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    CONSOLE_SMOKE_ACCESS,
    SQL_HEALTH_ACCESS,
    SYSTEM_METADATA_ACCESS,
)
from app.domain.services.smoke_definitions_service import load_smoke_definitions
from app.domain.services.sql_query_telemetry_service import get_sql_health_summary

router = APIRouter()


@router.get("/tables/search", summary="Busca tabelas por descrição (SX2)")
@require_any_permission(SYSTEM_METADATA_ACCESS)
def search_tables(
    description: str = Query(..., min_length=2, description="Descrição parcial ou completa da tabela"),
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(20, ge=1, le=200, description="Quantidade de registros por página"),
):
    log_info(
        f"Iniciando busca de tabelas com descrição semelhante a "
        f"'{description}' (página {page}, limite {limit})"
    )

    try:
        dto = SearchTablesByDescriptionRequest(
            description=description,
            page=page,
            limit=limit,
        )

        use_case = build_search_tables_by_description_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="search_tables_by_description",
            message="Busca de tabelas realizada com sucesso!",
        )

    except BusinessLogicError as e:
        log_error(f"Nenhuma tabela encontrada para '{description}': {e}")
        return error_response(str(e))
    except DatabaseConnectionError as e:
        log_error(f"Erro de conexão ao buscar tabelas: {e}")
        return error_response(f"Erro de conexão com o banco de dados: {e}")
    except Exception as e:
        log_error(f"Erro inesperado ao buscar tabelas com descrição '{description}': {e}")
        return error_response(f"Erro inesperado: {e}")


@router.get("/tables/{tableName}", summary="Consulta informações de tabela")
@require_any_permission(SYSTEM_METADATA_ACCESS)
def table(tableName: str):
    try:
        dto = GetTableRequest(table_name=tableName)
        use_case = build_get_table_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="get_protheus_table",
            message="Tabela localizada com sucesso!",
        )

    except Exception as e:
        log_error(f"Erro ao consultar informações da tabela {tableName}: {e}")
        return error_response(f"Erro inesperado: {e}")


@router.get("/tables/{tableName}/columns", summary="Consulta colunas de tabela com paginação")
@require_any_permission(SYSTEM_METADATA_ACCESS)
def table_columns(
    tableName: str,
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(50, ge=1, le=200, description="Quantidade de registros por página"),
):
    log_info(
        f"Consultando colunas da tabela {tableName} "
        f"(página {page}, limite {limit})"
    )

    try:
        dto = ListTableColumnsRequest(
            table_name=tableName,
            page=page,
            limit=limit,
        )

        use_case = build_list_table_columns_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="list_protheus_table_columns",
            message=f"Colunas da tabela {tableName} retornadas com sucesso!",
        )

    except BusinessLogicError as e:
        log_error(f"Nenhuma coluna encontrada para '{tableName}': {e}")
        return error_response(str(e))
    except Exception as e:
        log_error(f"Erro ao consultar colunas da tabela {tableName}: {e}")
        return error_response(f"Erro inesperado: {e}")


@router.get("/tables/{tableName}/indexes", summary="Consulta índices (SIX010)")
@require_any_permission(SYSTEM_METADATA_ACCESS)
def table_indexes(tableName: str):
    try:
        dto = GetTableIndexesRequest(table_name=tableName)
        use_case = build_get_table_indexes_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="get_protheus_table_indexes",
            message="Índices retornados com sucesso!",
        )

    except Exception as e:
        log_error(f"Erro ao consultar índices da tabela {tableName}: {e}")
        return error_response(str(e))


@router.get("/tables/{tableName}/relations", summary="Consulta relacionamentos (SX9010)")
@require_any_permission(SYSTEM_METADATA_ACCESS)
def table_relations(tableName: str):
    try:
        dto = GetTableRelationsRequest(table_name=tableName)
        use_case = build_get_table_relations_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="get_protheus_table_relations",
            message="Relacionamentos retornados com sucesso!",
        )

    except Exception as e:
        log_error(f"Erro ao consultar relacionamentos da tabela {tableName}: {e}")
        return error_response(str(e))


@router.get("/tables/{tableName}/schema", summary="Schema completo da tabela (SX2, SX3, SIX, SX9)")
@require_any_permission(SYSTEM_METADATA_ACCESS)
def table_schema(tableName: str):
    try:
        dto = GetTableSchemaRequest(table_name=tableName)
        use_case = build_get_table_schema_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="get_protheus_table_schema",
            message="Schema completo retornado!",
        )

    except Exception as e:
        log_error(f"Erro ao consultar schema da tabela {tableName}: {e}")
        return error_response(str(e))


@router.get("/tables/{tableName}/columns/search", summary="Buscar colunas por texto")
@require_any_permission(SYSTEM_METADATA_ACCESS)
def search_columns(tableName: str, q: str = Query(..., min_length=2)):
    try:
        dto = SearchColumnsInTableRequest(
            table_name=tableName,
            text=q,
        )

        use_case = build_search_columns_in_table_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="search_protheus_columns_in_table",
            message=f"Colunas contendo '{q}' retornadas!",
        )

    except Exception as e:
        log_error(f"Erro ao buscar colunas por texto na tabela {tableName}: {e}")
        return error_response(str(e))


@router.get(
    "/columns/search",
    summary="Busca colunas por descrição (SX3010 + ranking semântico)"
)
@require_any_permission(SYSTEM_METADATA_ACCESS)
def search_columns_global(
    description: str = Query(
        ...,
        min_length=2,
        description="Texto descritivo da coluna (ex: 'Amarração produto fornecedor')"
    ),
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(20, ge=1, le=200, description="Quantidade de registros por página"),
):
    log_info(
        f"Iniciando busca global de colunas por descrição '{description}' "
        f"(página {page}, limite {limit})"
    )

    try:
        dto = SearchColumnsByDescriptionRequest(
            description=description,
            page=page,
            limit=limit,
        )

        use_case = build_search_columns_by_description_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="search_protheus_columns_by_description",
            message="Busca de colunas realizada com sucesso!",
        )

    except BusinessLogicError as e:
        log_error(f"Nenhuma coluna encontrada: {e}")
        return error_response(str(e))
    except DatabaseConnectionError as e:
        log_error(f"Erro de conexão ao buscar colunas: {e}")
        return error_response(f"Erro de conexão com o banco de dados: {e}")
    except Exception as e:
        log_error(f"Erro inesperado ao buscar colunas: {e}")
        return error_response(f"Erro inesperado: {e}")


@router.get("/smoke-definitions", summary="Definições das smoke suites do console")
@require_any_permission(CONSOLE_SMOKE_ACCESS)
def get_smoke_definitions():
    try:
        payload = load_smoke_definitions()
        return api_delpi_success(
            payload,
            operation_id="get_smoke_definitions",
            message="Definições de smoke carregadas com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao carregar smoke definitions: {e}")
        return error_response("Erro ao carregar definições de smoke.", status_code=500)


@router.get("/sql-health", summary="Telemetria SQL recente (ring buffer em memória)")
@require_any_permission(SQL_HEALTH_ACCESS)
def get_sql_health(limit: int = Query(25, ge=1, le=100)):
    try:
        payload = get_sql_health_summary(limit=limit)
        return api_delpi_success(
            payload,
            operation_id="get_sql_health",
            message="Telemetria SQL carregada com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao carregar telemetria SQL: {e}")
        return error_response("Erro ao carregar telemetria SQL.", status_code=500)