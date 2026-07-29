"""Escopo e constantes — Apontamento de Produção (SH6 por CT).

Quantidade real produzida: ``SH6010.H6_QTDPROD``.
Denominador canônico (PPM / shipping / produced-totals): inspeção final + OP mãe.
"""

from __future__ import annotations

# Mesma convenção de nome SHB do domínio qualidade; sem acoplar rotas PPM.
CT_INSPECAO_NOME_SQL_LIKE = "%INSPE%FINAL%"

# Tipos SB1 no total produzido do PPM (PA + PI). Shipping usa só PA.
DEFAULT_PRODUCED_PRODUCT_TYPES: frozenset[str] = frozenset({"PA", "PI"})
SHIPPING_PRODUCED_PRODUCT_TYPES: frozenset[str] = frozenset({"PA"})

VALID_BRANCHES: frozenset[str] = frozenset({"01", "02"})

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MAX_BY_OP_LIMIT = 200
DEFAULT_BY_OP_LIMIT = 50

SERIES_GROUP_BY_OPTIONS: frozenset[str] = frozenset({"day", "day_work_center"})

# Série de OPs finalizadas (SC2.C2_DATRF) — granularidade dia ou mês.
FINISHED_OPS_GRANULARITY_OPTIONS: frozenset[str] = frozenset({"day", "month"})

# OP mãe Protheus — sequência 001 (mesmo critério OTD / C2_SEQUEN).
MOTHER_OP_SUFFIX = "001"
