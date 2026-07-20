# app/interface/http/routes/system_routes.py

from typing import Any

from fastapi import APIRouter, Body, Query

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
    OBSERVABILITY_ACCESS,
    SQL_HEALTH_ACCESS,
    SYSTEM_METADATA_ACCESS,
)
from app.composition.query_cache_composer import get_query_cache_backend_name, get_query_cache_storage
from app.config import settings
from app.domain.services.caller_request_stats_service import get_caller_stats_summary
from app.domain.services.console_alerts_service import (
    build_console_health_summary,
    list_console_alert_history,
    process_console_alerts,
)
from app.domain.services.envelope_contract_service import load_envelope_contract_golden
from app.domain.services.observability_snapshot_service import build_observability_snapshot
from app.domain.services.openapi_diff_service import diff_openapi_against_baseline
from app.domain.services.query_cache_stats_service import build_query_cache_stats_payload
from app.domain.services.smoke_definitions_service import load_smoke_definitions
from app.domain.services.sql_query_telemetry_service import get_sql_health_summary

router = APIRouter()


@router.get("/tables/search", summary="Busca tabelas por descrição (SX2)", operation_id="search_tables_by_description")
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


@router.get("/tables/{tableName}", summary="Consulta informações de tabela", operation_id="get_protheus_table")
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


@router.get("/tables/{tableName}/columns", summary="Consulta colunas de tabela com paginação", operation_id="list_protheus_table_columns")
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


@router.get("/tables/{tableName}/indexes", summary="Consulta índices (SIX010)", operation_id="get_protheus_table_indexes")
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


@router.get("/tables/{tableName}/relations", summary="Consulta relacionamentos (SX9010)", operation_id="get_protheus_table_relations")
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


@router.get("/tables/{tableName}/schema", summary="Schema completo da tabela (SX2, SX3, SIX, SX9)", operation_id="get_protheus_table_schema")
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


@router.get("/tables/{tableName}/columns/search", summary="Buscar colunas por texto", operation_id="search_protheus_columns_in_table")
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
, operation_id="search_protheus_columns_by_description")
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


@router.get("/smoke-definitions", summary="Definições das smoke suites do console", operation_id="get_smoke_definitions")
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


@router.get("/openapi-diff", summary="Diff do OpenAPI atual vs baseline versionado", operation_id="get_openapi_diff")
@require_any_permission(OBSERVABILITY_ACCESS)
def get_openapi_diff():
    try:
        from app.main import app

        payload = diff_openapi_against_baseline(app.openapi())
        return api_delpi_success(
            payload,
            operation_id="get_openapi_diff",
            message="Diff OpenAPI calculado com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao calcular diff OpenAPI: {e}")
        return error_response("Erro ao calcular diff OpenAPI.", status_code=500)


@router.get("/envelope-contracts", summary="Golden files de contrato de envelope (smoke)", operation_id="get_envelope_contracts")
@require_any_permission(OBSERVABILITY_ACCESS)
def get_envelope_contracts():
    try:
        payload = load_envelope_contract_golden()
        return api_delpi_success(
            payload,
            operation_id="get_envelope_contracts",
            message="Contratos de envelope carregados com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao carregar contratos de envelope: {e}")
        return error_response("Erro ao carregar contratos de envelope.", status_code=500)


@router.get("/query-cache/stats", summary="Hits e misses do cache compartilhado (LMP, estoque)", operation_id="get_query_cache_stats")
@require_any_permission(OBSERVABILITY_ACCESS)
def get_query_cache_stats():
    try:
        storage = get_query_cache_storage()
        keys_by_namespace = storage.count_keys_by_namespace() if storage else {}
        payload = build_query_cache_stats_payload(
            backend=get_query_cache_backend_name(),
            ttl_seconds=float(settings.QUERY_CACHE_TTL_SECONDS or 300),
            keys_by_namespace=keys_by_namespace,
        )
        return api_delpi_success(
            payload,
            operation_id="get_query_cache_stats",
            message="Estatísticas de cache carregadas com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao carregar estatísticas de cache: {e}")
        return error_response("Erro ao carregar estatísticas de cache.", status_code=500)


@router.get("/caller-stats", summary="Breakdown de requests por X-Delpi-Caller-App", operation_id="get_caller_stats")
@require_any_permission(OBSERVABILITY_ACCESS)
def get_caller_stats(limit: int = Query(25, ge=1, le=100)):
    try:
        payload = get_caller_stats_summary(limit=limit)
        return api_delpi_success(
            payload,
            operation_id="get_caller_stats",
            message="Estatísticas de callers carregadas com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao carregar estatísticas de callers: {e}")
        return error_response("Erro ao carregar estatísticas de callers.", status_code=500)


@router.get("/observability-snapshot", summary="Snapshot unificado para comparador de deploy", operation_id="get_observability_snapshot")
@require_any_permission(OBSERVABILITY_ACCESS)
def get_observability_snapshot(limit: int = Query(25, ge=1, le=100)):
    try:
        payload = build_observability_snapshot(limit=limit)
        return api_delpi_success(
            payload,
            operation_id="get_observability_snapshot",
            message="Snapshot de observabilidade capturado com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao capturar snapshot de observabilidade: {e}")
        return error_response("Erro ao capturar snapshot de observabilidade.", status_code=500)


@router.get("/console-health", summary="Saúde agregada do console para Admin Stats", operation_id="get_console_health")
@require_any_permission(OBSERVABILITY_ACCESS)
def get_console_health():
    try:
        payload = build_console_health_summary()
        return api_delpi_success(
            payload,
            operation_id="get_console_health",
            message="Saúde do console carregada com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao carregar saúde do console: {e}")
        return error_response("Erro ao carregar saúde do console.", status_code=500)


@router.get("/console-alerts", summary="Histórico recente de alertas do console", operation_id="get_console_alerts")
@require_any_permission(OBSERVABILITY_ACCESS)
def get_console_alerts(limit: int = Query(25, ge=1, le=100)):
    try:
        payload = list_console_alert_history(limit=limit)
        return api_delpi_success(
            payload,
            operation_id="get_console_alerts",
            message="Alertas do console carregados com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao carregar alertas do console: {e}")
        return error_response("Erro ao carregar alertas do console.", status_code=500)


@router.post("/console-alerts/evaluate", summary="Avalia alertas (p95, SQL) e opcionalmente dispara webhook", operation_id="evaluate_console_alerts")
@require_any_permission(OBSERVABILITY_ACCESS)
def post_console_alerts_evaluate(notify: bool = Query(True)):
    try:
        payload = process_console_alerts(smoke_result=None, notify=notify)
        return api_delpi_success(
            payload,
            operation_id="evaluate_console_alerts",
            message="Alertas avaliados com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao avaliar alertas do console: {e}")
        return error_response("Erro ao avaliar alertas do console.", status_code=500)


@router.post("/console-alerts/smoke", summary="Registra resultado de smoke e dispara alertas", operation_id="notify_console_smoke_alerts")
@require_any_permission(CONSOLE_SMOKE_ACCESS)
def post_console_alerts_smoke(
    smoke_result: dict[str, Any] = Body(...),
    notify: bool = Query(True),
):
    try:
        payload = process_console_alerts(smoke_result=smoke_result, notify=notify)
        return api_delpi_success(
            payload,
            operation_id="notify_console_smoke_alerts",
            message="Resultado de smoke processado com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao processar alertas de smoke: {e}")
        return error_response("Erro ao processar alertas de smoke.", status_code=500)


@router.get("/sql-health", summary="Telemetria SQL recente (ring buffer memória ou Redis)", operation_id="get_sql_health")
@require_any_permission(SQL_HEALTH_ACCESS)
def get_sql_health(
    limit: int = Query(25, ge=1, le=100),
    operation_id: str | None = Query(
        None,
        description="Filtra drill-down por operation id; use __none__ para amostras sem id.",
    ),
):
    try:
        payload = get_sql_health_summary(limit=limit, operation_id=operation_id)
        return api_delpi_success(
            payload,
            operation_id="get_sql_health",
            message="Telemetria SQL carregada com sucesso.",
        )
    except Exception as e:
        log_error(f"Erro ao carregar telemetria SQL: {e}")
        return error_response("Erro ao carregar telemetria SQL.", status_code=500)