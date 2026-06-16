"""Filtros SQL compartilhados para OPs de produto acabado (PA) em produção."""

# Alinhado ao Power BI OTD: apenas PA cujo código de produto (C2_PRODUTO) começa com 9.
SC2_PA_PRODUCT_CODE_PREFIX_SQL = "RTRIM(LTRIM(OP.C2_PRODUTO)) LIKE '9%'"

# OTD considera só OP mãe (sequência 001) — entrega do PA, não OPs vinculadas (002+).
SC2_MOTHER_OP_SEQUENCE_SQL = "RTRIM(LTRIM(OP.C2_SEQUEN)) = '001'"

# Variante para consultas com alias LINKED em OPs vinculadas.
LINKED_PA_PRODUCT_CODE_PREFIX_SQL = "RTRIM(LTRIM(LINKED.C2_PRODUTO)) LIKE '9%'"

# Mantém PI/MB/etc.; restringe PA vinculadas ao prefixo 9.
LINKED_PA_OR_PREFIX_FILTER_SQL = (
    "(RTRIM(LTRIM(P.B1_TIPO)) <> 'PA' OR "
    f"{LINKED_PA_PRODUCT_CODE_PREFIX_SQL})"
)
