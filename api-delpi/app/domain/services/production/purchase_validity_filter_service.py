class PurchaseValidityFilterService:
    """Filtros de compra válida em SD1010 (NF de entrada).

    Homologado jun/2026 nas MPs: notas de frete/transportadora alocadas no código
    da MP usam D1_QUANT = 0, D1_TES = '040' e D1_PEDIDO vazio — não são compra
    de material. Compras reais têm quantidade > 0 (mesmo quando o fornecedor não
    contém «TRANSP» no nome, ex.: RODOLOG LOGISTICA LTDA).
    """

    INTERNAL_SUPPLIERS = ("000019", "001149")

    SUPPLIER_NAME_EXCLUSION_PATTERNS = ("%TRANSP%",)

    @classmethod
    def supplier_join_sql(cls) -> str:
        return """
            INNER JOIN SA2010 SA2 WITH (NOLOCK)
                ON SA2.A2_COD = SD1.D1_FORNECE
               AND SA2.A2_LOJA = SD1.D1_LOJA
               AND SA2.D_E_L_E_T_ = ''
        """

    @classmethod
    def supplier_name_exclusion_sql(cls) -> str:
        clauses = [
            f"UPPER(SA2.A2_NOME) NOT LIKE '{pattern}'"
            for pattern in cls.SUPPLIER_NAME_EXCLUSION_PATTERNS
        ]
        return "\n              AND " + "\n              AND ".join(clauses)

    @classmethod
    def purchase_line_filter_sql(cls) -> str:
        return """
              AND SD1.D1_QUANT > 0
        """

    @classmethod
    def supplier_filter_sql(cls) -> str:
        return f"""
              AND SD1.D1_FORNECE NOT IN (?, ?)
              {cls.supplier_name_exclusion_sql()}
        """

    @classmethod
    def valid_purchase_filter_sql(cls) -> str:
        return cls.supplier_filter_sql() + cls.purchase_line_filter_sql()

    @classmethod
    def supplier_filter_params(cls) -> list[str]:
        return list(cls.INTERNAL_SUPPLIERS)
