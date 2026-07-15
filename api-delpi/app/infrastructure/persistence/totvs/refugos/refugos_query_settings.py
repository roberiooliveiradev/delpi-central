from __future__ import annotations

DEFAULT_MONTHS_WINDOW = 1
MAX_MONTHS_WINDOW = 24

DEFAULT_RANKING_LIMIT = 10
MAX_RANKING_LIMIT = 50

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

MAX_FILTROS_ITEMS = 500

RANKING_DIMENSIONS = frozenset(
    {
        "motivo",
        "materia_prima",
        "produto_acabado",
        "centro_trabalho",
        "colaborador",
    }
)

SERIE_GRANULARITIES = frozenset({"day", "month", "auto"})
# Períodos > N dias usam agregação mensal quando granularity=auto.
SERIE_AUTO_DAY_MAX_DAYS = 62
