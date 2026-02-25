from app.utils.sql_validator import SqlValidator
from app.repositories.data_repository import DataRepository
from app.utils.logger import log_info, log_error

def run_raw_sql(sql: str) -> dict:
    """
    Executa SQL bruto validado (somente SELECT em tabelas autorizadas).
    """
    log_info("[DATA_SQL] Executando consulta SQL segura")
    repo = DataRepository()
    try:
        validator = SqlValidator()
        validator.validate(sql)
        return repo.execute_raw_sql_safe(sql)
    except Exception as e:
        log_error(f"[DATA_SQL] Erro na execução: {e}")
        return {"success": False, "message": str(e)}