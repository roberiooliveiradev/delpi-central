"""Predicado e expressões SQL canônicas do ROL (SD2 / SD1).

Regra homologada vs resumo de vendas (ago/2026):
- CFOP de retorno de venda ``1201`` / ``2201``; ou
- ``D1_TIPO = 'D'`` **somente** quando o TES gera duplicata (``F4_DUPLIC = 'S'``).

Exclui movimentos de estoque/beneficiamento (ex.: TES «ENTRADA MAT FALTANTE»
com ``F4_DUPLIC = N``) que não entram no faturamento comercial.

Expressões de valor (líquido = TOTAL − ICMS − PIS − COFINS) são a fonte única
para FinancialRepository, ROL-by-customer e faturamento de carteira ``nature=net``.
"""

from __future__ import annotations


class CommercialRolReturnSql:
    SALES_RETURN_CFOPS = ("1201", "2201")

    @staticmethod
    def sale_net_line_expr(*, d2_alias: str = "D2") -> str:
        """Valor líquido de uma linha SD2 (sem agregação)."""
        a = d2_alias
        return (
            f"(ISNULL({a}.D2_TOTAL, 0)"
            f" - ISNULL({a}.D2_VALICM, 0)"
            f" - ISNULL({a}.D2_VALIMP5, 0)"
            f" - ISNULL({a}.D2_VALIMP6, 0))"
        )

    @staticmethod
    def sale_gross_line_expr(*, d2_alias: str = "D2") -> str:
        """Valor bruto de uma linha SD2 (D2_TOTAL)."""
        return f"ISNULL({d2_alias}.D2_TOTAL, 0)"

    @staticmethod
    def return_net_line_expr(*, d1_alias: str = "D1") -> str:
        """Valor líquido de uma linha SD1 de devolução (sem agregação)."""
        a = d1_alias
        return (
            f"(ISNULL({a}.D1_TOTAL, 0)"
            f" - ISNULL({a}.D1_VALICM, 0)"
            f" - ISNULL({a}.D1_VALIMP5, 0)"
            f" - ISNULL({a}.D1_VALIMP6, 0))"
        )

    @staticmethod
    def sale_net_sum_expr(*, d2_alias: str = "D2") -> str:
        return f"SUM(CONVERT(FLOAT, {CommercialRolReturnSql.sale_net_line_expr(d2_alias=d2_alias)}))"

    @staticmethod
    def sale_gross_sum_expr(*, d2_alias: str = "D2") -> str:
        return f"SUM(CONVERT(FLOAT, {CommercialRolReturnSql.sale_gross_line_expr(d2_alias=d2_alias)}))"

    @staticmethod
    def return_net_sum_expr(*, d1_alias: str = "D1") -> str:
        return f"SUM(CONVERT(FLOAT, {CommercialRolReturnSql.return_net_line_expr(d1_alias=d1_alias)}))"

    @staticmethod
    def sale_tes_join(
        *,
        d2_alias: str = "D2",
        f4_alias: str = "F4",
        with_nolock: bool = True,
    ) -> str:
        """LEFT JOIN SF4 pelo TES da linha SD2."""
        lock = " WITH (NOLOCK)" if with_nolock else ""
        return f"""
                LEFT JOIN SF4010 {f4_alias}{lock}
                    ON  {f4_alias}.D_E_L_E_T_ = ''
                    AND {f4_alias}.F4_CODIGO = {d2_alias}.D2_TES
                    AND (
                            {f4_alias}.F4_FILIAL = {d2_alias}.D2_FILIAL
                         OR {f4_alias}.F4_FILIAL = ''
                         OR {f4_alias}.F4_FILIAL IS NULL
                    )
        """

    @staticmethod
    def sale_customer_join(
        *,
        d2_alias: str = "D2",
        a1_alias: str = "A1",
        with_nolock: bool = True,
    ) -> str:
        lock = " WITH (NOLOCK)" if with_nolock else ""
        return f"""
                LEFT JOIN SA1010 {a1_alias}{lock}
                    ON  {a1_alias}.D_E_L_E_T_ = ''
                    AND {a1_alias}.A1_COD  = {d2_alias}.D2_CLIENTE
                    AND {a1_alias}.A1_LOJA = {d2_alias}.D2_LOJA
        """

    @staticmethod
    def sale_eligibility_predicate(
        *,
        d2_alias: str = "D2",
        f4_alias: str = "F4",
        a1_alias: str = "A1",
        exists_where: str,
    ) -> str:
        """Filtros de linha SD2 alinhados ao FinancialRepository / ROL-by-customer.

        ``exists_where`` deve restringir D1X.D1_DTDIGIT (ex.: período da consulta).
        """
        return f"""
                    ISNULL({a1_alias}.A1_NOME, '') <> ''
                    AND ISNULL({d2_alias}.D2_TIPO, '') <> 'D'
                    AND (
                        {d2_alias}.D2_CF NOT IN ('5911', '6151')
                        OR (
                            {d2_alias}.D2_FILIAL = '01'
                            AND {d2_alias}.D2_CF IN ('5911', '6911')
                            AND {d2_alias}.D2_COD LIKE '90%'
                            AND ISNULL({f4_alias}.F4_DUPLIC, '')  = 'N'
                            AND ISNULL({f4_alias}.F4_ESTOQUE, '') = 'S'
                            AND {d2_alias}.D2_UM = 'MI'
                        )
                    )
                    AND (
                        ISNULL({f4_alias}.F4_DUPLIC, '') = 'S'
                        OR (
                            ISNULL({f4_alias}.F4_DUPLIC, '')  = 'N'
                            AND ISNULL({f4_alias}.F4_ESTOQUE, '') = 'S'
                            AND ISNULL({f4_alias}.F4_FINALID, '') = 'BAIXA ESTOQUE'
                            AND {d2_alias}.D2_CF  = '5927'
                            AND {d2_alias}.D2_UM  = 'MI'
                            AND EXISTS (
                                SELECT 1
                                FROM SD1010 D1X WITH (NOLOCK)
                                {CommercialRolReturnSql.tes_join(d1_alias="D1X", f4_alias="F4X", with_nolock=True)}
                                WHERE
                                    D1X.D_E_L_E_T_ = ''
                                    AND D1X.D1_FILIAL  = {d2_alias}.D2_FILIAL
                                    AND D1X.D1_FORNECE = {d2_alias}.D2_CLIENTE
                                    AND D1X.D1_LOJA    = {d2_alias}.D2_LOJA
                                    AND {exists_where}
                                    AND {CommercialRolReturnSql.sales_return_predicate(d1_alias="D1X", f4_alias="F4X")}
                            )
                        )
                        OR (
                            {d2_alias}.D2_FILIAL = '01'
                            AND {d2_alias}.D2_CF IN ('5911', '6911')
                            AND {d2_alias}.D2_COD LIKE '90%'
                            AND ISNULL({f4_alias}.F4_DUPLIC, '')  = 'N'
                            AND ISNULL({f4_alias}.F4_ESTOQUE, '') = 'S'
                            AND {d2_alias}.D2_UM = 'MI'
                        )
                    )
        """

    @staticmethod
    def tes_join(
        *,
        d1_alias: str = "D1",
        f4_alias: str = "F4D",
        with_nolock: bool = False,
    ) -> str:
        """LEFT JOIN SF4 pelo TES da linha SD1 (filial da linha ou TES global)."""
        lock = " WITH (NOLOCK)" if with_nolock else ""
        return f"""
                LEFT JOIN SF4010 {f4_alias}{lock}
                    ON  {f4_alias}.D_E_L_E_T_ = ''
                    AND {f4_alias}.F4_CODIGO = {d1_alias}.D1_TES
                    AND (
                            {f4_alias}.F4_FILIAL = {d1_alias}.D1_FILIAL
                         OR {f4_alias}.F4_FILIAL = ''
                         OR {f4_alias}.F4_FILIAL IS NULL
                    )
        """

    @staticmethod
    def sales_return_predicate(
        *,
        d1_alias: str = "D1",
        f4_alias: str = "F4D",
    ) -> str:
        """Predicado WHERE/AND para linha SD1 contar como devolução de venda no ROL."""
        cfops = ", ".join(f"'{code}'" for code in CommercialRolReturnSql.SALES_RETURN_CFOPS)
        return f"""(
                        {d1_alias}.D1_CF IN ({cfops})
                        OR (
                            {d1_alias}.D1_TIPO = 'D'
                            AND ISNULL({f4_alias}.F4_DUPLIC, '') = 'S'
                        )
                    )"""
