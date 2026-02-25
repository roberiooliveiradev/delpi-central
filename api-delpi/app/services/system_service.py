# app/services/system_service.py

from app.repositories.system_repository import SystemRepository
from app.models.product_model import Product
from app.utils.logger import log_info, log_error
from app.core.exceptions import BusinessLogicError, DatabaseConnectionError

def get_columns_table(tableName: str, page: int = 1, limit: int = 50) -> dict:
    """
    Busca as colunas de uma tabela com paginação e totalização.
    """
    repo = SystemRepository()
    log_info(f"Iniciando consulta às colunas da tabela {tableName} (página {page}, limite {limit}) via repositório")
    try:
        result = repo.get_columns_table(tableName, page, limit)
        return result
    except BusinessLogicError as e:
        log_error(str(e))
        raise
    except Exception as e:
        log_error(f"Erro inesperado ao buscar colunas da tabela {tableName}: {e}")
        raise DatabaseConnectionError(str(e))

def get_table(tableName: str) ->dict:
    """
    Busca uma tabela no Protheus via repositório.
    """
    repo = SystemRepository()
    log_info(f"Iniciando consulta a tabela {tableName} via repositório")
    try:
        result = repo.get_table(tableName)
        return result
    except BusinessLogicError as e:
        log_error(str(e))
        raise
    except Exception as e:
        log_error(f"Erro inesperado ao buscar tabela {tableName}: {e}")
        raise DatabaseConnectionError(str(e))

def get_tables(page: int = 1, limit: int = 10) -> list[dict]:
    """
    Lista tabelas do Protheus com suporte à paginação.
    """
    repo = SystemRepository()
    offset = (page - 1) * limit
    log_info(f"Listando tabelas (página {page}, limite {limit})...")
    try:
        results = repo.get_all_tables(limit, offset)
        return {
            "page": page,
            "limit": limit,
            "results": results
        }
    except Exception as e:
        log_error(f"Erro ao listar tabelas: {e}")
        raise DatabaseConnectionError(str(e))

def search_table_by_description(description: str, page: int = 1, limit: int = 20) -> dict:
    """
    Busca tabelas no Protheus pela descrição (X2_NOME), 
    com suporte a múltiplas palavras, variações de LIKE e paginação.
    """
    repo = SystemRepository()
    log_info(f"Buscando tabelas com descrição semelhante a '{description}' (página {page}, limite {limit})")

    try:
        result = repo.search_table_for_description(description, page, limit)

        if not result or not result.get("data"):
            raise BusinessLogicError(f"Nenhuma tabela encontrada para '{description}'.")

        return {
            "success": True,
            "message": f"{len(result['data'])} resultados encontrados para '{description}'",
            "page": result.get("page", page),
            "page_size": result.get("page_size", limit),
            "total_records": result.get("total_records", 0),
            "total_pages": result.get("total_pages", 1),
            "results": result["data"]
        }

    except BusinessLogicError as e:
        log_error(f"Nenhuma tabela encontrada: {e}")
        raise
    except Exception as e:
        log_error(f"Erro inesperado ao buscar descrição '{description}': {e}")
        raise DatabaseConnectionError(str(e))
    
def get_table_indexes(tableName: str):
    repo = SystemRepository()
    log_info(f"Service: buscando índices da tabela {tableName}")
    return repo.get_table_indexes(tableName)


def get_table_relations(tableName: str):
    repo = SystemRepository()
    log_info(f"Service: buscando relacionamentos da tabela {tableName}")
    return repo.get_table_relations(tableName)


def search_columns_in_table(tableName: str, text: str):
    repo = SystemRepository()
    log_info(f"Service: buscando colunas da tabela {tableName} contendo '{text}'")
    return repo.search_columns(tableName, text)

def search_columns_by_description(description: str, page: int = 1, limit: int = 20) -> dict:
    """
    Busca colunas em todas as tabelas do Protheus pela descrição semântica (SX3010),
    retornando tabela, coluna e score de similaridade.
    """
    repo = SystemRepository()
    log_info(
        f"Service: buscando colunas por descrição semelhante a '{description}' "
        f"(página {page}, limite {limit})"
    )

    try:
        result = repo.search_columns_by_description(
            description=description,
            page=page,
            page_size=limit
        )

        if not result or not result.get("data"):
            raise BusinessLogicError(
                f"Nenhuma coluna encontrada para a descrição '{description}'."
            )

        return {
            "success": True,
            "message": f"{len(result['data'])} colunas encontradas para '{description}'",
            "page": result.get("page", page),
            "page_size": result.get("page_size", limit),
            "total_records": result.get("total_records", 0),
            "total_pages": result.get("total_pages", 1),
            "results": result["data"]
        }

    except BusinessLogicError as e:
        log_error(str(e))
        raise
    except Exception as e:
        log_error(
            f"Erro inesperado ao buscar colunas por descrição '{description}': {e}"
        )
        raise DatabaseConnectionError(str(e))

def get_table_schema(tableName: str):
    repo = SystemRepository()
    log_info(f"Service: montando schema completo da tabela {tableName}")
    return repo.get_table_schema(tableName)
