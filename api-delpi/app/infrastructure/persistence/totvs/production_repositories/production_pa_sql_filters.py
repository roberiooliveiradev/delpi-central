"""Filtros SQL compartilhados para OPs de produto acabado (PA) em produção."""

# PA elegível no OTD e detalhe de OP: C2_PRODUTO começa com 9 (PA DELPI) ou 8 (amostras/teste).
SC2_PA_PRODUCT_CODE_PREFIXES: tuple[str, ...] = ("9", "8")


def _product_code_prefix_clause(column: str) -> str:
    parts = [
        f"RTRIM(LTRIM({column})) LIKE '{prefix}%'"
        for prefix in SC2_PA_PRODUCT_CODE_PREFIXES
    ]
    return "(" + " OR ".join(parts) + ")"


SC2_PA_PRODUCT_CODE_PREFIX_SQL = _product_code_prefix_clause("OP.C2_PRODUTO")

# OTD considera só OP mãe (sequência 001) — entrega consolidada, não OPs vinculadas (002+).
SC2_MOTHER_OP_SEQUENCE_SQL = "RTRIM(LTRIM(OP.C2_SEQUEN)) = '001'"

# Variante para consultas com alias LINKED em OPs vinculadas.
LINKED_PA_PRODUCT_CODE_PREFIX_SQL = _product_code_prefix_clause("LINKED.C2_PRODUTO")

# Mantém PI/MB/etc.; restringe PA vinculadas aos prefixos elegíveis.
LINKED_PA_OR_PREFIX_FILTER_SQL = (
    "(RTRIM(LTRIM(P.B1_TIPO)) <> 'PA' OR "
    f"{LINKED_PA_PRODUCT_CODE_PREFIX_SQL})"
)
