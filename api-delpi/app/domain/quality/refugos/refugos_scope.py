from __future__ import annotations

VALID_REFUGOS_BRANCHES = frozenset({"01", "02"})

# BC_TIPO = 'R' → refugo (painel). Scrap ('S') fica fora do escopo do dashboard.
REFUGOS_LOSS_TYPE = "R"

# SB1.B1_TPMAT (SX3 «Produto de Terceiro»): 1=Não, 2=Sim — painel exclui Sim.
THIRD_PARTY_PRODUCT_TPMAT = "2"

# SB2.B2_LOCAL — custo de refugo (B2_CM1) usa o almoxarifado, alinhado ao Power BI.
REFUGOS_COST_WAREHOUSE = "01"  # almoxarifado
REFUGOS_FACTORY_WAREHOUSE = "99"  # fábrica (não usado no ValorPerda)

OPERADOR_SEM_NOME_LABEL = "Sem nome cadastrado"
MOTIVO_SEM_LABEL = "Sem motivo cadastrado"
