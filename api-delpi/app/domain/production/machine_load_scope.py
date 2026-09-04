"""Escopo — carga máquina (operações alocadas na SH8010).

Fonte confirmada em sonda no TOTVS Delpi (ago/2026):

- ``SH8010`` guarda a alocação da operação no centro de trabalho: ``H8_CTRAB``
  (centro), ``H8_FERRAM`` (ferramenta), ``H8_DTINI``/``H8_HRINI`` (início
  programado) e ``H8_OP`` (chave da OP com 11 posições, igual a ``C2_OP``).
- ``H8_QUANT`` **não** é a quantidade da ordem (vem sempre 1); a quantidade
  válida é ``C2_QUANT`` da ``SC2010``.
- A descrição da operação vem da ``SG2010`` por
  (``G2_FILIAL``, ``G2_PRODUTO``, ``G2_CODIGO`` = roteiro, ``G2_OPERAC``).
- O nome do centro de trabalho é ``SHB010.HB_NOME``.
- A entrega do PA é a da **OP mãe** (``LEFT(H8_OP, 8) + '001'``), porque a data
  da OP filha diverge da mãe na maioria dos casos.
- O que está sendo produzido **agora** vem da ``HZA010`` (apontamento de início
  no coletor), casada por filial + OP + operação.
"""

from __future__ import annotations

from app.domain.services.pagination_tier_service import PaginationTierService

from app.domain.totvs.protheus_production_orders import (  # noqa: F401 (reexport de escopo)
    MOTHER_ORDER_KEY_PREFIX_LENGTH,
    MOTHER_ORDER_SEQUENCE,
)

MACHINE_LOAD_ALLOCATION_TABLE = "SH8010"
MACHINE_LOAD_ORDER_TABLE = "SC2010"
MACHINE_LOAD_PRODUCT_TABLE = "SB1010"
MACHINE_LOAD_WORK_CENTER_TABLE = "SHB010"
MACHINE_LOAD_ROUTING_TABLE = "SG2010"
MACHINE_LOAD_ORDERS_VIEW = "dbo.VW_PCP_ORDENS_PRODUCAO"

VALID_MACHINE_LOAD_BRANCHES = frozenset({"01", "02"})

DEFAULT_WINDOW_DAYS = 7
MAX_WINDOW_DAYS = 90

DEFAULT_PAGE_SIZE = PaginationTierService.require_int("page_100_500", None)
MAX_PAGE_SIZE = int(PaginationTierService.max_size("page_100_500") or 0)
SORT_SCHEDULE_ASC = "schedule_asc"
SORT_SCHEDULE_DESC = "schedule_desc"
SORT_DUE_DATE_ASC = "due_date_asc"
SORT_DUE_DATE_DESC = "due_date_desc"
SORT_ORDER_ASC = "op_asc"
SORT_QTY_DESC = "qty_desc"

SORT_VALUES = (
    SORT_SCHEDULE_ASC,
    SORT_SCHEDULE_DESC,
    SORT_DUE_DATE_ASC,
    SORT_DUE_DATE_DESC,
    SORT_ORDER_ASC,
    SORT_QTY_DESC,
)
DEFAULT_SORT = SORT_SCHEDULE_ASC

# Ferramenta lançada como mão de obra — operação manual, sem ferramental.
MANUAL_LABOR_TOOL_CODE = "MOD"
