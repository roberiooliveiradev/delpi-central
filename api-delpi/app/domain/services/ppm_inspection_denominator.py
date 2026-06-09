"""Regras de negócio do denominador PPM — produção apontada no CT de inspeção final."""

PPM_PRODUCED_B1_TIPOS: frozenset[str] = frozenset({"PA", "PI"})

# SHB010.HB_NOME — localização dinâmica por filial (ex.: CT-70, CT-99).
CT_INSPECAO_NOME_SQL_LIKE = "%INSPE%FINAL%"


def is_eligible_product_type(tipo: str | None) -> bool:
    """Retorna True se o tipo SB1010 entra no total produzido do PPM."""
    return (tipo or "").strip().upper() in PPM_PRODUCED_B1_TIPOS


def sql_b1_tipo_in_clause() -> str:
    tipos = ", ".join(f"'{tipo}'" for tipo in sorted(PPM_PRODUCED_B1_TIPOS))
    return f"({tipos})"
