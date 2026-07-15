from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FaixaAtrasoDefinicao:
    codigo: str
    rotulo: str
    ordem: int


FAIXAS_ATRASO: tuple[FaixaAtrasoDefinicao, ...] = (
    FaixaAtrasoDefinicao("EM_DIA", "Em dia", 1),
    FaixaAtrasoDefinicao("ATRASO_1_A_5_DIAS", "1 a 5 dias", 2),
    FaixaAtrasoDefinicao("ATRASO_6_A_15_DIAS", "6 a 15 dias", 3),
    FaixaAtrasoDefinicao("ATRASO_16_A_30_DIAS", "16 a 30 dias", 4),
    FaixaAtrasoDefinicao("ATRASO_ACIMA_30_DIAS", "Acima de 30 dias", 5),
)

FAIXA_ATRASO_BY_CODE: dict[str, FaixaAtrasoDefinicao] = {
    item.codigo: item for item in FAIXAS_ATRASO
}

VALID_FAIXA_ATRASO_CODES = frozenset(FAIXA_ATRASO_BY_CODE.keys())

VALID_TITULO_STATUS = frozenset({"all", "on_time", "late"})

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

MAX_PERIOD_MONTHS = 60

DEFAULT_CLIENTES_SORT_BY = "late_amount"
DEFAULT_TITULOS_SORT_BY = "amount"
DEFAULT_SORT_DIR = "desc"

VALID_CLIENTES_SORT_BY = frozenset(
    {
        "late_amount",
        "late_titles",
        "total_amount",
        "on_time_by_quantity_percent",
        "on_time_by_amount_percent",
        "customer_name",
    }
)

VALID_TITULOS_SORT_BY = frozenset(
    {
        "amount",
        "days_late",
        "payment_date",
        "issue_date",
        "customer_name",
        "number",
    }
)

VALID_SORT_DIR = frozenset({"asc", "desc"})

PERIODO_PADRAO_ROTULO = "Últimos 12 meses completos"
PERIODO_PERSONALIZADO_ROTULO = "Período personalizado"

# Clientes fora do escopo deste plugin (ex.: intercompany Delpi).
EXCLUDED_CUSTOMER_CODES: tuple[str, ...] = ("000207",)

# Cliente-chave (WEG). Demais clientes = Novos Negócios.
WEG_CUSTOMER_CODE = "000001"
