class ProductBomValidityFilterService:
    """Filtro de vigência de estrutura (SG1010 — G1_INI / G1_FIM)."""

    @classmethod
    def _column_prefix(cls, alias: str) -> str:
        return f"{alias}." if alias else ""

    @classmethod
    def validity_filter_sql(
        cls,
        *,
        alias: str = "G1",
        reference_param: str = "@DATA_REF",
    ) -> str:
        prefix = cls._column_prefix(alias)
        return f"""
              AND ({prefix}G1_INI = '' OR {prefix}G1_INI <= {reference_param})
              AND ({prefix}G1_FIM = '' OR {prefix}G1_FIM >= {reference_param})"""

    @classmethod
    def validity_filter_sql_for_today(cls, *, alias: str = "") -> str:
        today = "CONVERT(CHAR(8), GETDATE(), 112)"
        prefix = cls._column_prefix(alias)
        return f"""
              AND ({prefix}G1_INI = '' OR {prefix}G1_INI <= {today})
              AND ({prefix}G1_FIM = '' OR {prefix}G1_FIM >= {today})"""
