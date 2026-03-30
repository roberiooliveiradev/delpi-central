# app/infrastructure/persistence/totvs/query_builder.py
from typing import Optional, Union, Iterable
from datetime import datetime


class QueryBuilder:
    """
    Construtor de filtros SQL dinâmicos.

    Responsabilidades:
    - construir cláusulas WHERE
    - controlar parâmetros
    - evitar SQL manual repetido
    """

    def __init__(self):
        self._filters = []
        self._params = []

    # --------------------------------------------------
    # OPERADORES BÁSICOS
    # --------------------------------------------------

    def eq(self, field: str, value):

        if value is not None:
            self._filters.append(f"{field} = ?")
            self._params.append(value)

    def ne(self, field: str, value):

        if value is not None:
            self._filters.append(f"{field} <> ?")
            self._params.append(value)

    def like(self, field: str, value: Optional[str], case_insensitive: bool = False):

        if value:

            if case_insensitive:
                self._filters.append(f"LOWER({field}) LIKE ?")
                self._params.append(f"%{value.lower()}%")
            else:
                self._filters.append(f"{field} LIKE ?")
                self._params.append(f"%{value}%")

    def gt(self, field: str, value):

        if value is not None:
            self._filters.append(f"{field} > ?")
            self._params.append(value)

    def gte(self, field: str, value):

        if value is not None:
            self._filters.append(f"{field} >= ?")
            self._params.append(value)

    def lt(self, field: str, value):

        if value is not None:
            self._filters.append(f"{field} < ?")
            self._params.append(value)

    def lte(self, field: str, value):

        if value is not None:
            self._filters.append(f"{field} <= ?")
            self._params.append(value)

    # --------------------------------------------------
    # LISTAS
    # --------------------------------------------------

    def in_list(self, field: str, values: Optional[Iterable]):

        if not values:
            return

        values = list(values)

        placeholders = ",".join("?" for _ in values)

        self._filters.append(f"{field} IN ({placeholders})")

        self._params.extend(values)

    # --------------------------------------------------
    # BETWEEN
    # --------------------------------------------------

    def between(self, field: str, start, end):

        if start is not None and end is not None:
            self._filters.append(f"{field} BETWEEN ? AND ?")
            self._params.extend([start, end])

        elif start is not None:
            self.gte(field, start)

        elif end is not None:
            self.lte(field, end)

    # --------------------------------------------------
    # DATAS (PROTHEUS)
    # --------------------------------------------------

    def date_range(
        self,
        field: str,
        start: Optional[Union[str, datetime]],
        end: Optional[Union[str, datetime]],
    ):

        start = self.convert_date_to_protheus(start)
        end = self.convert_date_to_protheus(end)

        self.between(field, start, end)

    # --------------------------------------------------
    # NULL
    # --------------------------------------------------

    def is_null(self, field: str):

        self._filters.append(f"{field} IS NULL")

    def is_not_null(self, field: str):

        self._filters.append(f"{field} IS NOT NULL")

    # --------------------------------------------------
    # RAW SQL
    # --------------------------------------------------

    def raw(self, condition: str):

        if condition:
            self._filters.append(condition)

    # --------------------------------------------------
    # CONDICIONAL
    # --------------------------------------------------

    def when(self, condition: bool, callback):

        if condition:
            callback(self)

    # --------------------------------------------------
    # RESULTADO
    # --------------------------------------------------

    def build(self):

        if not self._filters:
            return "1=1", ()

        return " AND ".join(self._filters), tuple(self._params)

    # --------------------------------------------------
    # UTILITÁRIOS
    # --------------------------------------------------

    def reset(self):

        self._filters.clear()
        self._params.clear()

    @property
    def params(self):

        return tuple(self._params)

    @property
    def has_filters(self):

        return len(self._filters) > 0

    # --------------------------------------------------
    # CONVERSÃO DE DATA (PROTHEUS)
    # --------------------------------------------------

    def convert_date_to_protheus(
        self,
        date_value: Optional[Union[str, datetime]]
    ) -> Optional[str]:

        """
        Converte vários formatos de data para 'YYYYMMDD' (padrão Protheus).
        """

        if not date_value:
            return None

        if isinstance(date_value, datetime):
            return date_value.strftime("%Y%m%d")

        if not isinstance(date_value, str):
            return None

        date_value = date_value.strip()

        if date_value.isdigit() and len(date_value) == 8:
            return date_value

        known_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y%m%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in known_formats:
            try:
                parsed = datetime.strptime(date_value, fmt)
                return parsed.strftime("%Y%m%d")
            except ValueError:
                continue

        try:
            parsed = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            return parsed.strftime("%Y%m%d")
        except Exception:
            return None