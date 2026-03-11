# app/infrastructure/persistence/query_builder.py

class QueryBuilder:
    """
    Construtor de filtros SQL dinâmicos.

    Responsabilidades:
    - construir cláusulas WHERE
    - controlar parâmetros
    """

    def __init__(self):

        self._filters = []
        self._params = []

    # ----------------------------------
    # Operadores
    # ----------------------------------

    def like(self, field: str, value: str):

        if value:
            self._filters.append(f"{field} LIKE ?")
            self._params.append(f"%{value}%")

    def eq(self, field: str, value):

        if value is not None:
            self._filters.append(f"{field} = ?")
            self._params.append(value)

    def gt(self, field: str, value):

        if value is not None:
            self._filters.append(f"{field} > ?")
            self._params.append(value)

    def lt(self, field: str, value):

        if value is not None:
            self._filters.append(f"{field} < ?")
            self._params.append(value)

    def raw(self, condition: str):

        if condition:
            self._filters.append(condition)

    # ----------------------------------
    # Resultado
    # ----------------------------------

    def build(self):

        if not self._filters:
            return "1=1", []

        return " AND ".join(self._filters), self._params

    # ----------------------------------
    # Utilitário
    # ----------------------------------

    @property
    def params(self):

        return tuple(self._params)