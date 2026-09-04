"""Escopo — conjuntos de ordens de produção (SC2010 x SG1010).

Um **conjunto** é o pacote de OPs que o Protheus cria de uma vez para fabricar
um produto: a OP mãe do produto raiz e uma OP filha para cada intermediário da
estrutura. A chave do conjunto é ``C2_FILIAL + C2_NUM + C2_ITEM``; a mãe é a
sequência ``001`` desse par (ver ``protheus_production_orders``).

Sonda no TOTVS Delpi (ago/2026), filial 01, conjuntos com saldo em aberto:

- 2 365 dos 2 376 conjuntos têm exatamente **uma** linha ``C2_SEQUEN = '001'``;
  os 11 restantes não têm mãe viva e ficam **fora** do detector, porque sem o
  produto raiz não há estrutura esperada com que comparar.
- ``C2_NUM`` sozinho **não** identifica o conjunto: existem números com até 96
  itens, cada um com a própria mãe. Agrupar só por número junta pacotes
  distintos e inventa falta e sobra.
- O produto da mãe é ``PA`` em 2 320 casos e ``PI`` em 556 — o raiz nem sempre
  é produto acabado, então nada de assumir ``PA``.
- As OPs filhas só apontam para ``PI`` e ``PA``; nenhuma matéria-prima tem OP.
  Por isso o esperado da estrutura é filtrado por ``B1_TIPO IN ('PI', 'PA')``.
- A vigência da estrutura tem de ser lida na **emissão da OP mãe**
  (``C2_EMISSAO``), não na data de hoje: um conjunto nasce com a estrutura da
  época e continua correto depois de uma troca de engenharia. Medindo a filial
  01, comparar contra hoje acusava 147 conjuntos com falta *e* sobra ao mesmo
  tempo (assinatura clássica de troca de versão); pela emissão sobram 3.

O join com a SG1/SB1 é feito em ``CHAR`` nativo, sem ``RTRIM`` — recortar a
coluna indexada derruba o índice e a consulta passa de ~2 s para timeout.
"""

from __future__ import annotations

from app.domain.services.pagination_tier_service import PaginationTierService

PRODUCTION_ORDER_TABLE = "SC2010"
PRODUCT_STRUCTURE_TABLE = "SG1010"
PRODUCT_TABLE = "SB1010"
PRODUCTION_ORDERS_VIEW = "dbo.VW_PCP_ORDENS_PRODUCAO"

VALID_PRODUCTION_ORDER_SET_BRANCHES = frozenset({"01", "02"})

# Teto de recursão da estrutura. Os chicotes da Delpi têm 2 a 3 níveis; o teto
# existe só para barrar estrutura cíclica cadastrada por engano.
MAX_BOM_DEPTH = 10

DEFAULT_PAGE_SIZE = PaginationTierService.require_int("page_50_200", None)
MAX_PAGE_SIZE = int(PaginationTierService.max_size("page_50_200") or 0)