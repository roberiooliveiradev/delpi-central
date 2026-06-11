class PurchaseValidityFilterService:
    INTERNAL_SUPPLIERS = ("000019", "001149")

    @classmethod
    def supplier_join_sql(cls) -> str:
        return """
            INNER JOIN SA2010 SA2 WITH (NOLOCK)
                ON SA2.A2_COD = SD1.D1_FORNECE
               AND SA2.A2_LOJA = SD1.D1_LOJA
               AND SA2.D_E_L_E_T_ = ''
        """

    @classmethod
    def supplier_filter_sql(cls) -> str:
        return """
              AND SD1.D1_FORNECE NOT IN (?, ?)
              AND UPPER(SA2.A2_NOME) NOT LIKE '%TRANSP%'
        """

    @classmethod
    def supplier_filter_params(cls) -> list[str]:
        return list(cls.INTERNAL_SUPPLIERS)
