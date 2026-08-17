"""Convenções Delpi — tipos de produto Protheus (SB1.B1_TIPO).

Doc: api-delpi/docs/api/padroes-totvs/cadastro-produto.md
"""

from __future__ import annotations

# Matéria-prima (estoque de segurança, OTD de compras MP).
PRODUCT_TYPE_RAW_MATERIAL = "MP"

# Produtos acabados / intermediários (produção).
PRODUCT_TYPE_FINISHED_GOOD = "PA"
PRODUCT_TYPE_INTERMEDIATE = "PI"

PRODUCT_TYPE_LABELS_PT: dict[str, str] = {
    PRODUCT_TYPE_RAW_MATERIAL: "Matéria-prima",
    PRODUCT_TYPE_FINISHED_GOOD: "Produto acabado",
    PRODUCT_TYPE_INTERMEDIATE: "Produto intermediário",
}

# Família de código incluída no OTD de compras do dashboard (/supplies/otd),
# além de B1_TIPO / TIPO_PRODUTO = MP (união OR).
SUPPLIES_OTD_PRODUCT_CODE_PREFIX = "3019"
SUPPLIES_OTD_PRODUCT_CODE_PREFIX_LEN = len(SUPPLIES_OTD_PRODUCT_CODE_PREFIX)
