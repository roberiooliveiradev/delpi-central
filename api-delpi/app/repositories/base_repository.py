# app/repositories/base_repository.py
from app.database import get_connection
from app.utils.logger import log_info, log_error
from app.core.exceptions import DatabaseConnectionError
from datetime import datetime, date
import json
class BaseRepository:
    """
    Classe base para acesso ao banco de dados SQL Server (Protheus).
    Fornece métodos utilitários para executar consultas e processar resultados.
    """

    def __init__(self):
        self.connection = None
        self.cursor = None

    # ---------------------------
    # 🔹 Conexão e controle
    # ---------------------------
    def connect(self):
        try:
            self.connection = get_connection()
            self.cursor = self.connection.cursor()
        except Exception as e:
            log_error(f"Erro ao conectar ao banco: {e}")
            raise DatabaseConnectionError(str(e))

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    # ---------------------------
    # 🔹 Execução de queries
    # ---------------------------
    def execute_query(self, query: str, params: tuple = ()) -> list[dict]:
        """
        Executa uma query SQL e retorna uma lista de dicionários {coluna: valor}.
        """
        try:
            self.connect()
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            result = [self._normalize_row(dict(zip(columns, row))) for row in rows]
            return result

        except Exception as e:
            log_error(f"Erro ao executar query: {e}")
            raise DatabaseConnectionError(str(e))
        finally:
            self.close()

    def execute_one(self, query: str, params: tuple = ()) -> dict | None:
        """
        Executa uma query SQL e retorna o primeiro registro (dict).
        """
        try:
            self.connect()
            self.cursor.execute(query, params)
            row = self.cursor.fetchone()
            if not row:
                return None
            columns = [desc[0] for desc in self.cursor.description]
            return self._normalize_row(dict(zip(columns, row)))
        except Exception as e:
            log_error(f"Erro ao executar query única: {e}")
            raise DatabaseConnectionError(str(e))
        finally:
            self.close()

    def execute_json(self, query: str, params: tuple = ()) -> dict:
        """
        Executa uma query SQL que retorna JSON (via FOR JSON PATH).
        Retorna o JSON já convertido para objeto Python.
        """
        result = self.execute_one(query, params)
        if not result:
            return {}
        key = next(iter(result))  # primeira (e única) chave do dict
        raw_json = result[key]
        try:
            return self._clean_json_data(json.loads(raw_json))
        except json.JSONDecodeError:
            return {}
        
    def execute_query_multiple(self, query: str, params: tuple = ()) -> list[dict]:
        """
        Executa SQL com múltiplos SELECTs e retorna múltiplos resultsets.
        Cada SELECT vira um bloco independente.
        """
        try:
            self.connect()
            self.cursor.execute(query, params)

            resultsets = []
            index = 1

            while True:
                if self.cursor.description:
                    columns = [desc[0] for desc in self.cursor.description]
                    rows = self.cursor.fetchall()

                    data = [
                        self._normalize_row(dict(zip(columns, row)))
                        for row in rows
                    ]

                    resultsets.append({
                        "index": index,
                        "columns": columns,
                        "total": len(data),
                        "data": data
                    })
                    index += 1

                if not self.cursor.nextset():
                    break

            return resultsets

        except Exception as e:
            log_error(f"Erro ao executar múltiplos SELECTs: {e}")
            raise DatabaseConnectionError(str(e))
        finally:
            self.close()

    # ---------------------------
    # 🔹 Normalização de dados
    # ---------------------------
    def _normalize_row(self, row: dict) -> dict:
        """
        Limpa e normaliza dados retornados do banco.
        - Remove espaços extras
        - Converte datetime/date para ISO
        - Substitui None por string vazia
        """
        for k, v in row.items():
            if isinstance(v, (datetime, date)):
                row[k] = v.isoformat()
            elif isinstance(v, str):
                row[k] = v.strip()
            elif v is None:
                row[k] = ""
        return row

    def _clean_json_data(self, data):
        """
        Limpa e normaliza o JSON retornado do SQL Server:
        - Remove espaços extras em strings (trim)
        - Converte sub-blocos JSON (QP6, QP7, QP8) de string para dict/list
        - Remove campos vazios
        """
        if isinstance(data, list):
            return [self._clean_json_data(item) for item in data]

        elif isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if isinstance(value, str):
                    value = value.strip()

                    # Se o campo é JSON válido (como QP6), decodifica
                    if value.startswith("{") or value.startswith("["):
                        try:
                            value = json.loads(value)
                            value = self._clean_json_data(value)
                        except Exception:
                            pass  # deixa string original se não for JSON
                elif isinstance(value, (list, dict)):
                    value = self._clean_json_data(value)

                cleaned[key] = value
            return cleaned

        else:
            return data
