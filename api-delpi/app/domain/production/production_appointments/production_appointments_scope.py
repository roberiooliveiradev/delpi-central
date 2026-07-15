"""Escopo e constantes — Apontamento de Produção (SH6 por CT)."""

from __future__ import annotations

# Mesma convenção de nome SHB do domínio qualidade; sem acoplar rotas PPM.
CT_INSPECAO_NOME_SQL_LIKE = "%INSPE%FINAL%"

VALID_BRANCHES: frozenset[str] = frozenset({"01", "02"})

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MAX_BY_OP_LIMIT = 200
DEFAULT_BY_OP_LIMIT = 50

SERIES_GROUP_BY_OPTIONS: frozenset[str] = frozenset({"day", "day_work_center"})
