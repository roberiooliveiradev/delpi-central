# app/infrastructure/providers/totvs/base_repository.py

from app.infrastructure.providers.totvs.database import get_connection
from app.utils.logger import log_error
from app.core.exceptions import DatabaseConnectionError

from datetime import datetime, date
from decimal import Decimal
import json


class BaseRepository:
    """
    Base para acesso ao banco SQL Server (Protheus).

    Responsabilidades:
    - Gerenciar conexão
    - Executar queries
    - Executar JSON SQL Server (FOR JSON PATH)
    - Executar múltiplos resultsets
    - Normalizar dados retornados
    """

    def __init__(self):
        self.connection = None
        self.cursor = None

    # --------------------------------------
    # Context Manager
    # --------------------------------------

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    # --------------------------------------
    # Conexão
    # --------------------------------------

    def _connect(self):
        try:
            self.connection = get_connection()
            self.cursor = self.connection.cursor()
        except Exception as e:
            log_error(f"Erro ao conectar ao banco: {e}")
            raise DatabaseConnectionError(str(e))

    def _close(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        except Exception:
            pass

    # --------------------------------------
    # Execução de queries
    # --------------------------------------

    def execute_query(self, query: str, params: tuple = ()) -> list[dict]:
        """
        Executa query SQL e retorna lista de registros.
        """

        try:
            self.cursor.execute(query, params)

            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]

            return [
                self._normalize_row(dict(zip(columns, row)))
                for row in rows
            ]

        except Exception as e:
            log_error(f"Erro ao executar query: {e}")
            raise DatabaseConnectionError(str(e))

    def execute_one(self, query: str, params: tuple = ()) -> dict | None:
        """
        Executa query SQL e retorna apenas um registro.
        """

        try:
            self.cursor.execute(query, params)

            row = self.cursor.fetchone()

            if not row:
                return None

            columns = [desc[0] for desc in self.cursor.description]

            return self._normalize_row(dict(zip(columns, row)))

        except Exception as e:
            log_error(f"Erro ao executar query única: {e}")
            raise DatabaseConnectionError(str(e))

    def execute_scalar(self, query: str, params: tuple = ()) -> int | float | None:
        """
        Executa query que retorna um valor escalar (COUNT, SUM, etc).
        """

        result = self.execute_one(query, params)

        if not result:
            return None

        return next(iter(result.values()))

    # --------------------------------------
    # SQL Server JSON
    # --------------------------------------

    def execute_json(self, query: str, params: tuple = ()) -> dict:
        """
        Executa SQL que retorna JSON via FOR JSON PATH.
        """

        result = self.execute_one(query, params)

        if not result:
            return {}

        key = next(iter(result))
        raw_json = result[key]

        try:
            return self._clean_json_data(json.loads(raw_json))
        except json.JSONDecodeError:
            return {}

    # --------------------------------------
    # Múltiplos resultsets
    # --------------------------------------

    def execute_query_multiple(self, query: str, params: tuple = ()) -> list[dict]:
        """
        Executa SQL com múltiplos SELECTs.
        """

        try:
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

    # --------------------------------------
    # Normalização de dados
    # --------------------------------------

    def _normalize_row(self, row: dict) -> dict:
        for key, value in row.items():
            if isinstance(value, (datetime, date)):
                row[key] = value.isoformat()

            elif isinstance(value, Decimal):
                row[key] = float(value)

            elif isinstance(value, str):
                row[key] = value.strip()

            elif value is None:
                row[key] = ""

        return row

    def _clean_json_data(self, data):
        if isinstance(data, list):
            return [self._clean_json_data(item) for item in data]

        elif isinstance(data, dict):
            cleaned = {}

            for key, value in data.items():
                if isinstance(value, str):
                    value = value.strip()

                    if value.startswith("{") or value.startswith("["):
                        try:
                            value = json.loads(value)
                            value = self._clean_json_data(value)
                        except Exception:
                            pass

                elif isinstance(value, (list, dict)):
                    value = self._clean_json_data(value)

                cleaned[key] = value

            return cleaned

        return data