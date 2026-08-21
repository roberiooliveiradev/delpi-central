"""Convenções Delpi — chave da ordem de produção no Protheus (SC2 / SH8).

Doc canônica: api-delpi/docs/api/padroes-totvs/ordem-producao-chave.md
"""

from __future__ import annotations

# C2_OP = C2_NUM (6) + C2_ITEM (2) + C2_SEQUEN (3) = 11 posições.
# SH8010.H8_OP já grava a chave completa — não concatenar de novo.
ORDER_NUMBER_LENGTH = 6
ORDER_ITEM_LENGTH = 2
ORDER_SEQUENCE_LENGTH = 3
ORDER_KEY_LENGTH = ORDER_NUMBER_LENGTH + ORDER_ITEM_LENGTH + ORDER_SEQUENCE_LENGTH

# A OP mãe (o PA) é sempre a sequência 001 do mesmo par número + item.
MOTHER_ORDER_SEQUENCE = "001"
MOTHER_ORDER_KEY_PREFIX_LENGTH = ORDER_NUMBER_LENGTH + ORDER_ITEM_LENGTH


def mother_order_key_sql(column: str) -> str:
    """SQL que deriva a chave da OP mãe a partir da chave de uma OP filha."""
    return f"LEFT({column}, {MOTHER_ORDER_KEY_PREFIX_LENGTH}) + '{MOTHER_ORDER_SEQUENCE}'"


def order_due_date_sql(column: str) -> str:
    """Previsão de entrega da própria OP (``C2_DATPRF``, YYYYMMDD) como DATE."""
    return f"TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM({column})), ''), 112)"


def order_finished_predicate_sql(column: str = "C2_DATRF") -> str:
    """OP encerrada: data real de fim (``C2_DATRF``) preenchida.

    Encerramento é o fato do SC2; apontamento aberto na HZA de OP encerrada é
    coletor não fechado pelo operador, não produção em curso.
    """
    return f"({column} IS NOT NULL AND LTRIM(RTRIM({column})) <> '')"


def effective_due_date_sql(*, mother_due_date: str, order_due_date: str) -> str:
    """Entrega efetiva de uma OP.

    A data da OP mãe manda, porque é ela que carrega o compromisso com o
    cliente; sem mãe, a previsão da própria OP evita operação sem data — o PCP
    planeja por entrega, então ninguém pode ficar de fora do recorte.
    """
    return f"COALESCE({mother_due_date}, {order_due_date_sql(order_due_date)})"
