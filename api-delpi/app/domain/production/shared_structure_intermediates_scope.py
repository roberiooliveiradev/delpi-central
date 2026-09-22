"""Escopo — intermediários PI/PA compartilhados entre estruturas de PAs ativos.

**PA ativo:** apontamento produtivo ``SH6010`` (``H6_TIPO = 'P'``) no produto PA
(``B1_TIPO = PA``) dentro da janela de movimentação.

**Compartilhado:** o mesmo ``component_code`` aparece na explosão SG1 (vigente
hoje) de **≥ 2** PAs distintos do universo ativo. Matéria-prima não entra.
"""

from __future__ import annotations

from app.domain.services.pagination_tier_service import PaginationTierService

PRODUCT_STRUCTURE_TABLE = "SG1010"
PRODUCT_TABLE = "SB1010"
APPOINTMENTS_TABLE = "SH6010"

VALID_BRANCHES = frozenset({"01", "02"})

DEFAULT_MOVEMENT_LOOKBACK_DAYS = 365
MAX_MOVEMENT_LOOKBACK_DAYS = 730

DEFAULT_PAGE_SIZE = PaginationTierService.require_int("page_50_200", None)
MAX_PAGE_SIZE = int(PaginationTierService.max_size("page_50_200") or 0)

# Mesma profundidade dos conjuntos de OP.
MAX_BOM_DEPTH = 10

EXCLUDED_PA_PREFIXES = ("8000", "8001")
