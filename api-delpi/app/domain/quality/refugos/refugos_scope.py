from __future__ import annotations

from app.domain.totvs.protheus_warehouses import (
    COST_UNIT_WAREHOUSE,
    WAREHOUSE_FABRICA,
)

VALID_REFUGOS_BRANCHES = frozenset({"01", "02"})

# BC_TIPO = 'R' → refugo (painel). Scrap ('S') fica fora do escopo do dashboard.
REFUGOS_LOSS_TYPE = "R"

# SB1.B1_TPMAT (SX3 «Produto de Terceiro»): 1=Não, 2=Sim — painel exclui Sim.
THIRD_PARTY_PRODUCT_TPMAT = "2"

# Reexport — custo de refugo = almoxarifado (padrão Delpi).
# Ver api-delpi/docs/api/padroes-totvs/armazem-custo.md
REFUGOS_COST_WAREHOUSE = COST_UNIT_WAREHOUSE  # 01 — almoxarifado
REFUGOS_FACTORY_WAREHOUSE = WAREHOUSE_FABRICA  # 99 — fábrica (fora do ValorPerda)

OPERADOR_SEM_NOME_LABEL = "Sem nome cadastrado"
MOTIVO_SEM_LABEL = "Sem motivo cadastrado"
