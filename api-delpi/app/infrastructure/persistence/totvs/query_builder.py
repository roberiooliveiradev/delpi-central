# app/infrastructure/persistence/totvs/query_builder.py
from typing import Optional, Union, Iterable
from datetime import date, datetime


class InvalidProtheusDateError(ValueError):
    """Data de filtro fornecida não pôde ser convertida para o formato Protheus.

    Distingue "filtro ausente" (None/vazio → predicado opcional) de
    "filtro fornecido inválido" (falha explícita) para que uma data
    malformada nunca remova silenciosamente um bound de consulta.
    """


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

    def not_in_list(self, field: str, values: Optional[Iterable]):

        if not values:
            return

        values = list(values)

        placeholders = ",".join("?" for _ in values)

        self._filters.append(f"{field} NOT IN ({placeholders})")

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

    def raw(self, condition: str, *params):

        if condition:
            self._filters.append(condition)
            if params:
                self._params.extend(params)

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

        None/vazio = filtro ausente (retorna None, predicado opcional).
        Valor fornecido mas inválido = InvalidProtheusDateError, nunca None.
        """

        if not date_value:
            return None

        if isinstance(date_value, date):
            return date_value.strftime("%Y%m%d")

        if not isinstance(date_value, str):
            raise InvalidProtheusDateError(
                f"Data inválida para filtro de período: {date_value!r}. "
                "Formatos aceitos: YYYYMMDD, YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY."
            )

        text = date_value.strip()

        if not text:
            # Contrato canônico (period_query_params._strip): blank = ausência.
            return None

        if text.isdigit() and len(text) == 8:
            return text

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
                parsed = datetime.strptime(text, fmt)
                return parsed.strftime("%Y%m%d")
            except ValueError:
                continue

        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed.strftime("%Y%m%d")
        except ValueError:
            pass

        raise InvalidProtheusDateError(
            f"Data inválida para filtro de período: {date_value!r}. "
            "Formatos aceitos: YYYYMMDD, YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY."
        )