"""Convenções Delpi — armazéns Protheus (SB2.B2_LOCAL) e custo unitário.

Doc canônica: api-delpi/docs/api/padroes-totvs/armazem-custo.md
"""

from __future__ import annotations

# --- Locais operacionais ---
WAREHOUSE_ALMOXARIFADO = "01"
WAREHOUSE_FABRICA = "99"
WAREHOUSE_WIP_50 = "50"
WAREHOUSE_AUX_98 = "98"

# Custo unitário canônico (B2_CM1) para valoração em R$ — alinhado ao Power BI.
COST_UNIT_WAREHOUSE = WAREHOUSE_ALMOXARIFADO

# Saldo disponível típico (estoque de segurança / cobertura).
AVAILABLE_BALANCE_WAREHOUSES = (
    WAREHOUSE_ALMOXARIFADO,
    WAREHOUSE_AUX_98,
    WAREHOUSE_FABRICA,
)

# Trabalho em processo (não usar para B2_CM1 de ValorPerda).
WORK_IN_PROCESS_WAREHOUSES = (
    WAREHOUSE_WIP_50,
    WAREHOUSE_AUX_98,
    WAREHOUSE_FABRICA,
)

WAREHOUSE_LABELS_PT: dict[str, str] = {
    WAREHOUSE_ALMOXARIFADO: "Almoxarifado",
    WAREHOUSE_FABRICA: "Fábrica",
    WAREHOUSE_WIP_50: "WIP / processo",
    WAREHOUSE_AUX_98: "Auxiliar (saldo/WIP)",
}
