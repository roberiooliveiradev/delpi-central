from app.repositories.base_repository import BaseRepository
from app.utils.logger import log_error

class DataRepository(BaseRepository):
    """
    Repositório para consultas dinâmicas.
    """

    def execute_raw_sql_safe(self, sql: str) -> dict:
        """
        Executa SQL bruto após validação de segurança
        (DECLARE / SET + múltiplos SELECTs).
        """
        try:
            resultsets = self.execute_query_multiple(sql)

            return {
                "success": True,
                "sql": sql,
                "total_resultsets": len(resultsets),
                "resultsets": resultsets
            }

        except Exception as e:
            log_error(f"[DATA_SQL] Erro ao executar SQL: {e}")
            return {
                "success": False,
                "message": str(e)
            }
